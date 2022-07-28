from utils.config import Config
from utils.file_transfer import PacketTransmitter, Packet, Reciver, ACK, Sender
import socket as sk
import signal

class Client(PacketTransmitter):
    '''
    A class that model a client
    '''
    def __init__(self, address : tuple=Config.ADDRESS, timeout : float=Config.TIMEOUT) -> None:
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
        self.socket.settimeout(timeout)
        self.path = "../" + Config.CLIENT_DIR
        self.in_progress = None

        signal.signal(signal.SIGINT, self.close)

        super().__init__(self.socket, address, Config.BUFFER_SIZE)

        self.commands = {}
        self.commands[Config.Command.LIST] = self.get_files
        self.commands[Config.Command.DOWNLOAD] = self.download_file
        self.commands[Config.Command.UPLOAD] = self.upload_file

    def _get_ack(self) -> bool:
        '''
        Get ACK from the server
        '''
        try:
            package = self._get_packet()
        except sk.timeout:
            print("timeout reached during waiting for ACK")
            return False
        
        except TypeError as e:
            print(e)
            return False
        
        if package.data != ACK.data:
            print("ACK expected", package.data.decode(), "found")
            return False
        
        return True

    def send_command(self, cmd : str) -> int:
        '''
        Send a command to the server
        '''
        return self._send_packet(Packet(cmd))

    def upload_file(self, file : str=None) -> int:
        '''
        Send a file to the server
        '''
        if file == None:
            file_name = input("file name: ")
        
        else:
            file_name = file

        self._send_packet(Packet(file_name))

        if self._get_ack():
            try:
                sender = Sender(self.path + file_name, self.socket, address=self.address)
                self.in_progress = sender

                sender.send_file()
                self.in_progress = None
            
            except IOError as e:
                print(e)

    def download_file(self, file : str=None) -> int:
        '''
        Download a file from the server
        '''
        if file == None:
            file_name = input("file name: ")
        
        else:
            file_name = file
        
        self._send_packet(Packet(file_name))
        
        if self._get_ack():
            try:
                reciver = Reciver(self.path + file_name, self.socket, address=self.address)
                self.in_progress = reciver
                
                reciver.recive_file()
                self.in_progress = None
            except IOError as e:
                print(e)

    def get_files(self) -> list[str]:
        '''
        Get list of files in the server
        '''
        if self._get_ack():
            files = self._get_data()
            print(files)

    def close(self, signal, fname):
        '''
        close connection
        '''
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
        
