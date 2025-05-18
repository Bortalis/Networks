"""
client.py

Connects to a Battleship server which runs the single-player game.
Simply pipes user input to the server, and prints all server responses.

"""
#import threading #will allow client and sever listening to be done at the same time

import socket
import threading

import sys

gameState = 0 #gameState the client understands

def flush_input():
    try:
        import termios  # Unix
        import tty
        import select

        while True:
            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if dr:
                sys.stdin.read(1)
            else:
                break
    except ImportError:
        # Windows
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()


HOST = '127.0.0.1'
PORT = 5000
#python3 Networks\Project\client.py for testing purposes


server_disc = threading.Event() # Is true when the thead closes
now_sending = threading.Event() # Is true while the sever is sending lines
now_sending.set() # The server starts first


def receive_messages(rfile):
    """Continuously receive and display messages from the server"""
    while True:
        line = rfile.readline()
        if not line: # Stops the thread once the server disconnects
            print("[INFO] Server disconnected.")
            server_disc.set() # Alerts the main thread that the server disconnected
            break
        
        #if line == "Your turn!":
            #cls() maybe for later

        # Handle game state changes
        if line.startswith("STATE:"):
            try:
                gameState = int(line.split(":")[1])
                print(f"[INFO] Game phase is now: {gameState} (0=placing, 1=firing, 2=game over)")
            except (IndexError, ValueError):
                print("[WARNING] Received malformed state update from server.")
            continue  # Skip further processing for this line

        # Process and display the message
        line = line.strip()
        if line == "GRID":
            # Begin reading board lines
            while True:
                board_line = rfile.readline()
                if not board_line or board_line.strip() == "":
                    break
                print(board_line.strip())
        else:
            # Normal message
            print(line)
            if line == '>>': # True when ">> " is the line TODO: Not a very secure method of checking
                now_sending.clear() # Time for User input
                now_sending.wait(timeout=None) # Wait until the user has sent ther input

            # TASK4.1 process the server's responses, for example:
            #if line == 'RESULT MISS':
            #    print("[INFO] The shot was a miss!")
            #elif line == 'RESULT HIT':
            #    print("[INFO] The shot was a hit!")
            #elif line == '>>':  # Time for user input
            #    now_sending.clear() 
            #    now_sending.wait(timeout=None)  # Wait for the user to send input
        


def main():
    # Set up connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        rfile = s.makefile('r')
        wfile = s.makefile('w')


    print("\n[INFO] Successfully connected to Server")
    # Start a thread for receiving messages
    sv_side = threading.Thread(target=receive_messages,args=(rfile,),daemon=True)
    sv_side.start()

    # Main thread handles sending user input
    try:

        while not server_disc.is_set():  # There is a connection to the sever
            if not now_sending.is_set(): # The sever is done sending messages
                flush_input() #eats up any buffed input
                user_input = input()
                message = None

                #Format the message depending on the state command
                stateCheck(message,user_input,wfile)

                wfile.write(user_input + '\n')
                wfile.flush()


                now_sending.set() # Server's turn to send a messages

    except KeyboardInterrupt:
        now_sending.set() # Unblocks the wait
        print("\n[INFO] Client exiting.")


#TASK 1.4___________________________________________________________Client Side Function
def stateCheck(message,user_input,wfile):
    """Checks the state of the game and returns the appropriate message"""
    if gameState == 0: # Game is in the placement phase
        message = f"PLACE ship at location {user_input}"
        wfile.write(message + '\n')
        wfile.flush()

    elif gameState == 1: # Game is in the firing phase
        message = f"FIRE at location {user_input}"
        wfile.write(message + '\n')
        wfile.flush()

    elif gameState == 2: # Game is over
        return # Do nothing, the game is over

         

if __name__ == "__main__":
    main()
