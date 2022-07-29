from abc import abstractmethod
from hashlib import md5
from json import dumps, loads
from math import ceil
from utils.config import Config
from os.path import getsize as file_size
import socket as sk

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
    
    def _get_data(self, timeout_error : str="Timeout reaced", timeout_end="\n", time_out_max=3, type_error_fun=print, to_str : bool=True) -> str | bytes | None:
        '''
        Recive a generic Packet, but it doesn't stop after a timeout,
        it simply print the message. If a data corruption is present
        a functtion passed as parameter will be executed. There's the
        possibility to not convert recived data into string
        '''
        cnt = 0
        while cnt < time_out_max:
            try:
                package = self._get_packet()
                break
            
            except sk.timeout:
                print(timeout_error, end=timeout_end)
                cnt += 1
            
            except TypeError as e:
                type_error_fun(e)

        if cnt == time_out_max:
            return None

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