import asyncio
import sys
sys.path.append("..")
from protocol import *
from game import Game

class Server:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()  # Track all connected client writers
        self.game = None
        self.player_map = {}  # writer -> player_name
        self.writer_map = {}  # player_name -> writer

    async def broadcast_message(self, message):
        # Broadcast a message to all connected clients
        for client_writer in self.clients:
            try:
                client_writer.write(message.encode())
                await client_writer.drain()
            except Exception:
                pass  # Ignore errors for dead clients

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"[SERVER] New connection from {addr}")
        self.clients.add(writer)
        player_name = None

        try:
            while True:
                data = await reader.readline()
                if not data:
                    print(f"[SERVER] Client {addr} disconnected")
                    break

                try:
                    message = decode_message(data)
                except Exception as e:
                    print(f"[SERVER] Received malformed JSON from {addr}: {e}")
                    # Send protocol error message
                    error_msg = encode_message({
                        "type": MSG_TYPE_ERROR,
                        "code": "invalid_json",
                        "message": "Malformed JSON received."
                    })
                    writer.write(error_msg)
                    await writer.drain()
                    continue

                print(f"[SERVER] Received from {addr}: {message}")

                msg_type = message.get("type")

                # Handle /start command (start a new game lobby)
                if msg_type == MSG_TYPE_START_GAME:
                    if self.game and self.game.state in ("waiting", "in_progress"):
                        info_msg = encode_message({
                            "type": MSG_TYPE_ERROR,
                            "code": "game_already_exists",
                            "message": "A game is already waiting or in progress."
                        })
                        writer.write(info_msg)
                        await writer.drain()
                    else:
                        self.game = Game("game1")
                        self.game.state = "waiting"
                        # Announce to all clients that a new game has started
                        announcement = encode_message({
                            "type": MSG_TYPE_ANNOUNCE,
                            "message": "A new game has been started. Type /join to join the game."
                        })
                        for w in self.clients:
                            w.write(announcement)
                            await w.drain()
                        await self.broadcast_message(encode_message({
                            "type": MSG_TYPE_WAITING,
                            "message": "A new game has been started. Type /join to join the game."
                        }))
                    continue

                # Handle /join command (join the waiting game)
                if msg_type == MSG_TYPE_JOIN_GAME:
                    if not self.game or self.game.state != "waiting":
                        info_msg = encode_message({
                            "type": MSG_TYPE_ERROR,
                            "code": "no_game_waiting",
                            "message": "No game is waiting to join. Type /start to create a new game."
                        })
                        writer.write(info_msg)
                        await writer.drain()
                    elif len(self.game.players) >= 2:
                        info_msg = encode_message({
                            "type": MSG_TYPE_ERROR,
                            "code": "game_full",
                            "message": "Game is full."
                        })
                        writer.write(info_msg)
                        await writer.drain()
                    else:
                        # Use the player's name if available, else assign a default
                        pname = player_name or f"Player{len(self.game.players)+1}"
                        try:
                            self.game.add_player(pname)
                            self.player_map[writer] = pname
                            self.writer_map[pname] = writer
                            if len(self.game.players) == 1:
                                waiting_msg = encode_message({
                                    "type": MSG_TYPE_WAITING,
                                    "message": "Waiting for another player to join."
                                })
                                writer.write(waiting_msg)
                                await writer.drain()
                            elif len(self.game.players) == 2:
                                # Start game for both
                                for idx, pname in enumerate(self.game.players):
                                    start_msg = encode_message({
                                        "type": MSG_TYPE_START,
                                        "symbol": "X" if idx == 0 else "O",
                                        "your_turn": idx == 0
                                    })
                                    self.writer_map[pname].write(start_msg)
                                    await self.writer_map[pname].drain()
                                await self.send_board()
                        except Exception as e:
                            error_msg = encode_message({
                                "type": MSG_TYPE_ERROR,
                                "code": "invalid_message",
                                "message": str(e)
                            })
                            writer.write(error_msg)
                            await writer.drain()
                    continue

                if msg_type == MSG_TYPE_CHAT:
                    # Broadcast chat message to all players and log it
                    chat_text = message.get("message", "")
                    if player_name:
                        print(f"[SERVER] Chat from {player_name}: {chat_text}")
                        chat_obj = encode_message({
                            "type": MSG_TYPE_CHAT,
                            "from": player_name,
                            "message": chat_text
                        })
                        for w in self.writer_map.values():
                            w.write(chat_obj)
                            await w.drain()
                    continue

                if msg_type == MSG_TYPE_CONNECT:
                    # Initial handshake, store player name
                    player_name = message.get("name")
                    if not player_name:
                        error_msg = encode_message({
                            "type": MSG_TYPE_ERROR,
                            "code": "invalid_message",
                            "message": "Missing player name."
                        })
                        writer.write(error_msg)
                        await writer.drain()
                        continue
                    # Only store name, do not join game yet
                    self.player_map[writer] = player_name
                    self.writer_map[player_name] = writer
                    # Announce to all other clients
                    num_players = len(self.player_map)
                    announcement = encode_message({
                        "type": MSG_TYPE_ANNOUNCE,
                        "message": f"{player_name} has connected to the server. Players connected: {num_players}"
                    })
                    for w in self.clients:
                        w.write(announcement)
                        await w.drain()
                    continue
                elif msg_type == MSG_TYPE_MOVE:
                    # Player move
                    if not self.game or player_name is None:
                        continue
                    row = message.get("row")
                    col = message.get("col")
                    try:
                        self.game.make_move(player_name, (row, col))
                        await self.send_board()
                        if self.game.state == "finished":
                            # Game over
                            winner = self.game.winner
                            if winner:
                                result = "X wins" if winner == self.game.players[0] else "O wins"
                            else:
                                result = "draw"
                            game_over_msg = encode_message({
                                "type": MSG_TYPE_GAME_OVER,
                                "result": result
                            })
                            for w in self.writer_map.values():
                                w.write(game_over_msg)
                                await w.drain()
                    except Exception as e:
                        error_msg = encode_message({
                            "type": MSG_TYPE_ERROR,
                            "code": "invalid_move",
                            "message": str(e)
                        })
                        writer.write(error_msg)
                        await writer.drain()
                        # Always send board after error so client can re-prompt
                        if self.game:
                            await self.send_board()
                # TODO: handle disconnects, opponent_disconnected, etc.

        except Exception as e:
            print(f"[SERVER] Error with {addr}: {e}")

        finally:
            self.clients.discard(writer)
            # Remove player from mappings
            if player_name and player_name in self.writer_map:
                del self.writer_map[player_name]
            if writer in self.player_map:
                del self.player_map[writer]


            # Remove player from game and notify opponent (only if a game exists)
            if self.game and player_name and player_name in self.game.players:
                try:
                    self.game.players.remove(player_name)
                except Exception:
                    pass
                # Notify opponent if still connected
                if len(self.game.players) == 1:
                    opponent = self.game.players[0]
                    w = self.writer_map.get(opponent)
                    if w:
                        msg = encode_message({
                            "type": MSG_TYPE_OPPONENT_DISCONNECTED,
                            "message": f"Opponent {player_name} disconnected."
                        })
                        try:
                            w.write(msg)
                            await w.drain()
                        except Exception:
                            pass
                # Optionally reset game state if both players gone
                if len(self.game.players) == 0:
                    self.game = None

            writer.close()
            await writer.wait_closed()
            print(f"[SERVER] Connection closed for {addr}")

    async def send_board(self):
        # Send board state to all players
        if not self.game:
            return
        board_msg = encode_message({
            "type": MSG_TYPE_BOARD,
            "board": self.render_board(),
            "turn": self.get_current_turn_symbol()
        })
        for w in self.writer_map.values():
            w.write(board_msg)
            await w.drain()

    def render_board(self):
        # Convert internal board to protocol format
        # 1 = X, -1 = O, 0 = ""
        if not self.game:
            return [["" for _ in range(3)] for _ in range(3)]
        return [["X" if cell == 1 else "O" if cell == -1 else "" for cell in row] for row in self.game.board]

    def get_current_turn_symbol(self):
        if self.game.state != "in_progress":
            return None
        idx = self.game.turn % 2
        return "X" if idx == 0 else "O"

    async def start(self):
        self.server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = self.server.sockets[0].getsockname()
        print(f"[SERVER] Listening on {addr}")

        async with self.server:
            await self.server.serve_forever()

async def main():
    server = Server()
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())