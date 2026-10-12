import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def run():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        url_local = f"http://localhost:{PORT}/index.html"
        url_lan = f"http://192.168.0.63:{PORT}/index.html"
        print(f"==================================================")
        print(f" Paltro-SD01 Git Operations Command Center")
        print(f" Workstation Local URL: {url_local}")
        print(f" LAN Network / Mobile:  {url_lan}")
        print(f" Press Ctrl+C to stop the server.")
        print(f"==================================================")
        webbrowser.open(url_local)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    run()
