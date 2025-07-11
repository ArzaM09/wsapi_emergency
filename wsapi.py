import asyncio
import threading
from app.websocket_server import WebsocketServer
from app.api import PerintahAPI

class ServerApp:
    def __init__(self):
        self.websocket_server = WebsocketServer()
        self.api = PerintahAPI(self.websocket_server)

    def start(self):
        threading.Thread(target=self.api.run, daemon=True).start()
        asyncio.run(self.websocket_server.run())

if __name__ == "__main__":
    ServerApp().start()
