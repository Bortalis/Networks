"""
server.py

Serves a single-player Battleship session to one connected client.
Game logic is handled entirely on the server using battleship.py.
Client sends FIRE commands, and receives game feedback.


"""

import socket
import threading
import logging
from battleship import run_single_player_game_online
from battleship import run_multi_player_game_online

HOST = '127.0.0.1'
PORT = 5000

logging.basicConfig(
    filename="Server_log",
    level=logging.DEBUG,
    filemode="w"
)
logger = logging.getLogger(__name__)


def single_client(conn, addr):
    logger.debug(f"[INFO] Client connected from {addr}")
    with conn:
        rfile = conn.makefile('r')
        wfile = conn.makefile('w')
        run_single_player_game_online(rfile, wfile)
    logger.debug(f"[INFO] Client from {addr} disconnected.")

def multi_client(conn1, addr1, conn2, addr2):
    logger.debug(f"[INFO] Client connected from {addr1}")
    logger.debug(f"[INFO] Client connected from {addr2}")
    rfile1 = conn1.makefile('r')
    wfile1 = conn1.makefile('w')
    rfile2 = conn2.makefile('r')
    wfile2 = conn2.makefile('w')

    run_multi_player_game_online(rfile1,wfile1,rfile2,wfile2)

    conn1.close()
    conn2.close()


#TASK 1.4 ----------------------------------------------------------------------------------
def clientListener(rfile, wfile): 
        #to deal with the client msgs

    while True:
        line = rfile.readline()
        if not line:
            print("[INFO] Server disconnected.")
            break

        logger.debug(f"[INFO] Received message from client: {line}")

        #PLACE MESSAGE RECIEVED (e.g., "Place ship at A1")
        if line.startswith("Place"):
            location = line.split()[-1]  # Assuming the format "Place ship at [location]"
            logger.debug(f"[INFO] Placing ship at {location}")

            # Respond with a successful placement message
            response = f"Successfully placed ship at {location}"
            wfile.write(response + '\n')
            wfile.flush()
            logger.debug(f"[INFO] Sent to client: {response}")

        #FIRE MESSAGE RECIEVED (e.g., "Fire at A1")
        elif line.startswith("Fire at"):
            # Extract the target location (e.g., "Fire at A1")
            target = line[8:]  # Everything after "Fire at "
            logger.debug(f"[INFO] Player fired at {target}")

            # For now, let's assume the server sends a random hit/miss result
            # REPLACE with game logic
            result = "HIT" if target == "A1" else "MISS"  # Example REMOVE LATER
            response = f"RESULT {result}"

            # Send the result back to the client
            wfile.write(response + '\n')
            wfile.flush()
            logger.debug(f"[INFO] Sent to client: {response}")

        else:
            #invalid command received?? - NOT sure if this would happen but this is just in case 
            logger.warning(f"[WARNING] Unknown command received: {line}")
            response = "Invalid command. Try again."
            wfile.write(response + '\n')
            wfile.flush()
            logger.debug(f"[INFO] Sent to client: {response}")



    


def main():
    try:
        threads = [] # keeps track of threads

        logger.debug(f"[INFO] Server listening on {HOST}:{PORT}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            queue = [] #this is the list of players idk
            while True:
                conn, addr = s.accept()
                conn2, addr2 = s.accept()
                client_thread = threading.Thread(target=multi_client, args=(conn, addr, conn2, addr2), daemon=True)
                client_thread.start()
                threads.append(client_thread)
                break


            for thread in threads: #waits for all players to finish their game before closing
                thread.join()
                logger.debug("All threads have joined")

    except Exception as e:
        logger.exception("I don't even know what went wrong in this case",stack_info = True)

    logger.debug("Server turning off")





if __name__ == "__main__":
    main()
