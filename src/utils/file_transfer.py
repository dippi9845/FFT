from email.quoprimime import header_check
from hashlib import md5
from json import dumps, loads
import socket as sk
from config import Config

class Packet:
    def __init__(self, data : bytes | str, hextdigest : str = None) -> None:
        
        if type(data) == str:
            data = data.encode()
        
        self.data = data
        self.hash = md5(data).hexdigest()

        if hextdigest is not None and self.hash != hextdigest:
            raise TypeError("Data is corrupted")
    
    def to_json(self) -> str:
        return dumps({"data" : self.data.decode(), "hash" : self.hash})
    
    def to_byte(self) -> bytes:
        return self.to_json().encode()


class FileData:
    def __init__(self, file_path : str, block_size : int = Config.BLOCKSIZE) -> None:
        self.blocks = []

        with open(file_path, "r") as f:
            data = f.read(block_size)
            self.blocks.append(Packet(data))

            while data:
                data = f.read(block_size)
                self.blocks.append(Packet(data))

    def __iter__(self) -> list[Packet]:
        return iter(self.blocks)


class FileDataIterator:
    def __init__(self, file_path : str, block_size : int = Config.BLOCKSIZE) -> None:
        self.fd = open(file_path, "r")
        self.block_size = block_size
        self.current_block = None

    def __iter__(self):
        return self

    def __next__(self) -> Packet:
        data = self.fd.read(self.block_size)
        
        if data:
            self.current_block = Packet(data)
            return self.current_block
        
        else:
            self.close()
            raise StopIteration
    
    def close(self):
        self.fd.close()
        self.current_block = None


class Sender:
    def __init__(self, file_path : str, socket : sk.socket, address : tuple = Config.ADDRESS, block_size : int = Config.BLOCKSIZE) -> None:
        self.file = FileData(file_path, block_size=block_size)
        self.socket = socket
        self.address = address
    
    def _send_packet(self, package : Packet) -> int:
        return self.socket.sendto(package.to_byte(), self.address)
    
    def _get_command(self) -> str:
        pass

    def send_file(self) -> None:
        for block in self.file:
            cmd = " "
            while cmd != "next":
                self._send_packet(block)
                cmd = self._get_command()
    

class Reciver:
    def __init__(self, out_name : str, socket : sk.socket, address : tuple = Config.ADDRESS, buffer_size : int = Config.BUFFERSIZE) -> None:
        self.out_name = out_name
        self.socket = socket
        self.address = address
        self.buffer_size = buffer_size
    
    def _send_comand(self, command : str) -> int:
        return self.socket.sendto(command.encode(), self.address)

    def close(self) -> None:
        self.socket.close()

    def _get_block_num(self) -> int:
        while True:
            try:
                num = self.socket.recvfrom(self.buffer_size)
                num = int(num)
                break
            except sk.timeout:
                print("Too long waiting for number of blocks")
                print("Timeout reaced")
        
        return num

    def recive_file(self) -> None:
        with open(self.out_name, "wb") as file:
            n = self._get_block_num()
            
            for _ in range(n):
                valid = False
                
                while not valid:
                    raw, _ = self.socket.recvfrom(self.buffer_size)
                    data = loads(raw.decode())
                    try:
                        block = Packet(data["data"], hextdigest=data["hash"])
                        valid = True
                    except TypeError:
                        self._send_comand("re-send")
                
                file.write(block.data)
                self._send_comand("next")
