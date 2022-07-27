from re import S
from utils.config import Config
from utils.file_transfer import PacketTransmitter, Packet
import socket as sk

class Client(PacketTransmitter):
    def __init__(self, address : tuple=Config.ADDRESS, timeout : float=Config.TIMEOUT) -> None:
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.socket.timeout(timeout)
        super().__init__(self.socket, address, Config.BUFFERSIZE)
    
    def recive_commands(self) -> list[str]:
        pass

    def send_command(self, cmd : str) -> None:
        pass

    def upload_file(self) -> int:
        pass

    def download_file(self) -> int:
        pass

    def close(self):
        self.socket.close()

if __name__ == "__main__":
    client = Client()
    cmds = client.recive_commands()

    print("Avaiable commands:")
    map(lambda x: print(x), cmds)
    print()

    while True:
        cmd = input("-> ")
        if cmd in cmds:
            client.send_command(cmd)
        
