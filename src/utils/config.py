from dataclasses import dataclass

@dataclass
class Config:
    
    HOSTNAME = "localhost"
    PORT = 10501
    ADDRESS = (HOSTNAME, PORT)
    TIMEOUT = 2
    BLOCK_SIZE = 1024
    BUFFER_SIZE = BLOCK_SIZE * 4
    LARGE_FILE = 2**30

    SERVER_DIR = "test/srv/"
    CLIENT_DIR = "test/clt/"

    @dataclass
    class Command:
        LIST = "ls"
        DOWNLOAD = "get"
        UPLOAD = "put"

    COMMANDS = [Command.LIST, Command.DOWNLOAD, Command.UPLOAD]