from tkinter.messagebox import NO
from utils.config import Config
import socket as sk
from utils.file_transfer import Sender, Reciver, PacketTransmitter, Packet, ACK
from os import scandir
from os.path import isfile
import signal

class Server(PacketTransmitter):
    def __init__(self, address : tuple=Config.ADDRESS, timeout : float=Config.TIMEOUT) -> None:
        self.address = address
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.socket.bind(address)
        self.socket.settimeout(Config.TIMEOUT)

        self.path = "../" + Config.SERVER_DIR
        self.in_progress = None

        signal.signal(signal.SIGINT, self.close)

        super().__init__(self.socket, self.address, Config.BUFFERSIZE)

        self.commands = {}
        self.commands[Config.Command.LIST] = self.list_files
        self.commands[Config.Command.DOWNLOAD] = self.upload_file
        self.commands[Config.Command.UPLOAD] = self.download_file

    def _send_ack(self) -> int:
        return self._send_packet(ACK)
    
    def recive_command(self) -> str:
        print("I'm waiting for a command\n")
        return self._get_data(timeout_error="", timeout_end="")

    def process_command(self, command : str) -> None:
        if self.commands.__contains__(command):
            self.commands[command]()
            print()

    def list_files(self) -> int:
        print("Request of list file")
        files = scandir(path=self.path)
        real_file = list(filter(isfile, files))
        real_file = " ".join([file.name for file in real_file])
        self._send_ack()
        self._send_packet(Packet(real_file))

    def upload_file(self):
        print("Request of upload a file")
        print("Waiting for file name ...")

        file_name = self._get_data()
        print("Requested", file_name)

        self._send_ack()
        
        try:
            sender = Sender(self.path + file_name, self.socket, address=self.address)
            self.in_progress = sender
            
            sender.send_file()
            self.in_progress = None
        
        except IOError as e:
            print(e)

        


    def download_file(self) -> int:
        print("Request of download a file")
        print("Waiting for file name ...")

        file_name = self._get_data()
        self._send_ack()

        try:
            reciver = Reciver(self.path + file_name, self.socket, address=self.address)
            self.in_progress = reciver

            reciver.recive_file()
            self.in_progress = None
            
        except IOError as e:
            print(e)

    def close(self, signal, fname):
        if self.in_progress == None:
            self.socket.close()
        
        else:
            self.in_progress.close()
        
        exit(0)

if __name__ == "__main__":
    server = Server()
    
    while True:
        cmd = server.recive_command()
        server.process_command(cmd)
