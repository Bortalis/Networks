"""
server.py
Game logic is handled entirely on the server using battleship.py.
"""

import time
import socket
import threading
import logging
from battleship import run_multi_player_game_online

gamestate_ref = [0] 
#This is contained in the gamestate_ref list so that it can be passed by reference
# this will be updated based on battleship.py 
# all games will start in the placement phase = 0
# firing phase = 1
# game over = 2


HOST = '127.0.0.1'
PORT = 5000

logging.basicConfig(
    filename="Server_log",
    level=logging.DEBUG,
    filemode="w"
)
logger = logging.getLogger(__name__)

def multi_client(conn1, conn2):
    rfile1 = conn1.makefile('r')
    wfile1 = conn1.makefile('w')
    rfile2 = conn2.makefile('r')
    wfile2 = conn2.makefile('w')

    # Start threads to send game state updates to the clients
    gamestate_thread_P1 = threading.Thread(target=monitor_and_send_gamestate, args=(wfile1, gamestate_ref), daemon=True)
    gamestate_thread_P2 = threading.Thread(target=monitor_and_send_gamestate, args=(wfile2, gamestate_ref), daemon=True)
    gamestate_thread_P1.start()
    gamestate_thread_P2.start()

    run_multi_player_game_online(rfile1,wfile1,rfile2,wfile2, gamestate_ref)


def main():
    try:
        threads = [] # keeps track of threads

        logger.debug(f"[INFO] Server listening on {HOST}:{PORT}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            queue = [] #players waiting for an opponent
            players = [] #players playing
            s.bind((HOST, PORT))
            s.listen()
            while True:
                conn, addr = s.accept()
                logger.debug(f"[INFO] Client connected from {addr}")

                # If a game is in progress, immediately notify the client and do not add to queue
                if len(players) == 2:
                    try:
                        wfile = conn.makefile('w')
                        wfile.write("WAITING: Game in progress, please wait for it to end...\n")
                        wfile.flush()
                    except Exception as e:
                        logger.debug(f"[ERROR] Failed to communicate with waiting client: {e}")
                    continue  # Skip the rest of the loop for this client


                # Only add to queue if not in-game

                queue.append((conn,addr)) #we keep their addr for id for T3.3

                if len(queue) < 2: # Notify client if waiting for opponent
                    try:
                            wfile = conn.makefile('w')
                            wfile.write("WAITING: Hold on until another player to join...\n")
                            wfile.flush()
                    except Exception as e:
                        logger.debug(f"[ERROR] Failed to commiunicate with waiting client: {e}")

                # Start a game with the first two clients in the queue, given no game is running
                if len(queue) >= 2 and len(players) == 0: 
                    client_thread = threading.Thread(target=multi_client, args=(queue[0][0], queue[1][0]), daemon=True)
                    players.append(queue[0])
                    players.append(queue[0]) #I DON'T KNOW IF THIS IS SUPPOSED TO BE QUEUE[1]??????

                    client_thread.start()
                    threads.append(client_thread)

                # Remove that pair of clients from queue
                    queue = queue[2:]

    except Exception as e:
        logger.exception("I don't even know what went wrong in this case",stack_info = True)

    logger.debug("[INFO] Server turning off")




#Server should not end for now                    
#
#                if len(players) >= 2:
#                    break
#
#            for thread in threads: #waits for all players to finish their game before closing
#                thread.join()
#            logger.debug("[INFO] All threads have joined")
#            #remember to close all conn 
#
#


#TASK 1.4___________________________________________________________Server Side Function 


def monitor_and_send_gamestate(wfile, gamestate_ref, interval=2):
    """
    Periodically sends the game state to the client every 'interval' seconds.
    """
    last_state = None
    while True:
        current_state = gamestate_ref[0]
        if current_state != last_state:
            try:
                wfile.write(f"STATE:{current_state}\n")
                wfile.flush()
                last_state = current_state
            except Exception as e:
                logger.debug(f"[ERROR] Failed to send gamestate to client: {e}")
                break

        # Exit once the game is over
        if current_state == 2:
            break

        time.sleep(interval)

if __name__ == "__main__":
    main()
