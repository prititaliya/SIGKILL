import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from engine.llama_client import LlamaClient

HOST = "127.0.0.1"
PORT = 8081
MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "/Users/jatin/Models/qwen2.5-coder-3b-instruct-q2_k.gguf")

client = None

class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True

class DaemonHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return  # Suppress HTTP access logging

    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/step":
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            
            try:
                body = json.loads(raw_body)
            except Exception:
                self.send_response(400)
                self.end_headers()
                return

            messages = body.get("messages", [])
            res = client.step(messages) if messages else {"status": "ok"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))

        elif self.path == "/unload":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Unloaded")
            os._exit(0)
        else:
            self.send_response(404)
            self.end_headers()

def main():
    global client
    client = LlamaClient(model_path=MODEL_PATH)
    server = ReuseHTTPServer((HOST, PORT), DaemonHandler)
    server.serve_forever()

if __name__ == "__main__":
    main()