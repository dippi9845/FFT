from utils.config import Config
from utils.file_transfer import PacketTransmitter, Packet, Reciver, ACK, Sender
import socket as sk
import signal

class Client(PacketTransmitter):
    def __init__(self, address : tuple=Config.ADDRESS, timeout : float=Config.TIMEOUT) -> None:
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.path = "../" + Config.CLIENT_DIR
        self.in_progress = None

        signal.signal(signal.SIGINT, self.close)

        super().__init__(self.socket, address, Config.BUFFERSIZE)

        self.commands = {}
        self.commands[Config.Command.LIST] = self.get_files
        self.commands[Config.Command.DOWNLOAD] = self.download_file
        self.commands[Config.Command.UPLOAD] = self.upload_file

    def _get_ack(self) -> tuple[bool, str]:
        
        try:
            package = self._get_packet()
        except sk.timeout:
            return False, "timeout reached during waiting for ACK"
        
        except TypeError as e:
            return False, str(e)
        
        if package.data != ACK.data:
            return False, str(package)
        
        return True, ""

    def send_command(self, cmd : str) -> int:
        return self._send_packet(Packet(cmd))

    def upload_file(self, file : str=None) -> int:
        
        if file == None:
            file_name = input("file name: ")
        
        else:
            file_name = file

        self._send_packet(Packet(file_name))

        scs, err = self._get_ack()

        if scs:
            sender = Sender(self.path + file_name, self.socket, address=self.address)
            self.in_progress = sender

            sender.send_file()
            self.in_progress = None
        
        else:
            print(err)

    def download_file(self, file : str=None) -> int:
        
        if file == None:
            file_name = input("file name: ")
        
        else:
            file_name = file
        
        self._send_packet(Packet(file_name))
        
        if self._get_ack():
            reciver = Reciver(self.path + file_name, self.socket, address=self.address)
            self.in_progress = reciver
            
            reciver.recive_file()
            self.in_progress = None

    def get_files(self) -> list[str]:
        if self._get_ack():
            files = self._get_data()
            print(files)

    def close(self, signal, fname):
        if self.in_progress == None:
            self.socket.close()
        
        else:
            self.in_progress.close()
        
        exit(0)


if __name__ == "__main__":
    client = Client()
    cmds = Config.COMMANDS

    print("Avaiable commands:")
    print(" ".join(cmds))

    while True:
        cmdl = input("-> ").strip().split(" ")
        it = iter(cmdl)
        cmd = next(it)

        if cmd in cmds:
            client.send_command(cmd)

            if len(cmdl) == 2:
                file = next(it)
                client.commands[cmd](file=file)

            else:
                client.commands[cmd]()
        
