#!/usr/bin/env python3
import http.server
import socketserver
import os

# Change to frontend directory
os.chdir('/Users/leowang/github/Krio_music/local-music-generator/frontend')

PORT = 8080
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    print(f"Access the application at: http://localhost:{PORT}/")
    httpd.serve_forever()