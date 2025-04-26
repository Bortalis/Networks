"""
server.py

Serves a single-player Battleship session to one connected client.
Game logic is handled entirely on the server using battleship.py.
Client sends FIRE commands, and receives game feedback.

However, if you want to support multiple clients (i.e. progress through further Tiers), you'll need concurrency here too.
"""

import socket
import threading
from battleship import run_single_player_game_online

HOST = '127.0.0.1'
PORT = 5000

players_ready = threading.Event()

#starts the game for the client
def handle_client(conn, addr):
    print(f"[INFO] Client connected from {addr}")

    with conn:
        rfile = conn.makefile('r')
        wfile = conn.makefile('w')
        players_ready.wait(timeout=None) #only start once the number of players needed is reached
        run_single_player_game_online(rfile, wfile)

    print(f"[INFO] Client from {addr} disconnected.")


def main():
    threads = [] # keeps track of threads
    player_cap = 2 #sets the max number of clients
    player_num = 0 #current number of connected clients

    print(f"[INFO] Server listening on {HOST}:{PORT}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(2)  # Allow up to 2 unaccepted connections before refusing

        while player_num < player_cap: #only accept connections if below the player cap
            conn, addr = s.accept() #something is weird here
            client_thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            client_thread.start()
            threads.append(client_thread)
            player_num += 1

        players_ready.set()
        for thread in threads: #waits for all players to finish their game before closing
            thread.join()


if __name__ == "__main__":
    main()
