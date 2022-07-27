from dataclasses import dataclass
from pickle import LIST

@dataclass
class Config:
    
    HOSTNAME = "localhost"
    PORT = 10001
    ADDRESS = (HOSTNAME, PORT)
    TIMEOUT = 2
    BLOCKSIZE = 1024
    BUFFERSIZE = BLOCKSIZE * 2
    SERVER_DIR = "test/srv/"

    class Command:
        LIST = "ls"
        DOWNLOAD = "get"
        UPLOAD = "put"

    COMMANDS = [Command.LIST, Command.DOWNLOAD, Command.UPLOAD]