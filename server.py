import socket
import threading
import json
import tkinter as tk
from tkinter import filedialog
import csv

HOST = '0.0.0.0'
PORT = 8000
GRID_SIZE = 10

players = {}  # {addr: (x, y)}
claimed_tiles = {}  # {(x, y): player_id}
lock = threading.Lock()
scores = {}  # {player_id: tile_count}

# Tkinter GUI
class ServerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Server Dashboard")

        self.label = tk.Label(root, text="[SERVER] Waiting for players...")
        self.label.pack()

        self.score_display = tk.Text(root, height=15, width=40)
        self.score_display.pack()

        self.save_button = tk.Button(root, text="Save Scores to CSV", command=self.save_scores)
        self.save_button.pack(pady=10)

        self.update_gui_loop()

    def update_gui_loop(self):
        self.update_score_display()
        self.root.after(1000, self.update_gui_loop)

    def update_score_display(self):
        with lock:
            live_scores = calculate_scores()
        self.score_display.delete(1.0, tk.END)
        for player, count in sorted(live_scores.items(), key=lambda x: -x[1]):
            self.score_display.insert(tk.END, f"Player {player}: {count} tiles\n")

    def save_scores(self):
        with lock:
            live_scores = calculate_scores()
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            with open(file_path, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Player ID", "Claimed Tiles"])
                for player, count in live_scores.items():
                    writer.writerow([player, count])
            self.label.config(text=f"Saved scores to {file_path}")

# Server logic
def handle_client(conn, addr):
    print(f"[+] New connection from {addr}")
    player_id = str(addr[1])

    with lock:
        if addr not in players:
            players[addr] = (0, 0)
            claimed_tiles[(0, 0)] = player_id

    with conn:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break

                command = data.decode().strip().upper()

                with lock:
                    x, y = players.get(addr, (0, 0))

                    if command == "MOVE UP":
                        y = max(0, y - 1)
                    elif command == "MOVE DOWN":
                        y = min(GRID_SIZE - 1, y + 1)
                    elif command == "MOVE LEFT":
                        x = max(0, x - 1)
                    elif command == "MOVE RIGHT":
                        x = min(GRID_SIZE - 1, x + 1)
                    elif command == "RESTART" and is_game_over():
                        print("[SERVER] Game restarted by", player_id)
                        players.clear()
                        claimed_tiles.clear()
                        players[addr] = (0, 0)
                        claimed_tiles[(0, 0)] = player_id
                        x, y = 0, 0

                    players[addr] = (x, y)
                    claimed_tiles.setdefault((x, y), player_id)

                    # Build game state
                    state = {
                        "your_id": player_id,
                        "players": {str(a[1]): pos for a, pos in players.items()},
                        "claimed": {f"{k[0]},{k[1]}": v for k, v in claimed_tiles.items()},
                        "winner": get_winner() if is_game_over() else None
                    }

                    conn.sendall(json.dumps(state).encode())

            except (ConnectionResetError, json.JSONDecodeError):
                break

    print(f"[-] Connection closed from {addr}")
    with lock:
        if addr in players:
            del players[addr]

def is_game_over():
    return len(claimed_tiles) >= GRID_SIZE * GRID_SIZE

def get_winner():
    live_scores = calculate_scores()
    return max(live_scores, key=live_scores.get) if live_scores else None

def calculate_scores():
    count = {}
    for owner in claimed_tiles.values():
        count[owner] = count.get(owner, 0) + 1
    return count

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

def main():
    gui_root = tk.Tk()
    server_gui = ServerGUI(gui_root)
    threading.Thread(target=start_server, daemon=True).start()
    gui_root.mainloop()

if __name__ == "__main__":
    main()

