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

game_running = threading.Event()

def multi_client(player1, player2):

    logger.debug("whats0")
    conn1 = player1[0]
    conn2 = player2[0]
    rfile1 = conn1.makefile('r')
    wfile1 = conn1.makefile('w')

    logger.debug("whats1")

    # Start threads to send game state updates to the clients
    gamestate_thread_P1 = threading.Thread(target=monitor_and_send_gamestate, args=(wfile1, gamestate_ref), daemon=True)
    gamestate_thread_P2 = threading.Thread(target=monitor_and_send_gamestate, args=(wfile2, gamestate_ref), daemon=True)
    gamestate_thread_P1.start()
    gamestate_thread_P2.start()

    run_multi_player_game_online(rfile1,wfile1,rfile2,wfile2, gamestate_ref)

    #put players back in the queue
    queue.append(player1)
    queue.append(player2)

    game_running.clear()


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

                
                queue.append((conn,addr)) #keep their addr for id for T3.3?

                if len(queue) >= 2 and not game_running.is_set():
                    client_thread = threading.Thread(target=multi_client, args=(queue[0], queue[1]), daemon=True)
                    queue.pop(0)
                    queue.pop(0)
                    game_running.set()
                    client_thread.start()

    except Exception as e:
        logger.exception("I don't even know what went wrong in this case",stack_info = True)

    logger.debug("[INFO] Server turning off")




#Server should not end for now                    
#                if len(players) >= 2:
#                    break
#            for thread in threads: #waits for all players to finish their game before closing
#                thread.join()
#            logger.debug("[INFO] All threads have joined")
#            #remember to close all conn 


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
