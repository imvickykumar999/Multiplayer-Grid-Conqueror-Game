import socket
import tkinter as tk
import json

GRID_SIZE = 10
CELL_SIZE = 40


class GameClient:
    def __init__(self, master, server_ip, server_port):
        self.master = master
        master.title("Grid Conqueror")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server_ip, server_port))

        self.canvas = tk.Canvas(master, width=GRID_SIZE * CELL_SIZE, height=GRID_SIZE * CELL_SIZE, bg="white")
        self.canvas.pack()

        self.my_id = None
        self.player_boxes = {}
        self.colors = {}
        self.game_over = False

        self.winner_label = tk.Label(master, text="", font=("Arial", 14))
        self.winner_label.pack(pady=5)

        self.restart_button = tk.Button(master, text="Play Again", font=("Arial", 12), command=self.restart_game)
        self.restart_button.pack(pady=5)
        self.restart_button.pack_forget()

        master.bind('<Up>', lambda e: self.send_command("MOVE UP"))
        master.bind('<Down>', lambda e: self.send_command("MOVE DOWN"))
        master.bind('<Left>', lambda e: self.send_command("MOVE LEFT"))
        master.bind('<Right>', lambda e: self.send_command("MOVE RIGHT"))

        self.send_command("HELLO")
        self.poll_updates()

    def send_command(self, command):
        if self.game_over and command.startswith("MOVE"):
            return
        try:
            self.sock.sendall(command.encode())
            data = self.sock.recv(4096).decode()
            state = json.loads(data)
            self.update_display(state)
        except Exception as e:
            print("Error:", e)

    def poll_updates(self):
        self.send_command("PING")
        self.master.after(500, self.poll_updates)

    def restart_game(self):
        self.restart_button.pack_forget()
        self.winner_label.config(text="")
        self.my_id = None
        self.game_over = False
        self.send_command("RESTART")

    def update_display(self, state):
        if self.my_id is None and "your_id" in state:
            self.my_id = state["your_id"]
            print(f"My player ID: {self.my_id}")

        self.canvas.delete("all")
        self.draw_grid()

        for coord, owner in state["claimed"].items():
            x, y = map(int, coord.split(','))
            color = self.get_color(owner)
            self.canvas.create_rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill=color, outline="black"
            )

        for pid, (x, y) in state["players"].items():
            self.canvas.create_rectangle(
                x * CELL_SIZE + 10, y * CELL_SIZE + 10,
                (x + 1) * CELL_SIZE - 10, (y + 1) * CELL_SIZE - 10,
                fill=self.get_color(pid), outline="black"
            )

        if state["winner"]:
            self.game_over = True
            if state["winner"] == self.my_id:
                self.winner_label.config(text="🎉 YOU WIN!")
            else:
                self.winner_label.config(text="❌ YOU LOSE!")
            self.restart_button.pack()

    def draw_grid(self):
        for i in range(GRID_SIZE + 1):
            self.canvas.create_line(i * CELL_SIZE, 0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE)
            self.canvas.create_line(0, i * CELL_SIZE, GRID_SIZE * CELL_SIZE, i * CELL_SIZE)

    def get_color(self, pid):
        if pid not in self.colors:
            palette = ["red", "blue", "green", "orange", "purple", "magenta", "cyan", "yellow", "pink"]
            self.colors[pid] = palette[int(pid) % len(palette)]
        return self.colors[pid]

    def close(self):
        self.sock.close()


def launch_connection_window():
    def connect():
        ip = ip_entry.get()
        port = port_entry.get()
        try:
            port = int(port)
            root.destroy()
            game_root = tk.Tk()
            client = GameClient(game_root, ip, port)
            game_root.protocol("WM_DELETE_WINDOW", lambda: (client.close(), game_root.destroy()))
            game_root.mainloop()
        except Exception as e:
            error_label.config(text=f"Error: {e}")

    root = tk.Tk()
    root.title("Connect to Server")

    tk.Label(root, text="Server IP:").pack(pady=2)
    ip_entry = tk.Entry(root)
    ip_entry.insert(0, "february-exactly.gl.at.ply.gg")  # Default IP 127.0.0.1
    ip_entry.pack(pady=2)

    tk.Label(root, text="Server Port:").pack(pady=2)
    port_entry = tk.Entry(root)
    port_entry.insert(0, "5892")  # Default port 8000
    port_entry.pack(pady=2)

    tk.Button(root, text="Connect", command=connect).pack(pady=5)
    error_label = tk.Label(root, text="", fg="red")
    error_label.pack()

    root.mainloop()


if __name__ == "__main__":
    launch_connection_window()

