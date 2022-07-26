from dataclasses import dataclass

@dataclass
class Config:
    
    HOSTNAME = "localhost"
    PORT = 10001
    ADDRESS = (HOSTNAME, PORT)
    TIMEOUT = 2
    BLOCKSIZE = 1024