from dataclasses import dataclass

@dataclass
class Config:
    
    HOSTNAME = "localhost"
    PORT = 10501
    ADDRESS = (HOSTNAME, PORT)
    TIMEOUT = 2
    BLOCKSIZE = 1024
    BUFFERSIZE = BLOCKSIZE * 4
    LARGE_FILE = 2**30

    SERVER_DIR = "test/srv/"
    CLIENT_DIR = "test/clt/"

    @dataclass
    class Command:
        LIST = "ls"
        DOWNLOAD = "get"
        UPLOAD = "put"

    COMMANDS = [Command.LIST, Command.DOWNLOAD, Command.UPLOAD]