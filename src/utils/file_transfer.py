from hashlib import md5
from json import dumps
from typing_extensions import Self

class DataFile:
    def __init__(self, data : bytes) -> None:
        self.data = data
        self.hash = md5(data).hexdigest()
    
    def to_json(self) -> str:
        return dumps({"data" : self.data.decode(), "hash" : self.hash})
    
    def to_byte(self) -> bytes:
        return self.to_json().encode()
    
    @classmethod
    def from_data(cls, data : bytes, digest : str) -> Self:
        packet = cls(data)
        if packet.hash == digest:
            return packet
        else:
            raise TypeError("Data is corrupted")


class Sender:
    def __init__(self) -> None:
        pass

class Reciver:
    def __init__(self) -> None:
        pass