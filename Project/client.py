"""
client.py

Connects to a Battleship server which runs the single-player game.
Simply pipes user input to the server, and prints all server responses.

"""
import socket
import threading
import time
import msvcrt
import os

def cls():
    os.system("cls")

gameState = 0 #gameState the client understands

HOST = '127.0.0.1'
PORT = 5000
#python3 Networks\Project\client.py for testing purposes

server_disc = threading.Event() # Is true when the thead closes
now_sending = threading.Event() # Is true while the sever is sending lines
now_sending.set() # The server starts first

def flush_input(): #removes up any buffered up input
    while msvcrt.kbhit():
        msvcrt.getch()

def quick_time_event(): #30 second timeout for inputs
    timeout = 30
    print(end='', flush=True)
    start_time = time.time()
    input_str = ''
    while True:
        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char == '\r':  # Enter key
                break
            elif char == '\b':  # Backspace
                if input_str:
                    input_str = input_str[:-1]
                    print('\b \b', end='', flush=True)
            else:
                input_str += char
                print(char, end='', flush=True)
        if time.time() - start_time > timeout:
            print("\nTimed out!")
            return "QUIT"
        time.sleep(0.05) # we want to check every so often, but not so often that it strains performance
    print(flush=True) # used as a new line
    if input_str == '':
        return '-'#empty input isnt valid, but the connection is not brokn
    return input_str

def receive_messages(rfile):
    """Continuously receive and display messages from the server"""
    global gameState
    do_cls = True
    while True:
        try:
            line = rfile.readline()
            if not line: # Stops the thread once the server disconnects
                print("[INFO] Server disconnected.")
                server_disc.set() # Alerts the main thread that the server disconnected
                break
        except:
            print("[ERROR] Server error.")
            server_disc.set() # Alerts the main thread that the server disconnected
            break
        
        if line.strip() == "Invalid input, try again." or line.strip() == "--GAME START!--":    
            cls()
            do_cls = False
        if line.strip() == "Your turn!":
            if do_cls:
                cls()
            do_cls = True


            

        # Handle game state changes
        if line.startswith("STATE:"):
            try:
                gameState = int(line.split(":")[1])
                #print(f"[INFO] Game phase is now: {gameState} (0=placing, 1=firing, 2=game over)")
            except (IndexError, ValueError):
                print("[WARNING] Received malformed state update from server.")
            continue  # Skip further processing for this line

        # Process and display the message
        line = line.strip()
        if line == "GRID":
            while True:
                board_line = rfile.readline()
                if not board_line or board_line.strip() == "":
                    break
                print(board_line.strip())

        else:
            print(line)
            if line == '>>': #input request flag
                now_sending.clear()
                now_sending.wait(timeout=None) # Wait until the user has sent ther input

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
        while not server_disc.is_set():  # There is a connection to the server
            if not now_sending.is_set(): # The server is done sending messages

                flush_input() 
                user_input = quick_time_event()
                
                wfile.write(user_input + '\n')
                wfile.flush()

                
                now_sending.set() # Server's turn to send a messages
    except KeyboardInterrupt:
        now_sending.set() # Unblocks the wait
        print("\n[INFO] Client exiting.")

if __name__ == "__main__":
    main()
