
import random


BOARD_SIZE = 10
SHIPS = [
    ("Carrier", 5),
    ("Battleship", 4),
    ("Cruiser", 3),
    ("Submarine", 3),
    ("Destroyer", 2)
]


class Board:
    """
    Represents a single Battleship board with hidden ships.
    We store:
      - self.hidden_grid: tracks real positions of ships ('S'), hits ('X'), misses ('o')
      - self.display_grid: the version we show to the player ('.' for unknown, 'X' for hits, 'o' for misses)
      - self.placed_ships: a list of dicts, each dict with:
          {
             'name': <ship_name>,
             'positions': set of (r, c),
          }
        used to determine when a specific ship has been fully sunk.

    In a full 2-player networked game:
      - Each player has their own Board instance.
      - When a player fires at their opponent, the server calls
        opponent_board.fire_at(...) and sends back the result.
    """

    def __init__(self, size=BOARD_SIZE):
        self.size = size
        # '.' for empty water
        self.hidden_grid = [['.' for _ in range(size)] for _ in range(size)]
        # display_grid is what the player or an observer sees (no 'S')
        self.display_grid = [['.' for _ in range(size)] for _ in range(size)]
        self.placed_ships = []  # e.g. [{'name': 'Destroyer', 'positions': {(r, c), ...}}, ...]

    def place_ships_randomly(self, ships=SHIPS):
        """
        Randomly place each ship in 'ships' on the hidden_grid, storing positions for each ship.
        In a networked version, you might parse explicit placements from a player's commands
        (e.g. "PLACE A1 H BATTLESHIP") or prompt the user for board coordinates and placement orientations; 
        the self.place_ships_manually() can be used as a guide.
        """
        for ship_name, ship_size in ships:
            placed = False
            while not placed:
                orientation = random.randint(0, 1)  # 0 => horizontal, 1 => vertical
                row = random.randint(0, self.size - 1)
                col = random.randint(0, self.size - 1)

                if self.can_place_ship(row, col, ship_size, orientation):
                    occupied_positions = self.do_place_ship(row, col, ship_size, orientation)
                    self.placed_ships.append({
                        'name': ship_name,
                        'positions': occupied_positions
                    })
                    placed = True


    def place_ships_manually(self, ships=SHIPS):
        """
        Prompt the user for each ship's starting coordinate and orientation (H or V).
        Validates the placement; if invalid, re-prompts.
        """
        print("\nPlease place your ships manually on the board.")
        for ship_name, ship_size in ships:
            while True:
                self.print_display_grid(show_hidden_board=True)
                print(f"\nPlacing your {ship_name} (size {ship_size}).")
                coord_str = input("  Enter starting coordinate (e.g. A1): ").strip()
                orientation_str = input("  Orientation? Enter 'H' (horizontal) or 'V' (vertical): ").strip().upper()

                try:
                    row, col = parse_coordinate(coord_str)
                except ValueError as e:
                    print(f"  [!] Invalid coordinate: {e}")
                    continue

                # Convert orientation_str to 0 (horizontal) or 1 (vertical)
                if orientation_str == 'H':
                    orientation = 0
                elif orientation_str == 'V':
                    orientation = 1
                else:
                    print("  [!] Invalid orientation. Please enter 'H' or 'V'.")
                    continue

                # Check if we can place the ship
                if self.can_place_ship(row, col, ship_size, orientation):
                    occupied_positions = self.do_place_ship(row, col, ship_size, orientation)
                    self.placed_ships.append({
                        'name': ship_name,
                        'positions': occupied_positions
                    })
                    break
                else:
                    print(f"  [!] Cannot place {ship_name} at {coord_str} (orientation={orientation_str}). Try again.")


    def can_place_ship(self, row, col, ship_size, orientation):
        """
        Check if we can place a ship of length 'ship_size' at (row, col)
        with the given orientation (0 => horizontal, 1 => vertical).
        Returns True if the space is free, False otherwise.
        """
        if orientation == 0:  # Horizontal
            if col + ship_size > self.size:
                return False
            for c in range(col, col + ship_size):
                if self.hidden_grid[row][c] != '.':
                    return False
        else:  # Vertical
            if row + ship_size > self.size:
                return False
            for r in range(row, row + ship_size):
                if self.hidden_grid[r][col] != '.':
                    return False
        return True

    def do_place_ship(self, row, col, ship_size, orientation):
        """
        Place the ship on hidden_grid by marking 'S', and return the set of occupied positions.
        """
        occupied = set()
        if orientation == 0:  # Horizontal
            for c in range(col, col + ship_size):
                self.hidden_grid[row][c] = 'S'
                occupied.add((row, c))
        else:  # Vertical
            for r in range(row, row + ship_size):
                self.hidden_grid[r][col] = 'S'
                occupied.add((r, col))
        return occupied

    def fire_at(self, row, col):
        """
        Fire at (row, col). Return a tuple (result, sunk_ship_name).
        Possible outcomes:
          - ('hit', None)          if it's a hit but not sunk
          - ('hit', <ship_name>)   if that shot causes the entire ship to sink
          - ('miss', None)         if no ship was there
          - ('already_shot', None) if that cell was already revealed as 'X' or 'o'

        The server can use this result to inform the firing player.
        """
        cell = self.hidden_grid[row][col]
        if cell == 'S':
            # Mark a hit
            self.hidden_grid[row][col] = 'X'
            self.display_grid[row][col] = 'X'
            # Check if that hit sank a ship
            sunk_ship_name = self._mark_hit_and_check_sunk(row, col)
            if sunk_ship_name:
                return ('hit', sunk_ship_name)  # A ship has just been sunk
            else:
                return ('hit', None)
        elif cell == '.':
            # Mark a miss
            self.hidden_grid[row][col] = 'o'
            self.display_grid[row][col] = 'o'
            return ('miss', None)
        elif cell == 'X' or cell == 'o':
            return ('already_shot', None)
        else:
            # In principle, this branch shouldn't happen if 'S', '.', 'X', 'o' are all possibilities
            return ('already_shot', None)

    def _mark_hit_and_check_sunk(self, row, col):
        """
        Remove (row, col) from the relevant ship's positions.
        If that ship's positions become empty, return the ship name (it's sunk).
        Otherwise return None.
        """
        for ship in self.placed_ships:
            if (row, col) in ship['positions']:
                ship['positions'].remove((row, col))
                if len(ship['positions']) == 0:
                    return ship['name']
                break
        return None

    def all_ships_sunk(self):
        """
        Check if all ships are sunk (i.e. every ship's positions are empty).
        """
        for ship in self.placed_ships:
            if len(ship['positions']) > 0:
                return False
        return True

    def print_display_grid(self, show_hidden_board=False):
        """
        Print the board as a 2D grid.
        
        If show_hidden_board is False (default), it prints the 'attacker' or 'observer' view:
        - '.' for unknown cells,
        - 'X' for known hits,
        - 'o' for known misses.
        
        If show_hidden_board is True, it prints the entire hidden grid:
        - 'S' for ships,
        - 'X' for hits,
        - 'o' for misses,
        - '.' for empty water.
        """
        # Decide which grid to print
        grid_to_print = self.hidden_grid if show_hidden_board else self.display_grid

        # Column headers (1 .. N)
        print("  " + "".join(str(i + 1).rjust(2) for i in range(self.size)))
        # Each row labeled with A, B, C, ...
        for r in range(self.size):
            row_label = chr(ord('A') + r)
            row_str = " ".join(grid_to_print[r][c] for c in range(self.size))
            print(f"{row_label:2} {row_str}")


