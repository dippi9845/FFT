from dataclasses import dataclass

@dataclass
class Config:
    
    HOSTNAME = "localhost"
    PORT = 10001
    
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