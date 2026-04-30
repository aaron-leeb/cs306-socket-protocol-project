# Socket Tic-Tac-Toe Project

This project is a simple multiplayer Tic-Tac-Toe game that runs over a network.

One program is the **server**. It keeps track of the game and sends updates.

The other program is the **client**. Each player runs the client and types commands in the terminal.

## What This Project Does

- Lets 2 players connect to the same server
- Lets players start and join a Tic-Tac-Toe game
- Sends moves between players
- Lets players send simple chat messages

## Project Files

- `server/server.py` = runs the server
- `server/game.py` = game rules and board logic
- `client/client.py` = runs the player client
- `protocol.py` = shared message types and default port

## How To Run It

You will need **3 terminal windows**:

- 1 terminal for the server
- 1 terminal for player 1
- 1 terminal for player 2

### 1. Start the server

```sh
cd /Users/jack/Desktop/Spring2026/CS450/Project/cs306-socket-protocol-project/server
python3 server.py
```

### 2. Start player 1

```sh
cd /Users/jack/Desktop/Spring2026/CS450/Project/cs306-socket-protocol-project/client
python3 client.py
```

When asked, enter:

- Server IP: `127.0.0.1`
- Port: press Enter to use the default
- Player name: something like `Alice`

### 3. Start player 2

Open another terminal and run:

```sh
cd /Users/jack/Desktop/Spring2026/CS450/Project/cs306-socket-protocol-project/client
python3 client.py
```

When asked, enter:

- Server IP: `127.0.0.1`
- Port: press Enter to use the default
- Player name: something like `Bob`

## Commands To Use In The Client

After the client connects, type these in the **client terminal**:

- `/start` = create a new game
- `/join` = join the waiting game
- `/move 0 0` = place your mark on the board
- `/chat hello` = send a message to the other player
- `/help` = show commands
- `/exit` = quit

## Simple Example

Player 1:

```text
/start
/join
```

Player 2:

```text
/join
```

Then both players take turns using moves like:

```text
/move 0 0
/move 1 1
/move 0 2
```

## How The Board Works

The board uses row and column numbers:

- Top-left is `0 0`
- Top-middle is `0 1`
- Center is `1 1`
- Bottom-right is `2 2`

So if you type:

```text
/move 2 2
```

that means bottom-right corner.

## If The Port Does Not Work

The default port is stored in `protocol.py`.

If needed, change:

```python
DEFAULT_TCP_PORT = 50555
```

Make sure the server and both clients use the same port.

## In One Sentence

This is a terminal-based 2-player Tic-Tac-Toe game where a server manages the game and two clients connect and play.
