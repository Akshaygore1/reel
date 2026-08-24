#!/usr/bin/env python3
"""
Lightweight Gallery Server for @buildebugship System Design Reels.
Serves static gallery files and provides the /api/delete endpoint for live file deletion.
"""
import os
import sys
import json
import http.server
import socketserver
import urllib.parse
from engine.build_gallery import build_gallery_html, WORKSPACE_DIR, OUTPUT_DIR

PORT = 8000

class GalleryRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WORKSPACE_DIR, **kwargs)

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        if parsed_url.path == "/api/delete":
            self.handle_delete()
        else:
            self.send_error(404, "Endpoint not found")

    def handle_delete(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body) if body else {}
            filename = data.get("filename", "").strip()

            if not filename or ".." in filename or "/" in filename or "\\" in filename:
                self.send_json({"success": False, "error": "Invalid filename parameter"}, status=400)
                return

            if not filename.endswith(".mp4"):
                self.send_json({"success": False, "error": "Only .mp4 files can be deleted"}, status=400)
                return

            mp4_path = os.path.join(OUTPUT_DIR, filename)
            txt_path = os.path.join(OUTPUT_DIR, filename.replace(".mp4", ".txt"))

            deleted_files = []
            if os.path.exists(mp4_path):
                os.remove(mp4_path)
                deleted_files.append(filename)

            if os.path.exists(txt_path):
                os.remove(txt_path)
                deleted_files.append(os.path.basename(txt_path))

            # Re-generate gallery HTML to keep everything in sync
            build_gallery_html()

            remaining_videos = len([f for f in os.listdir(OUTPUT_DIR) if f.endswith(".mp4")])

            self.send_json({
                "success": True,
                "deleted": deleted_files,
                "remaining": remaining_videos,
                "message": f"Successfully deleted {filename}"
            })
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, status=500)

    def send_json(self, data, status=200):
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def run_server(port=PORT):
    # Ensure gallery is up to date when server starts
    build_gallery_html()
    
    # Allow address reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), GalleryRequestHandler) as httpd:
        print(f"\n🎬 ========================================================")
        print(f"🚀 Video Gallery Server running at: http://localhost:{port}")
        print(f"📂 Serving workspace: {WORKSPACE_DIR}")
        print(f"🗑️ Deletion API enabled at: http://localhost:{port}/api/delete")
        print(f"Press Ctrl+C to stop the server.")
        print(f"==========================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")

if __name__ == "__main__":
    port = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
