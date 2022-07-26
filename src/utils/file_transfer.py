from hashlib import md5
from json import dumps
from typing_extensions import Self
from utils.config import Config

class Packet:
    def __init__(self, data : bytes, hextdigest : str = None) -> None:
        self.data = data
        self.hash = md5(data).hexdigest()

        if hextdigest is not None and self.hash != hextdigest:
            raise TypeError("Data is corrupted")
    
    def to_json(self) -> str:
        return dumps({"data" : self.data.decode(), "hash" : self.hash})
    
    def to_byte(self) -> bytes:
        return self.to_json().encode()

class FileData:
    def __init__(self, file_pah : str, block_size : int = Config.BLOCKSIZE) -> None:
        pass

    def __iter__(self):
        return FileDataIterator(self)

class FileDataIterator:
    def __init__(self, file_data : FileData) -> None:
        pass

    def __next__(self):
        pass

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