import asyncio
import json
import websockets
import websockets.exceptions
import websockets.server

class WebsocketServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.loop = None
        self.client_map = {}
        self.antrianPesan = asyncio.Queue()

    async def handler(self, websocket, path):
        try:
            rawData = await websocket.recv() 
            data = json.loads(rawData)
            esp_id = data.get("id")
            esp_type = data.get("type", "generic")

            if not esp_id:
                await websocket.close()
                return

            print(f"[WS] Terhubung: {esp_id} ({esp_type}) dari {websocket.remote_address}")
            self.client_map[esp_id] = {
                "type": esp_type,
                "ws": websocket
            }

            async for msg in websocket:
                print(f"[WS] [{esp_id}] → {msg}")

        except websockets.exceptions.ConnectionClosed:
            print(f"[WS] ESP Terputus: {esp_id}")
        finally:
            if esp_id in self.client_map:
                del self.client_map[esp_id]

    async def sender_loop(self):
        while True:
            target_id, pesan = await self.antrianPesan.get()
            client = self.client_map.get(target_id)
            if client and client["ws"].open:
                try:
                    await client["ws"].send(pesan)
                    print(f"[WS] Instruksi ke {target_id}: {pesan}")
                except Exception as e:
                    print(f"[WS] Gagal kirim ke {target_id}: {e}")
            else:
                print(f"[WS] Target {target_id} tidak terhubung")

    async def run(self):
        self.loop = asyncio.get_running_loop()
        print(f"[WS] Server berjalan di ws://{self.host}:{self.port}")
        await websockets.serve(self.handler, self.host, self.port, ping_interval=5, ping_timeout=2)
        await self.sender_loop()

    def KirimPesan(self, target_id: str, pesan: str):
        asyncio.run_coroutine_threadsafe(
            self.antrianPesan.put((target_id, pesan)),
            self.loop
        )

    def getStatus(self):
        return {
            esp_id: {
                "type": info["type"],
                "connected": info["ws"].open
            }
            for esp_id, info in self.client_map.items()
        }
