import asyncio
import sys
sys.path.append("..")
from protocol import EXIT_COMMAND

class Server:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()  # Track all connected client writers

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

        try:
            while True:
                data = await reader.readline()
                if not data:
                    print(f"[SERVER] Client {addr} disconnected")
                    break

                message = data.decode().strip()
                print(f"[SERVER] Received from {addr}: {message}")

                # Broadcast the message to all clients
                broadcast_msg = f"{addr}: {message}\n"
                await self.broadcast_message(broadcast_msg)

        except Exception as e:
            print(f"[SERVER] Error with {addr}: {e}")

        finally:
            self.clients.discard(writer)
            writer.close()
            await writer.wait_closed()
            print(f"[SERVER] Connection closed for {addr}")

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