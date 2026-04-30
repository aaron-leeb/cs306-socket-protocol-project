import asyncio
import sys
sys.path.append("..")
from protocol import *

class Client:
    def __init__(self, host="127.0.0.1", port=DEFAULT_TCP_PORT):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self, name):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print(f"[CLIENT] Connected to server at {self.host}:{self.port}\n")
        self.name = name
        # Send connect message as handshake
        connect_msg = {"type": MSG_TYPE_CONNECT, "name": name}
        print(f"Welcome, {name}!")
        print(f"Type /help for options")
        self.writer.write(encode_message(connect_msg))
        await self.writer.drain()

    async def listen(self):
        try:
            self.my_symbol = None
            self.my_turn = False
            while True:
                data = await self.reader.readline()
                if not data:
                    print("[CLIENT] Server closed the connection.")
                    break
                try:
                    message = decode_message(data)
                except Exception as e:
                    print(f"[CLIENT] Received malformed JSON: {e}")
                    continue
                msg_type = message.get("type")
                if msg_type == "waiting":
                    msg = message.get("message", "Waiting...")
                    print(f"{msg} (type /help to see options)")
                elif msg_type == "start":
                    self.my_symbol = message.get("symbol")
                    your_turn = bool(message.get("your_turn", False))
                    print(f"Game started. You are {self.my_symbol}.")
                    if your_turn:
                        print("It is your turn.")
                elif msg_type == "board":
                    board = message.get("board")
                    turn = message.get("turn")
                    if isinstance(board, list):
                        print("\nBoard:")
                        for row in board:
                            print(" ".join(cell if cell else "." for cell in row))
                    print(f"Turn: {turn}")
                    self.my_turn = self.my_symbol is not None and turn == self.my_symbol
                    if not self.my_turn:
                        print("Waiting for opponent to move.")
                elif msg_type == MSG_TYPE_CHAT:
                    print(f"[chat] {message.get('from')}: {message.get('message')}")
                elif msg_type == MSG_TYPE_ANNOUNCE:
                    print(f"[announcement] {message.get('message')}")
                elif msg_type == "error":
                    print(f"[error] {message.get('code')}: {message.get('message')}")
                elif msg_type == "game_over":
                    print(f"Game over: {message.get('result')}")
                    print("Type /start to play again.")
                elif msg_type == "opponent_disconnected":
                    print(message.get("message", "Opponent disconnected"))
                    break
                else:
                    print(f"[CLIENT] Unknown message type: {msg_type}")
        except Exception as e:
            print(f"[CLIENT] Error receiving message: {e}")


    async def unified_input_loop(self):
        while True:
            raw = await asyncio.to_thread(input, "")
            s = raw.strip()
            if s == "/help":
                print("\nOptions:")
                print("  /start             Start a new game of tick tac toe")
                print("  /join              Join a waiting game")
                print("  /move <row> <col>  Make a move (e.g. /move 1 2)")
                print("  /chat <message>    Send a chat message to your opponent")
                print("  /help              Show this help message")
                print("  /exit              Quit the game")
                continue
            if s == "/start":
                msg = {"type": MSG_TYPE_START_GAME}
                self.writer.write(encode_message(msg))
                await self.writer.drain()
                continue
            if s == "/join":
                msg = {"type": MSG_TYPE_JOIN_GAME}
                self.writer.write(encode_message(msg))
                await self.writer.drain()
                continue
            if s.startswith("/chat"):
                chat_msg = s[5:].strip()
                if chat_msg:
                    msg = {"type": MSG_TYPE_CHAT, "message": chat_msg}
                    self.writer.write(encode_message(msg))
                    await self.writer.drain()
                else:
                    print("Usage: /chat your message")
                continue
            if s.startswith("/move"):
                if not self.my_turn:
                    print("It's not your turn.")
                    continue
                parts = s[5:].strip().split()
                if len(parts) != 2:
                    print("Usage: /move <row> <col>")
                    continue
                try:
                    row = int(parts[0])
                    col = int(parts[1])
                except ValueError:
                    print("Row and col must be integers.")
                    continue
                move_msg = {"type": MSG_TYPE_MOVE, "row": row, "col": col}
                self.writer.write(encode_message(move_msg))
                await self.writer.drain()
                continue
            if s == "/exit":
                print("Exiting game.")
                if self.writer:
                    self.writer.close()
                    await self.writer.wait_closed()
                break
            print("Unknown command. Type /help for options.")

    async def main_loop(self, name):
        await asyncio.gather(
            self.listen(),
            self.unified_input_loop()
        )

async def main():
    host = input("Enter server IP (default 127.0.0.1): ").strip() or "127.0.0.1"
    port_input = input(f"Enter server port (default {DEFAULT_TCP_PORT}): ").strip()
    try:
        port = int(port_input) if port_input else DEFAULT_TCP_PORT
    except ValueError:
        print(f"Invalid port, using {DEFAULT_TCP_PORT}.")
        port = DEFAULT_TCP_PORT
    name = input("Enter your player name: ")
    client = Client(host=host, port=port)
    await client.connect(name)
    await client.main_loop(name)

if __name__ == "__main__":
    asyncio.run(main())