def parse_coordinate(coord_str):
    """
    Convert something like 'B5' into zero-based (row, col).
    Example: 'A1' => (0, 0), 'C10' => (2, 9)
    """
    coord_str = coord_str.strip().upper()
    row_letter = coord_str[0]
    col_digits = coord_str[1:]

    row = ord(row_letter) - ord('A')
    col = int(col_digits) - 1  # zero-based

    # simple valididation forces coordinates within bounds
    if row > 9:
        row = 9
    elif row < 0:
        row = 0
    if col > 9:
        col = 9
    elif col < 0:
        col = 0
    return (row, col)



def run_single_player_game_online(rfile, wfile):
    """
    A test harness for running the single-player game with I/O redirected to socket file objects.
    Expects:
      - rfile: file-like object to .readline() from client
      - wfile: file-like object to .write() back to client
    """
    gameState = 0 # 0 = waiting for player to place ships, 1 = game in progress, 2 = game over

    def send(msg):
        wfile.write(msg + '\n')
        wfile.flush()

    def send_board(board,show_hidden=False):
        grid_to_send = board.hidden_grid if show_hidden else board.display_grid
        wfile.write("GRID\n")
        wfile.write("_|" + " ".join(str(i + 1).rjust(2) for i in range(board.size)) + '\n')
        for r in range(board.size):
            row_label = chr(ord('A') + r)
            row_str = "  ".join(grid_to_send[r][c] for c in range(board.size))
            wfile.write(f"{row_label:2} {row_str}\n")
        wfile.write('\n')
        wfile.flush()

    def recv():
        return rfile.readline().strip()

    board = Board(BOARD_SIZE)
    board.place_ships_manually(SHIPS)
    gameState = 1 # Game is in progress, now in firing phase 

    send("Welcome to Online Single-Player Battleship! Try to sink all the ships. Type 'quit' to exit.")

    moves = 0
    while True:
        send_board(board)
        send("Enter coordinate to fire at (e.g. B5):")
        send(">> ")
        guess = recv()
        if guess.lower() == 'quit':
            send("Thanks for playing. Goodbye.")
            return

        try:
            row, col = parse_coordinate(guess)
            result, sunk_name = board.fire_at(row, col)
            moves += 1

            if result == 'hit':
                if sunk_name:
                    send(f"HIT! You sank the {sunk_name}!")
                else:
                    send("HIT!")
                if board.all_ships_sunk():
                    send_board(board)
                    send(f"Congratulations! You sank all ships in {moves} moves.")
                    gameState = 2 # Game over
                    return
            elif result == 'miss':
                send("MISS!")
            elif result == 'already_shot':
                send("You've already fired at that location.")
        except ValueError as e:
            send(f"Invalid input: {e}")

