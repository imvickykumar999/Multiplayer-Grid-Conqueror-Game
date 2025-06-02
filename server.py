import socket
import threading
import json

HOST = '0.0.0.0'
PORT = 8080
GRID_SIZE = 10

players = {}  # {addr: (x, y)}
claimed_tiles = {}  # {(x, y): player_id}
lock = threading.Lock()

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
    count = {}
    for owner in claimed_tiles.values():
        count[owner] = count.get(owner, 0) + 1
    return max(count, key=count.get)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    main()
