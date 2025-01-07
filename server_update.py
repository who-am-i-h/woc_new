import threading
import termcolor
from rich.console import Console
from rich.table import Table
from rich.live import Live
import time
import socket
from DFH import Dfh_server as Dfh
from Client_mod import Client
from master_mod import master_dashboard


# Variable
lock = threading.Lock()
listen_clients = 5
clients = []
server_id = 0

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

#socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST = "localhost"
PORT = 6969
s.bind((HOST, PORT))
s.listen(listen_clients)
print(termcolor.colored("Server started and listening...", "green"))

#methods

def color(text, col):
    return termcolor.colored(text, col)

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
        key = str(key).encode()[:16]
        conn.send(str(secret).encode())
        new_client = Client(key, conn, True, addr)
        try:
            new_client.os = new_client.recv()
        except:
            new_client.os = "Unidentifed!!!"
        with lock:
            clients.append(new_client)
            print(color(f"Connected to {new_client.addr}", "green"), "secret=",new_client.key)

threading.Thread(target=handle_clients, daemon=True).start()

def check_client(client: Client):
    try:
        client.send("..SYN..")
        client.recv()  
    except socket.error:
        client.mark_offline()
    
def show_clients():
    with lock:
        print(color("Connected clients:", "cyan"))
        for i, client in enumerate(clients):
            check_client(client)
            print(f"[{i}] {color(client.addr, "blue")}" + f" Active {color("*", "green")}" if client.status else f"[{i}] {color(client.addr, "red")}" + f" unActive {color("*", "red")}")

while True:
    if clients:
        try:
            client_now = clients[server_id]
        except (ValueError, IndexError) as e:
            print(termcolor.colored(f"Some Error Happened: {e}", "red"))
            server_id = 0
            continue

        prompt = input(f"[{color("*", "blue")}] {color("shell", "green")}~{client_now.addr} ")


        if prompt.lower().startswith("switch"):
            try:
                server_id = int(prompt.split()[1]) - 1
            except:
                server_id = 0
                continue

        elif prompt.lower() == "clients":
            show_clients()
        elif prompt.lower() == "master":
            for clts in clients:
                check_client(clts)
            master_dashboard(clients)
        else:
            if client_now.status:
                try:
                    client_now.send(prompt)
                    from_client = client_now.recv()
                    if from_client.startswith("####CPUM#### "):
                        stats = from_client.split("####CPUM#### ")[1].split("-")
                        show_stats(stats[0], stats[1], stats[2])
                    else:
                        print(from_client)
                except:
                    print(color("The Client may be offline.... ", "red"))
                    print(color("try switching to active servers", "green"))
                    check_client(client_now)
                    show_clients()
                    continue
            else:
                print(color("You Can't send command to offline server....", "red"))
                print(color("switch to active servers", "green"))
                show_clients()

        check_client(client_now)