def run_multi_player_game_online(rfile1, wfile1, rfile2, wfile2):

    gameState = 0 # 0 = waiting for player to place ships, 1 = game in progress, 2 = game over

    def send(msg,player):
        if player == 1:
            wfile1.write(msg + '\n')
            wfile1.flush()
        else:
            wfile2.write(msg + '\n')
            wfile2.flush()
            
    def send_board(board, player, show_hidden = False):
        grid = board.hidden_grid if show_hidden else board.display_grid

        if player == 1:
            wfile1.write("GRID\n")
            wfile1.write("_|" + " ".join(str(i + 1).rjust(2) for i in range(board.size)) + '\n')
            for r in range(board.size):
                row_label = chr(ord('A') + r)
                row_str = "  ".join(grid[r][c] for c in range(board.size))
                wfile1.write(f"{row_label:2} {row_str}\n")
            wfile1.write('\n')
            wfile1.flush()
        else: 
            wfile2.write("GRID\n")
            wfile2.write("_|" + " ".join(str(i + 1).rjust(2) for i in range(board.size)) + '\n')
            for r in range(board.size):
                row_label = chr(ord('A') + r)
                row_str = "  ".join(grid[r][c] for c in range(board.size))
                wfile2.write(f"{row_label:2} {row_str}\n")
            wfile2.write('\n')
            wfile2.flush()


    def recv(player):
        if player == 1:
            return rfile1.readline().strip()
        else:
            return rfile2.readline().strip()
    
    player1_board = Board(BOARD_SIZE)
    player2_board = Board(BOARD_SIZE)

    send("Welcome to Online Multi-Player Battleship! Try to sink all the ships. Type 'quit' to exit.",1)
    send("Welcome to Online Multi-Player Battleship! Try to sink all the ships. Type 'quit' to exit.",2)

    testing = False 

    if testing: #REMOVE LATER!!!!!!!!!!!!!!????????????????
        player1_board.place_ships_randomly(SHIPS)
        player2_board.place_ships_randomly(SHIPS)

    else:
        player1_board.place_ships_manually(SHIPS)
        player2_board.place_ships_manually(SHIPS) 

    gameState = 1 # Game state is now in progress 

    # Player 1 starts off
    current_player = 1
    while True:
        # Turn tracker and manager
        send(f"Your turn!",current_player)
        if current_player == 1:
            board_in_use = player1_board
            opponent_board = player2_board
        else:
            board_in_use = player2_board
            opponent_board = player1_board

        # Display boards
        send(f"Your Opponent's board:", current_player)
        send_board(opponent_board, current_player)
        send(f"Your board:", current_player)
        send_board(board_in_use, current_player, True)



        # Get the shot from the current player
        send("Enter a coordinate to fire at (or 'quit' to forfeit): ", current_player)
        send(">>", current_player)
        guess = recv(current_player)

        if guess.lower() == 'quit':
            send(f"Player {current_player} forfeits! Player {3 - current_player} wins!", current_player)
            send(f"Player {current_player} forfeits! Player {3 - current_player} wins!", 3 - current_player)
            gameState = 2 # Game over
            break

        try:
            row, col = parse_coordinate(guess)
            result, sunk_name = opponent_board.fire_at(row, col)

            if result == 'hit':
                if sunk_name:
                    send(f"HIT! You sank the {sunk_name}!", current_player)
                else:
                    send("HIT!", current_player)
            elif result == 'miss':
                send("MISS!", current_player)
            elif result == 'already_shot':
                send("You've already shot at that spot. Pay attention.", current_player)
       
            # Check if the opponent has lost all ships
            if opponent_board.all_ships_sunk():
                send(f"\nPlayer {current_player} wins! All ships have been sunk.", current_player)
                gameState = 2 # Game over
                break

            # Switch turns between Player 1 and Player 2
            current_player = 3 - current_player
        except ValueError as e:
            send("  Invalid input, better luck next shot...", current_player)



