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
    '''
    This class model a packet of data sendable with socket
    is possible to read data as bytes or string
    '''
    def __init__(self, data : bytes | str) -> None:
        
        if type(data) == str:
            data = data.encode()
        
        self.data = data.hex()
        self.hash = self.hash_fun(data)

    def to_json(self) -> str:
        '''
        Return an json rappresentation
        '''
        return dumps({"data" : self.data, "hash" : self.hash})
    
    def to_byte(self) -> bytes:
        '''
        Convert to a json rappresentation then into bytes
        '''
        return self.to_json().encode()
    
    def __str__(self):
        '''
        Convert data to str
        '''
        return bytes.fromhex(self.data).decode()
    
    @classmethod
    def by_json(cls, json : str):
        '''
        Checks if data and hash on that is the same, next build a packet on that data
        '''
        hextdigest = json["hash"]
        rtr = cls(bytes.fromhex(json['data']))

        if rtr.hash != hextdigest:
            raise TypeError("Data is corrupted")
        
        return rtr
    
    @staticmethod
    def hash_fun(data : str):
        '''
        Function used to hash data (md5)
        '''
        return md5(data).hexdigest()

ACK = Packet("ACK")

class FileData:
    '''
    A class that read an entire file by blocks, then creat a list of packets on that data
    '''
    def __init__(self, file_path : str, block_size : int = Config.BLOCK_SIZE) -> None:
        self.blocks = []

        with open(file_path, "rb") as f:
            data = f.read(block_size)
            self.blocks.append(Packet(data))

            while data:
                data = f.read(block_size)
                self.blocks.append(Packet(data))
    
    def __len__(self) -> int:
        '''
        Number of packets
        '''
        return len(self.blocks)

    def __iter__(self) -> list[Packet]:
        '''
        Return the iter of the list
        '''
        return iter(self.blocks)


class FileDataIterator:
    '''
    A class that read a file at every iteration, useful to save ram memory
    '''
    def __init__(self, file_path : str, block_size : int = Config.BLOCK_SIZE) -> None:
        self.file_size = file_size(file_path)
        self.fd = open(file_path, "rb")
        self.block_size = block_size
        self.current_block = None

    def __iter__(self):
        '''
        return it self
        '''
        return self
    
    def __len__(self) -> int:
        '''
        Return the number of blocks that will be readed
        '''
        return ceil(self.file_size / self.block_size)

    def __next__(self) -> Packet:
        '''
        Read the next block of bytes
        '''
        data = self.fd.read(self.block_size)
        
        if data:
            self.current_block = Packet(data)
            return self.current_block
        
        else:
            self.close()
            raise StopIteration
    
    def close(self):
        '''
        Close file descriptor
        '''
        self.fd.close()
        self.current_block = None


class PacketTransmitter:
    '''
    This class model a calss that is able to send and recive Packet
    '''
    def __init__(self, socket : sk.socket, address : tuple, buffer_size : int) -> None:
        self.socket = socket
        self.address = address
        self.buffer_size = buffer_size
    
    def _send_packet(self, package : Packet) -> int:
        '''
        Send a generic Packet
        '''
        return self.socket.sendto(package.to_byte(), self.address)

    def _get_packet(self) -> Packet:
        '''
        Recive a generic Packet
        '''
        data, addr = self.socket.recvfrom(self.buffer_size)
        
        if self.address != addr:
            self.address = addr
        
        data = loads(data.decode())

        return Packet.by_json(data)
    
    def _get_data(self, timeout_error : str="Timeout reaced", timeout_end="\n", type_error_fun=print, to_str : bool=True) -> str | bytes:
        '''
        Recive a generic Packet, but it doesn't stop after a timeout,
        it simply print the message. If a data corruption is present
        a functtion passed as parameter will be executed. There's the
        possibility to not convert recived data into string
        '''
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
        '''
        close the conncetion
        '''
        pass


class Sender(PacketTransmitter):
    '''
    This class model a file sender
    '''
    def __init__(self, file_path : str, socket : sk.socket, address : tuple=Config.ADDRESS, block_size : int=Config.BLOCK_SIZE, buffer_size : int=Config.BUFFER_SIZE) -> None:
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
        '''
        Recive a command from the Reciver
        '''
        return self._get_data(timeout_error="Too long waiting for command")
    
    def close(self):
        '''
        Close the connection
        '''
        self.socket.close()
        if self.large_file:
            self.file.close()

    def send_file(self) -> None:
        '''
        Send the file
        '''
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
    '''
    A class that model a file reciver
    '''
    def __init__(self, out_name : str, socket : sk.socket, address : tuple=Config.ADDRESS, buffer_size : int=Config.BUFFER_SIZE) -> None:
        super().__init__(socket, address, buffer_size)
        self.out_name = out_name

        if self._get_data(timeout_error="Waiting for file existing") == "doesn't exts":
            raise IOError("File reqquested doesn't exists")

    def _send_comand(self, command : str) -> int:
        '''
        Send a command to the sender
        '''
        return self._send_packet(Packet(command))

    def close(self) -> None:
        '''
        Close connetion
        '''
        self.socket.close()

    def _get_block_num(self) -> int:
        '''
        Get number of blocks of a file
        '''
        num = self._get_data(timeout_error="Too long waiting for number of blocks")
        try:
            num = int(num)
        except ValueError:
            print("cannot convert to int", num)
            self.close()
        
        return num

    def recive_file(self) -> None:
        '''
        Recive the file
        '''
        with open(self.out_name, "wb") as file:
            n = self._get_block_num()
            print("num of blocks", n)

            for i in range(n):               
                block = self._get_data(type_error_fun=lambda x: self._send_comand("re-send"), timeout_error="Timeout reached when file block is requested", to_str=False)
                file.write(block)
                self._send_comand("next")
                progress_bar(i, n)
            
            print("\n")
