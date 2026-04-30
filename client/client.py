
import asyncio
import socket
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from protocol import *


def discover_server(timeout=2):
    """Send UDP broadcast to discover the server's IP and port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)
    try:
        sock.sendto(b"DISCOVER_SERVER", ("<broadcast>", DEFAULT_UDP_PORT))
        data, _ = sock.recvfrom(1024)
        ip, port = data.decode().split(":")
        return ip, int(port)
    except Exception:
        return None, None
    finally:
        sock.close()

class Client:
    def __init__(self, host=None, port=None):
        # If host/port not provided, try to discover
        if host is None or port is None:
            ip, p = discover_server()
            if ip and p:
                print(f"[CLIENT] Discovered server at {ip}:{p}")
                self.host = ip
                self.port = p
            else:
                print("[CLIENT] Could not discover server. Defaulting to 127.0.0.1:{DEFAULT_TCP_PORT}")
                self.host = "127.0.0.1"
                self.port = DEFAULT_TCP_PORT
        else:
            self.host = host
            self.port = port
        self.reader = None
        self.writer = None
        self.connected = False
        self.my_symbol = None
        self.my_turn = False

    async def connect(self, name):
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=5,
            )
        except asyncio.TimeoutError:
            print(f"[CLIENT] Timed out connecting to {self.host}:{self.port}.")
            return False
        except ConnectionRefusedError:
            print(f"[CLIENT] Connection refused. Make sure the server is running on {self.host}:{self.port}.")
            return False
        except OSError as e:
            print(f"[CLIENT] Could not connect to {self.host}:{self.port}: {e}")
            return False

        print(f"[CLIENT] Connected to server at {self.host}:{self.port}\n")
        self.name = name
        self.connected = True
        # Send connect message as handshake
        connect_msg = {"type": MSG_TYPE_CONNECT, "name": name}
        print(f"Welcome, {name}!")
        print(f"Type /help for options")
        return await self.send_message(connect_msg)

    async def send_message(self, message):
        if not self.writer or self.writer.is_closing():
            print("[CLIENT] Not connected to the server.")
            self.connected = False
            return False
        try:
            self.writer.write(encode_message(message))
            await self.writer.drain()
            return True
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            print(f"[CLIENT] Lost connection while sending data: {e}")
            self.connected = False
            return False

    async def listen(self):
        try:
            while self.connected:
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
                    self.my_turn = bool(message.get("your_turn", False))
                    print(f"Game started. You are {self.my_symbol}.")
                    if self.my_turn:
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
                    self.my_turn = False
                    print("Type /start to play again.")
                elif msg_type == "opponent_disconnected":
                    self.my_turn = False
                    self.my_symbol = None
                    print(message.get("message", "Opponent disconnected"))
                    print("Type /start to begin a new game.")
                else:
                    print(f"[CLIENT] Unknown message type: {msg_type}")
        except ConnectionResetError:
            print("[CLIENT] Connection was reset by the server.")
        except Exception as e:
            print(f"[CLIENT] Error receiving message: {e}")
        finally:
            self.connected = False


    async def unified_input_loop(self):
        while self.connected:
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
                if not await self.send_message(msg):
                    break
                continue
            if s == "/join":
                msg = {"type": MSG_TYPE_JOIN_GAME}
                if not await self.send_message(msg):
                    break
                continue
            if s.startswith("/chat"):
                chat_msg = s[5:].strip()
                if chat_msg:
                    msg = {"type": MSG_TYPE_CHAT, "message": chat_msg}
                    if not await self.send_message(msg):
                        break
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
                if not await self.send_message(move_msg):
                    break
                continue
            if s == "/exit":
                print("Exiting game.")
                self.connected = False
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
    # Try UDP discovery first
    ip, port = discover_server()
    if ip and port:
        print(f"[CLIENT] Discovered server at {ip}:{port}")
    else:
        print("[CLIENT] Could not auto-discover server. Please enter manually.")
        ip = input("Enter server IP (default 127.0.0.1): ").strip() or "127.0.0.1"
        port_input = input(f"Enter server port (default {DEFAULT_TCP_PORT}): ").strip()
        try:
            port = int(port_input) if port_input else DEFAULT_TCP_PORT
        except ValueError:
            print(f"Invalid port, using {DEFAULT_TCP_PORT}.")
            port = DEFAULT_TCP_PORT
    name = input("Enter your player name: ")
    client = Client(host=ip, port=port)
    connected = await client.connect(name)
    if not connected:
        return
    await client.main_loop(name)

if __name__ == "__main__":
    asyncio.run(main())
