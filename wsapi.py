import asyncio
import threading
import websockets
from flask import Flask, request, jsonify
import websockets.exceptions
import websockets.server

#websocket Server Class
class WebSocketServer:
    def __init__(self, host='0.0.0.0', port = 8765):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.antrian_pesan = asyncio.Queue()

    async def handler(self, websocket, path):
        print(f"[ESP32] Terkoneksi : {websocket.remote_address}")
        self.connected_clients.add(websocket)
        try:
            async for pesan in websocket:
                print(f"[ESP32] Pesan dari {websocket.remote_address}: {pesan}")
                await websocket.send("ACK: " + pesan)
        except websockets.exceptions.ConnectionClosed:
            print(f"[ESP32] Terputus : {websocket.remote_address}")
        finally:
            self.connected_clients.remove(websocket)

    async def sender_loop(self):
        while True:
            pesan = await self.antrian_pesan.get()
            for ws in self.connected_clients.copy():
                try:
                    await ws.send(pesan)
                    print(f"[Websocket] Mengirim : {pesan} Ke {ws.remote_address}")
                except Exception as e:
                    print (f"[Websocket] Gagal Mengirimkan Pesan : {e}")
    
    async def run(self):
        self.loop = asyncio.get_running_loop() 
        print(f"[Websocket] dijalankan di ws://{self.host}:{self.port}")
        await websockets.serve(self.handler, self.host, self.port, ping_interval=5, ping_timeout=2)
        await self.sender_loop()
    
    def send_message(self, message: str):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = self.loop

        asyncio.run_coroutine_threadsafe(
            self.antrian_pesan.put(message),
            loop
        )

#flask API
class CommandAPI:
    def __init__(self, websocket_server: WebSocketServer, host='0.0.0.0', port=5000):
        self.websocket_server = websocket_server
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route("/api/trigger", methods=["POST"])
        def trigger():
            if not request.is_json:
                return jsonify({"status": "error", "message": "Invalid content type"}), 400

            data = request.get_json()
            command = data.get("command")
            target = data.get("target", "all")

            if command is None:
                return jsonify({"status": "error", "message": "command field harus di isi."}), 400
            
            if command == 1:
                actual_command = "ON"
            elif command == 0:
                actual_command = "OFF"
            else:
                return jsonify({"status": "error", "message": "Command harus terdiri dari 1 dan 0 (integer)."}), 400

            message = actual_command
            self.websocket_server.send_message(message)

            return jsonify({
                "status": "success",
                "message": "Command sent",
                "sent": {
                    "target": target,
                    "command": actual_command
                }
            })
        
        @self.app.route("/api/status", methods=["GET"])
        def status():
            esp_connected = len(self.websocket_server.connected_clients)>0
            if esp_connected > 0 :
                status = True
            else :
                status = False
            return jsonify({
                "esp_status": status
            })
    def run(self):
        print(f"[Flask] API Dijalankan di http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

# Jalankan wsapi
class ServerApp:
    def __init__(self):
        self.websocket_server = WebSocketServer()
        self.api = CommandAPI(self.websocket_server)

    def start(self):
        threading.Thread(target=self.api.run, daemon=True).start()
        asyncio.run(self.websocket_server.run())

if __name__ == "__main__":
    app = ServerApp()
    app.start()