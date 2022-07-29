import socket as sk
from os.path import getsize as file_size, exists
from utils.config import Config
from utils.data import Packet, PacketTransmitter, FileData, FileDataIterator

def progress_bar(progress: float, total: float, width: int = 25):
    # function taken from https://stackoverflow.com/questions/3160699/python-progress-bar?page=2&tab=scoredesc#tab-top
    percent = width * ((progress + 1) / total)
    bar = chr(9608) * int(percent) + "-" * (width - int(percent))
    print(f"\r|{bar}| {(100/width)*percent:.2f}%", end="\r")


class Sender(PacketTransmitter):
    '''
    This class model a file sender
    '''
    def __init__(self, file_path : str, socket : sk.socket, address : tuple=Config.ADDRESS, block_size : int=Config.BLOCK_SIZE, buffer_size : int=Config.BUFFER_SIZE, progress_bar : bool=True) -> None:
        super().__init__(socket, address, buffer_size)
        self.progress_bar = progress_bar
        
        if exists(file_path):
            self._send_packet(Packet("exts"))
        else:
            self._send_packet(Packet("doesn't exts"))
            raise IOError("File reqquested doesn't exists")

        if file_size(file_path) > Config.LARGE_FILE:
            self.large_file = True
            self.file = FileDataIterator(file_path, block_size=block_size)
        
        else:
            self.large_file = False
            self.file = FileData(file_path, block_size=block_size)
    
    def _get_command(self) -> str:
        '''
        Recive a command from the Reciver
        '''
        return self._get_data(timeout_error="Too long waiting for command")
    
    def close(self):
        '''
        Close the connection
        '''
        self.socket.close()
        if self.large_file:
            self.file.close()

    def send_file(self) -> None:
        '''
        Send the file
        '''
        length = len(self.file)
        print("num of blocks", length)
        self._send_packet(Packet(str(length)))
        
        if self.progress_bar:
            for i, block in enumerate(self.file):
                cmd = " "
                while cmd != "next":
                    self._send_packet(block)
                    cmd = self._get_command()
                
                progress_bar(i, length)
            
            print("\n")

        else:
            for block in self.file:
                cmd = " "
                while cmd != "next":
                    self._send_packet(block)
                    cmd = self._get_command()
    

class Receiver(PacketTransmitter):
    '''
    A class that model a file reciver
    '''
    def __init__(self, out_name : str, socket : sk.socket, address : tuple=Config.ADDRESS, buffer_size : int=Config.BUFFER_SIZE, progress_bar : bool=True) -> None:
        super().__init__(socket, address, buffer_size)
        self.out_name = out_name
        self.progress_bar = progress_bar

        if self._get_data(timeout_error="Waiting for file existing") == "doesn't exts":
            raise IOError("File reqquested doesn't exists")

    def _send_comand(self, command : str) -> int:
        '''
        Send a command to the sender
        '''
        return self._send_packet(Packet(command))

    def close(self) -> None:
        '''
        Close connetion
        '''
        self.socket.close()

    def _get_block_num(self) -> int:
        '''
        Get number of blocks of a file
        '''
        num = self._get_data(timeout_error="Too long waiting for number of blocks")
        try:
            num = int(num)
        except ValueError:
            print("cannot convert to int", num)
            self.close()
        
        return num

    def recive_file(self) -> None:
        '''
        Recive the file
        '''
        with open(self.out_name, "wb") as file:
            n = self._get_block_num()
            print("num of blocks", n)

            for i in range(n):
                block = None
                block = self._get_data(type_error_fun=lambda x: self._send_comand("re-send"), timeout_error="Timeout reached when file block is requested", to_str=False)
                
                while block is None:
                    self._send_comand("re-send")
                    block = self._get_data(type_error_fun=lambda x: self._send_comand("re-send"), timeout_error="Timeout reached when file block is requested", to_str=False)
                
                file.write(block)
                self._send_comand("next")
                
                if self.progress_bar:
                    progress_bar(i, n)
            
            if self.progress_bar:
                print("\n")
