from re import S
from utils.config import Config
from utils.file_transfer import PacketTransmitter, Packet
import socket as sk

class Client(PacketTransmitter):
    def __init__(self, address : tuple=Config.ADDRESS, timeout : float=Config.TIMEOUT) -> None:
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.socket.timeout(timeout)
        super().__init__(self.socket, address, Config.BUFFERSIZE)
    
    def recive_commands(self) -> None:
        pass

    def send_command(self) -> None:
        pass

    def upload_file(self) -> int:
        pass

    def download_file(self) -> int:
        pass

    def close(self):
        self.socket.close()

if __name__ == "__main__":
    client = Client()