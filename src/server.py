from utils.config import Config
import socket as sk
from json import loads, dumps
from utils.file_transfer import Sender, Reciver, PacketTransmitter, Packet
from os import scandir

class Server(PacketTransmitter):
    def __init__(self, address : tuple=Config.ADDRESS, timeout : float=Config.TIMEOUT) -> None:
        self.address = address
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.socket.bind(address)
        #self.socket.settimeout(timeout)
        super().__init__(self.socket, self.address, Config.BUFFERSIZE)
        

        self.commands = {}
        self.commands[Config.Command.LIST] = self.list_files
        self.commands[Config.Command.DOWNLOAD] = self.upload_file
        self.commands[Config.Command.UPLOAD] = self.download_file

    def recive_command(self) -> str:
        print("I'm waiting for a command")
        return self._get_data()

    def process_command(self, command : str) -> None:
        if self.commands.__contains__(command):
            self.commands[command]()

    def list_files(self) -> int:
        print("Request of list file")
        files = scandir(path = "../" + Config.SERVER_DIR)
        real_file = list(filter(lambda x: x.is_file, files))
        real_file = dumps([file.name for file in real_file])
        self._send_packet(Packet(real_file))

    def upload_file(self) -> int:
        print("Request of upload a file")
        print("Waiting for file name ...")

        file_name = self._get_data()
        print("Requested", file_name)
        

    def download_file(self) -> int:
        print("Request of download a file")

    def close(self):
        self.socket.close()

if __name__ == "__main__":
    server = Server()
    
    while True:
        cmd = server.recive_command()
        server.process_command(cmd)
