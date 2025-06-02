import socket
import tkinter as tk
import json

# # local server configuration
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8080

# playit.gg server configuration
# SERVER_IP = 'provided-stayed.gl.at.ply.gg'  # Public hostname from playit.gg
# SERVER_PORT = 65002                           # Public port from playit.gg

GRID_SIZE = 10
CELL_SIZE = 40

class GameClient:
    def __init__(self, master):
        self.master = master
        master.title("Grid Conqueror")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((SERVER_IP, SERVER_PORT))

        self.canvas = tk.Canvas(master, width=GRID_SIZE * CELL_SIZE, height=GRID_SIZE * CELL_SIZE, bg="white")
        self.canvas.pack()

        self.my_id = None
        self.player_boxes = {}
        self.colors = {}

        self.winner_label = tk.Label(master, text="", font=("Arial", 14))
        self.winner_label.pack(pady=5)

        master.bind('<Up>', lambda e: self.send_command("MOVE UP"))
        master.bind('<Down>', lambda e: self.send_command("MOVE DOWN"))
        master.bind('<Left>', lambda e: self.send_command("MOVE LEFT"))
        master.bind('<Right>', lambda e: self.send_command("MOVE RIGHT"))

        self.send_command("HELLO")
        self.poll_updates()

    def send_command(self, command):
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

    def update_display(self, state):
        if self.my_id is None and "your_id" in state:
            self.my_id = state["your_id"]
            print(f"My player ID: {self.my_id}")

        self.canvas.delete("all")
        self.draw_grid()

        # Draw claimed tiles
        for coord, owner in state["claimed"].items():
            x, y = map(int, coord.split(','))
            color = self.get_color(owner)
            self.canvas.create_rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill=color, outline="black"
            )

        # Draw player positions
        for pid, (x, y) in state["players"].items():
            self.canvas.create_rectangle(
                x * CELL_SIZE + 10, y * CELL_SIZE + 10,
                (x + 1) * CELL_SIZE - 10, (y + 1) * CELL_SIZE - 10,
                fill=self.get_color(pid), outline="black"
            )

        # Show winner
        if state["winner"]:
            if state["winner"] == self.my_id:
                self.winner_label.config(text="YOU WIN!")
            else:
                self.winner_label.config(text="YOU LOSE!")

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

if __name__ == "__main__":
    root = tk.Tk()
    client = GameClient(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (client.close(), root.destroy()))
    root.mainloop()
