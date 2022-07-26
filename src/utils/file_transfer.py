from hashlib import md5
from json import dumps
from utils.config import Config

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
        self.current_block = ""

    def __iter__(self):
        return self

    def __next__(self) -> Packet:
        data = self.fd.read(self.block_size)
        
        if data:
            self.current_block = Packet(data)
            return self.current_block
        
        else:
            raise StopIteration

# Must give a close function
class Sender:
    def __init__(self) -> None:
        pass
    '''
    while nextpacket.is_last_one():
        if command == "next":
            nextpacket = next(packetiterator)
        send_packet(nextpacket)
        commad = recive_command()
    '''
    

class Reciver:
    def __init__(self) -> None:
        pass
    
    '''
    Ricevi il paccetto
    se giusto invia la richiesta del prossimo
    se sbagliato richiedilo
    
    '''