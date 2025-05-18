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
# 0 = placement phase
# 1 = firing phase
# 2 = game over phase


HOST = '127.0.0.1'
PORT = 5000

logging.basicConfig(
    filename="Server_log",
    level=logging.DEBUG,
    filemode="w"
)
logger = logging.getLogger(__name__)

game_running = threading.Event()

def multi_client(player1, player2):


    # Start threads to send game state updates to the clients
    gamestate_thread_P1 = threading.Thread(target=monitor_and_send_gamestate, args=(player1[3], gamestate_ref), daemon=True)
    gamestate_thread_P2 = threading.Thread(target=monitor_and_send_gamestate, args=(player2[3], gamestate_ref), daemon=True)
    gamestate_thread_P1.start()
    gamestate_thread_P2.start()

    run_multi_player_game_online(player1[2],player1[3],player2[2],player2[3], gamestate_ref)

    #put players back in the queue
    queue.append(player1)
    queue.append(player2)


queue = [] #players waiting for an opponent
players = [] #players playing

def main():
    try:
        logger.debug(f"[INFO] Server listening on {HOST}:{PORT}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            
            s.bind((HOST, PORT))
            s.listen()
            while True:
                conn, addr = s.accept()
                logger.debug(f"[INFO] Client connected from {addr}")
                rfile = conn.makefile('r')
                wfile = conn.makefile('w')
                queue.append((conn, addr, rfile, wfile))

                if len(players) == 2:
                    try:
                        wfile.write("WAITING: Game in progress, please wait for it to end...\n")
                        wfile.flush()

                    except Exception as e:
                        logger.debug(f"[ERROR] Failed to communicate with waiting client: {e}")
                    continue

                if len(queue) < 2: # Notify client if waiting for opponent
                    try:
                        wfile.write("WAITING: Hold on until another player to join...\n")
                        wfile.flush()

                    except Exception as e:
                        logger.debug(f"[ERROR] Failed to commiunicate with waiting client: {e}")
                else:
                    multi_client = threading.Thread(target=multi_client, args=(queue[0], queue[1]), daemon=True)
                    multi_client.start()
                    players.append(queue.pop(0))
                    players.append(queue.pop(0))


    except Exception as e:
        logger.exception("I don't even know what went wrong in this case",stack_info = True)

    logger.debug("[INFO] Server turning off")



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