def start_game_locally():
    while True:
        print("Welcome! Please indicate what you want")
        print("1: singleplayer")
        print("2: multiplayer")
        print("3: quit")
        print(">> ")
        choice = input()
        if choice == "1":
            run_single_player_game_locally()
            break
        elif choice == "2":
            run_multi_player_game_locally()
            break
        elif choice == "3":
            print("Goodbye!")
            break
        else: 
            print("That wasn't a valid input, try again.") 

def run_single_player_game_locally():
    """
    A test harness for local single-player mode, demonstrating two approaches:
     1) place_ships_manually()
     2) place_ships_randomly()

    Then the player tries to sink them by firing coordinates.
    """
    board = Board(BOARD_SIZE)

    # Ask user how they'd like to place ships
    choice = input("Place ships manually (M) or randomly (R)? [M/R]: ").strip().upper()
    if choice == 'M':
        board.place_ships_manually(SHIPS)
    else:
        board.place_ships_randomly(SHIPS)

    print("\nNow try to sink all the ships!")
    moves = 0
    while True:
        board.print_display_grid()
        guess = input("\nEnter coordinate to fire at (or 'quit'): ").strip()
        if guess.lower() == 'quit':
            print("Thanks for playing. Exiting...")
            return

        try:
            row, col = parse_coordinate(guess)
            result, sunk_name = board.fire_at(row, col)
            moves += 1

            if result == 'hit':
                if sunk_name:
                    print(f"  >> HIT! You sank the {sunk_name}!")
                else:
                    print("  >> HIT!")
                if board.all_ships_sunk():
                    board.print_display_grid()
                    print(f"\nCongratulations! You sank all ships in {moves} moves.")
                    break
            elif result == 'miss':
                print("  >> MISS!")
            elif result == 'already_shot':
                print("  >> You've already fired at that location. Try again.")

        except ValueError as e:
            print("  >> Invalid input:", e)

def run_multi_player_game_locally():
    testing = True

    player1_board = Board(BOARD_SIZE)
    player2_board = Board(BOARD_SIZE)

    if testing == True: #REMOVE LATER!!!!!!!!!!!!!!
        player1_board.place_ships_randomly(SHIPS)
        player2_board.place_ships_randomly(SHIPS)

    else:
        print("Player 1, place your ships.")
        player1_board.place_ships_manually(SHIPS)

        print("\nPlayer 2, place your ships.")
        player2_board.place_ships_manually(SHIPS)

    # Player turn tracker
    current_player = 1
    while True:
        # Who's turn is it? swap boards?
        if current_player == 1:
            print("\nPlayer 1's turn!")
            board_in_use = player1_board
            opponent_board = player2_board
        else:
            print("\nPlayer 2's turn!")
            board_in_use = player2_board
            opponent_board = player1_board

        # Display the current player's board (without showing ships)
        print(f"\nPlayer {current_player} board:")
        board_in_use.print_display_grid(True)

        # Get the shot from the current player
        guess = input("Enter a coordinate to fire at (or 'quit' to forfeit): ").strip()

        if guess.lower() == 'quit':
            print(f"Player {current_player} forfeits! Player {3 - current_player} wins!")
            break
        #3 - current_player is used to switch between 1 and 2

        try:
            # Parse the coordinate entered
            row, col = parse_coordinate(guess)

            # check if it's a hit or miss
            result, sunk_name = opponent_board.fire_at(row, col)

            if result == 'hit':
                if sunk_name:
                    print(f"  >> HIT! You sank the {sunk_name}!")
                else:
                    print("  >> HIT!")
            elif result == 'miss':
                print("  >> MISS!")
            elif result == 'already_shot':
                print("  >> You've already shot at that spot. Try again.")

            print("\nOpponent's board after your shot:")
            opponent_board.print_display_grid()
            
            # Check if the opponent has lost all ships
            if opponent_board.all_ships_sunk():
                print(f"\nPlayer {current_player} wins! All ships have been sunk.")
                break

            # Switch turns between Player 1 and Player 2
            if current_player == 1:
                current_player = 2
            else:   
                current_player = 1

        except ValueError as e:
            print("  >> Invalid input:", e)

if __name__ == "__main__":
    # Optional: run this file as a script to test single-player mode
    print("--Online functionallity will be disabled while Running locally--")
    start_game_locally()
