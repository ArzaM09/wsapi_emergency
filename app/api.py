from flask import Flask, request, jsonify

class PerintahAPI:
    def __init__(self, websocket_server, host='0.0.0.0', port=9091):
        self.websocket_server = websocket_server
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.SetupRoutes()

    def SetupRoutes(self):
        @self.app.route("/api/trigger", methods=["POST"])
        def checking_emergency():
            data = request.get_json()
            command = data.get("command")
            target = data.get("target")

            if not target or command is None:
                return jsonify({"Error" : "Tidak ada request target atau command"}),400
            
            client_info = self.websocket_server.client_map.get(target)
            if not client_info:
                return jsonify({"Error":f"ESP {target} Diluar Jangkauan"}),404

            esp_type = client_info.get("type")
            if esp_type == "Emergency":
                pesan = str(command)
            
            if pesan == "CEK" or pesan == "cek" :
                self.websocket_server.KirimPesan(target, pesan)
            else :
                return jsonify({"Error" : "Command Salah"}),400

            return jsonify({
                "status": "success",
                "target": target,
                "esp_type": esp_type,
                "sent_command": pesan
            })
        
        def trigger():
            data = request.get_json()
            target = data.get("target")
            command = data.get("command")

            if not target or command is None:
                return jsonify({"Error" : "Tidak ada request target atau command"}), 400
            client_info = self.websocket_server.client_map.get(target)

            if not client_info:
                return jsonify({"Error":f"ESP {target} Diluar Jangkauan"}),404
            esp_type = client_info.get("type")

            if esp_type == "Emergency":
                pesan = "E:"+str(command)
            elif esp_type == "Locater":
                pesan = "L"+str(command)
            else:
                pesan = str(command) 
             
            self.websocket_server.KirimPesan(target, pesan)

            return jsonify({
                "status": "success",
                "target": target,
                "esp_type": esp_type,
                "sent_command": pesan
            })
        @self.app.route("/api/status", methods=["POST"])
        def status():
            data = request.get_json()
            requested_type = data.get("type")

            result = []
            for esp_id, info in self.websocket_server.client_map.items():
                esp_type = info.get("type", "unknown")
                if requested_type and esp_type.lower() == requested_type.lower() and info["ws"].open:
                    result.append({
                        "Nama": esp_id,
                        "type": esp_type,
                        "connected": True
                    })

            if not result:
                return jsonify({
                    "status": False,
                    "message": f"Tidak ada ESP aktif dengan tipe '{requested_type}'"
                })

            return jsonify({
                "status": True,
                "found": len(result),
                "clients": result
            })
    def run(self):
        print(f"[Flask] API running on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)