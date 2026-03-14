import http.server
import socketserver
import json
import os
import subprocess
import sys
from urllib.parse import urlparse, parse_qs
import threading

# Agregar el directorio pipeline al path
sys.path.insert(0, os.path.dirname(__file__))
from validator import run_validations, get_changed_modules

PORT = 8888
ADDONS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "addons"))

class PilotHandler(http.server.SimpleHTTPRequestHandler):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(__file__), "static"), **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/modules":
            self.handle_modules()
        elif parsed.path == "/api/validate":
            params = parse_qs(parsed.query)
            modules = params.get("modules", [None])[0]
            self.handle_validate(modules)
        else:
            super().do_GET()
    
    def handle_modules(self):
        """Retorna lista de módulos disponibles"""
        try:
            modules = [
                d for d in os.listdir(ADDONS_PATH)
                if os.path.isdir(os.path.join(ADDONS_PATH, d))
            ]
            self.send_json({"modules": modules, "addons_path": ADDONS_PATH})
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def handle_validate(self, modules_param):
        """Corre validaciones y retorna resultados"""
        try:
            if modules_param and modules_param != "all":
                modules = modules_param.split(",")
            else:
                modules = [
                    d for d in os.listdir(ADDONS_PATH)
                    if os.path.isdir(os.path.join(ADDONS_PATH, d))
                ]
            
            results = run_validations(ADDONS_PATH, modules)
            
            total = len(results)
            ok = sum(1 for v in results.values() if v["ok"])
            
            self.send_json({
                "results": results,
                "summary": {
                    "total": total,
                    "ok": ok,
                    "failed": total - ok,
                    "passed": total == ok
                }
            })
        except Exception as e:
            self.send_json({"error": str(e)}, 500)
    
    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, format, *args):
        pass  # Silencia logs del servidor

def run():
    with socketserver.TCPServer(("", PORT), PilotHandler) as httpd:
        print(f"")
        print(f"  OdooCodePilot UI corriendo en http://localhost:{PORT}")
        print(f"  Ctrl+C para detener")
        print(f"")
        httpd.serve_forever()

if __name__ == "__main__":
    run()