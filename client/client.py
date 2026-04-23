import asyncio
import sys
sys.path.append("..")
from protocol import EXIT_COMMAND

class Client:
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print(f"[CLIENT] Connected to server at {self.host}:{self.port}")

    async def listen(self):
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    print("[CLIENT] Server closed the connection.")
                    break
                print(f"\n[SERVER] {data.decode().strip()}")
        except Exception as e:
            print(f"[CLIENT] Error receiving message: {e}")

    async def main_loop(self):
        listen_task = asyncio.create_task(self.listen())
        try:
            while True:
                message = await asyncio.get_event_loop().run_in_executor(None, lambda: input(f"[CLIENT] Enter message (type '{EXIT_COMMAND}' to quit): "))
                if message.lower() == EXIT_COMMAND:
                    print("[CLIENT] Exiting and closing connection...")
                    break
                if not message.endswith("\n"):
                    message += "\n"
                self.writer.write(message.encode())
                await self.writer.drain()
        finally:
            self.writer.close()
            await self.writer.wait_closed()
            listen_task.cancel()
            print("[CLIENT] Connection closed")

async def main():
    client = Client()
    await client.connect()
    await client.main_loop()

if __name__ == "__main__":
    asyncio.run(main())