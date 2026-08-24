#!/usr/bin/env python3
"""
Root entrypoint for running the Reels Video Gallery local server.
Usage:
  python3 server.py        # Starts server on http://localhost:8000
  python3 server.py 8080   # Starts server on custom port
"""
import sys
from engine.server import run_server, PORT

if __name__ == "__main__":
    port = PORT
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
