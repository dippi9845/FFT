from abc import abstractmethod
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
        self.fd = open(file_path, "rb")
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


class _FileTransmitter:
    
    def __init__(self, socket : sk.socket, address : tuple) -> None:
        self.socket = socket
        self.address = address

    def _send_packet(self, package : Packet) -> int:
        return self.socket.sendto(package.to_byte(), self.address)

    def _get_data(self, buffer_size : int, timeout_error : str="Timeout reaced", type_error_fun : function=print) -> str:
        while True:
            try:
                data, _ = self.socket.recvfrom(buffer_size)
                data = loads(data.decode())
                package = Packet(data["data"], hextdigest=data["hash"])
                break
            
            except sk.timeout:
                print(timeout_error)
            
            except TypeError as e:
                type_error_fun(e)
        
        return package.data.decode()

    @abstractmethod
    def close():
        pass


class Sender(_FileTransmitter):
    def __init__(self, file_path : str, socket : sk.socket, address : tuple=Config.ADDRESS, block_size : int=Config.BLOCKSIZE, buffer_size : int=Config.BUFFERSIZE) -> None:
        super().__init__(socket, address)
        self.file = FileData(file_path, block_size=block_size)
        self.buffer_size = buffer_size
    
    def _get_command(self) -> str:
        return super()._get_data(self.socket, self.buffer_size, timeout_error="Too long waiting for command")
    
    def close(self):
        self.socket.close()

    def send_file(self) -> None:
        for block in self.file:
            cmd = " "
            while cmd != "next":
                self._send_packet(block)
                cmd = self._get_command()
    

class Reciver(_FileTransmitter):
    def __init__(self, out_name : str, socket : sk.socket, address : tuple=Config.ADDRESS, buffer_size : int=Config.BUFFERSIZE) -> None:
        super().__init__(socket, address)
        self.out_name = out_name
        self.buffer_size = buffer_size

    def _send_comand(self, command : str) -> int:
        return self._send_packet(Packet(command))

    def close(self) -> None:
        self.socket.close()

    def _get_block_num(self) -> int:
        num = self._get_data(self.socket, self.buffer_size, timeout_error="Too long waiting for number of blocks")
        try:
            num = int(num)
        except ValueError:
            print("cannot convert to int", num)
            self.close()

    def recive_file(self) -> None:
        with open(self.out_name, "wb") as file:
            n = self._get_block_num()
            
            for _ in range(n):               
                block = self._get_data(self.socket, self.buffer_size, type_error_fun=lambda x: self._send_comand("re-send"))
                file.write(block.encode())
                self._send_comand("next")
