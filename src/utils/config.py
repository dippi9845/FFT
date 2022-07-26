from dataclasses import dataclass

@dataclass
class Config:
    
    HOSTNAME = "localhost"
    PORT = 10001
    
    ADDRESS = (HOSTNAME, PORT)

    CLIENT_CONFIG = {
        "hostname" : HOSTNAME,
        "port" : PORT,
        "timeout" : 2

    }

    SERVER_CONFIG = {
        "hostname" : HOSTNAME,
        "port" : PORT,
        "timeout" : 2
    }