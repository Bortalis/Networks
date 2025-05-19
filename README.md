# Networks CITS3007 Project

**Lachoneus Flake 	(23858382)**
**Luke Vidovich 		(23814635)**

## Instructions
To use this code in the file to run multiplayer game of BEER follow theses steps:
1. **Start the Server** - Run Server.py
This will create a server for the incoming clients to connect to

2. **Start clients** - In two seperate terminals run the client.py twice
Therefore you should now have a Terminal for Server, Client 1 and Client 2
Client 1 and 2 should be placed into a multiplayer game at this point

3. **Play the game** - Follow the command prompts to play 
When manually placing ships Client 1 goes first, Client 2 waits, then the roles are swapped
After the placement, alternate between each client terminal when firing
A match will end once a player sinks all their opponent's ships '

## Spectators
If more than two clients connect, extra clients will become spectators. Spectators can watch the game in real-time and receive updates about moves and board states. Once the game ends the first two spectators waiting in the client queue will be able to play now, with the previous players being added to the back of the queue. 

## Controls
- Input coordinates as e.g., `A5`, `C10`.
- Type `quit` at any prompt to exit the game.
