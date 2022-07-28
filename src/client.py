from utils.config import Config
from utils.file_transfer import PacketTransmitter, Packet, Reciver, Sender
import socket as sk
from json import loads

class Client(PacketTransmitter):
    def __init__(self, address : tuple=Config.ADDRESS, timeout : float=Config.TIMEOUT) -> None:
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.path = "../" + Config.CLIENT_DIR
        super().__init__(self.socket, address, Config.BUFFERSIZE)

        self.commands = {}
        self.commands[Config.Command.LIST] = self.get_files
        self.commands[Config.Command.DOWNLOAD] = self.download_file
        self.commands[Config.Command.UPLOAD] = self.upload_file

    def send_command(self, cmd : str) -> int:
        return self._send_packet(Packet(cmd))

    def upload_file(self) -> int:
        pass

    def download_file(self) -> int:
        file_name = input("file name: ")
        self._send_packet(Packet(file_name))

        reciver = Reciver(self.path + file_name, self.socket, address=self.address)
        reciver.recive_file()

    def get_files(self) -> list[str]:
        files = loads(self._get_data())
        print(" ".join(files))

    def close(self):
        self.socket.close()


if __name__ == "__main__":
    client = Client()
    cmds = Config.COMMANDS

    print("Avaiable commands:")
    print(" ".join(cmds))

    while True:
        cmd = input("-> ")
        if cmd in cmds:
            client.send_command(cmd)
            client.commands[cmd]()
        
