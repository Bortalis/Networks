"""
client.py

Connects to a Battleship server which runs the single-player game.
Simply pipes user input to the server, and prints all server responses.

TODO: Fix the message synchronization issue using concurrency (Tier 1, item 1).
"""
#import threading #will allow client and sever listening to be done at the same time

import socket
import threading

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
            server_disc.set() # Aerts the main thread that the server disconnected
            break
        # Process and display the message
        line = line.strip()
        if line == "GRID":
            # Begin reading board lines
            print("\n[Board]")
            while True:
                board_line = rfile.readline()
                if not board_line or board_line.strip() == "":
                    break
                print(board_line.strip())
        else:
            # Normal message
            print(line)
            if line[0] == '>': # True when ">> " is the first word TODO: Not a very secure method of checking
                now_sending.clear() # Time for User input
                now_sending.wait(timeout=None) # Wait until the user has sent ther input


def main():
    # Set up connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        rfile = s.makefile('r')
        wfile = s.makefile('w')

    # Start a thread for receiving messages
    sv_side = threading.Thread(target=receive_messages,args=(rfile,),daemon=True)
    sv_side.start()

    # Main thread handles sending user input
    try:
        while not server_disc.is_set():  # There is a connection to the sever
            if not now_sending.is_set(): # The sever is done sending messages
                user_input = input()
                wfile.write(user_input + '\n')
                wfile.flush()
                now_sending.set() # Server's turn to send a messages

    except KeyboardInterrupt:
        now_sending.set() # Unblocks the wait
        print("\n[INFO] Client exiting.")
    

if __name__ == "__main__":
    main()
