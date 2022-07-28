from abc import abstractmethod
from hashlib import md5
from json import dumps, loads
from math import ceil
import socket as sk
from utils.config import Config
from os.path import getsize as file_size, exists

def progress_bar(progress: float, total: float, width: int = 25):
    # function taken from https://stackoverflow.com/questions/3160699/python-progress-bar?page=2&tab=scoredesc#tab-top
    percent = width * ((progress + 1) / total)
    bar = chr(9608) * int(percent) + "-" * (width - int(percent))
    print(f"\r|{bar}| {(100/width)*percent:.2f}%", end="\r")

class Packet:
    def __init__(self, data : bytes | str) -> None:
        
        if type(data) == str:
            data = data.encode()
        
        self.data = data.hex()
        self.hash = self.hash_fun(data)

    def to_json(self) -> str:
        return dumps({"data" : self.data, "hash" : self.hash})
    
    def to_byte(self) -> bytes:
        return self.to_json().encode()
    
    def __str__(self):
        return bytes.fromhex(self.data).decode()
    
    @classmethod
    def by_json(cls, json : str):
        hextdigest = json["hash"]
        rtr = cls(bytes.fromhex(json['data']))

        if rtr.hash != hextdigest:
            raise TypeError("Data is corrupted")
        
        return rtr
    
    @staticmethod
    def hash_fun(data : str):
        return md5(data).hexdigest()

ACK = Packet("ACK")

class FileData:
    def __init__(self, file_path : str, block_size : int = Config.BLOCKSIZE) -> None:
        self.blocks = []

        with open(file_path, "rb") as f:
            data = f.read(block_size)
            self.blocks.append(Packet(data))

            while data:
                data = f.read(block_size)
                self.blocks.append(Packet(data))
    
    def __len__(self) -> int:
        return len(self.blocks)

    def __iter__(self) -> list[Packet]:
        return iter(self.blocks)


class FileDataIterator:
    def __init__(self, file_path : str, block_size : int = Config.BLOCKSIZE) -> None:
        self.file_size = file_size(file_path)
        self.fd = open(file_path, "rb")
        self.block_size = block_size
        self.current_block = None

    def __iter__(self):
        return self
    
    def __len__(self) -> int:
        return ceil(self.file_size / self.block_size)

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


class PacketTransmitter:
    
    def __init__(self, socket : sk.socket, address : tuple, buffer_size : int) -> None:
        self.socket = socket
        self.address = address
        self.buffer_size = buffer_size

    def _send_ack(self) -> int:
        return self._send_packet(ACK, wait_ack=False)
    
    def _get_ack(self) -> None:
        data = self._get_data(send_ack=False)
        assert data == "ACK"
    
    def _send_packet(self, package : Packet) -> int:
        return self.socket.sendto(package.to_byte(), self.address)

    def _get_packet(self) -> Packet:
        data, addr = self.socket.recvfrom(self.buffer_size)
        
        if self.address != addr:
            self.address = addr
        
        data = loads(data.decode())

        return Packet.by_json(data)
    
    def _get_data(self, timeout_error : str="Timeout reaced", timeout_end="\n", type_error_fun=print, to_str : bool=True) -> str | bytes:
        while True:
            try:
                package = self._get_packet()
                break
            
            except sk.timeout:
                print(timeout_error, end=timeout_end)
            
            except TypeError as e:
                type_error_fun(e)

        if to_str:
            return str(package)
        
        else:
            return bytes.fromhex(package.data)

    @abstractmethod
    def close():
        pass


class Sender(PacketTransmitter):
    def __init__(self, file_path : str, socket : sk.socket, address : tuple=Config.ADDRESS, block_size : int=Config.BLOCKSIZE, buffer_size : int=Config.BUFFER_SIZE) -> None:
        super().__init__(socket, address, buffer_size)
        
        if exists(file_path):
            self._send_packet(Packet("exts"))
        else:
            self._send_packet(Packet("doesn't exts"))
            raise IOError("File reqquested doesn't exists")

        if file_size(file_path) > Config.LARGE_FILE:
            self.large_file = True
            self.file = FileDataIterator(file_path, block_size=block_size)
        
        else:
            self.large_file = False
            self.file = FileData(file_path, block_size=block_size)
    
    def _get_command(self) -> str:
        return self._get_data(timeout_error="Too long waiting for command")
    
    def close(self):
        self.socket.close()
        if self.large_file:
            self.file.close()

    def send_file(self) -> None:
        length = len(self.file)
        print("num of blocks", length)
        self._send_packet(Packet(str(length)))
        
        for i, block in enumerate(self.file):
            cmd = " "
            while cmd != "next":
                self._send_packet(block)
                cmd = self._get_command()
            
            progress_bar(i, length)
        
        print("\n")
    

class Reciver(PacketTransmitter):
    def __init__(self, out_name : str, socket : sk.socket, address : tuple=Config.ADDRESS, buffer_size : int=Config.BUFFER_SIZE) -> None:
        super().__init__(socket, address, buffer_size)
        self.out_name = out_name

        if self._get_data(timeout_error="Waiting for file existing") == "doesn't exts":
            raise IOError("File reqquested doesn't exists")

    def _send_comand(self, command : str) -> int:
        return self._send_packet(Packet(command))

    def close(self) -> None:
        self.socket.close()

    def _get_block_num(self) -> int:
        num = self._get_data(timeout_error="Too long waiting for number of blocks")
        try:
            num = int(num)
        except ValueError:
            print("cannot convert to int", num)
            self.close()
        
        return num

    def recive_file(self) -> None:
        with open(self.out_name, "wb") as file:
            n = self._get_block_num()
            print("num of blocks", n)

            for i in range(n):               
                block = self._get_data(type_error_fun=lambda x: self._send_comand("re-send"), timeout_error="Timeout reached when file block is requested", to_str=False)
                file.write(block)
                self._send_comand("next")
                progress_bar(i, n)
            
            print("\n")
