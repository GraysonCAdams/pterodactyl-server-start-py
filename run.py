import a2s
import os
import socket
import datetime
import json
import sys
import requests
import logging
import threading
import time
import http.server
import socketserver

PTERODACTYL_URL = os.environ.get("PTERODACTYL_URL")
PTERODACTYL_API_KEY = os.environ.get("PTERODACTYL_API_KEY")
PTERODACTYL_SERVER_ID = os.environ.get("PTERODACTYL_SERVER_ID")
IDLE_MINUTES_SHUTOFF = int(os.environ.get("IDLE_MINUTES_SHUTOFF", 15))

server_online = False
last_active = datetime.datetime.now()

def start_server():
    logging.info("Starting server!")
    r = requests.post(  
        f"{PTERODACTYL_URL}/api/client/servers/{PTERODACTYL_SERVER_ID}/power",
        headers={
            "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json={
            "signal": "start"
        }
    )
    if r.status_code != 204:
        raise Exception()

def stop_server():
    logging.warning("Stopping server!")
    r = requests.post(  
        f"{PTERODACTYL_URL}/api/client/servers/{PTERODACTYL_SERVER_ID}/power",
        headers={
            "Authorization": f"Bearer {PTERODACTYL_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        json={
            "signal": "stop"
        }
    )

def refresh():
    while True:
        logging.info("Refreshing server info...")

        address = (
            os.environ.get("SERVER_ADDRESS", "n1-atl-pterodactyl.graysons.network"),
            int(os.environ.get("SERVER_PORT", "2457"))
        )

        global last_active
        global server_online

        players = []
        try:
            players = a2s.players(address, timeout=2)
            server_online = True
            logging.info("Server is online")
        except socket.timeout:
            logging.warning("Failed to get players, server offline")
            server_online = False
            last_active = datetime.datetime.now()

        if len(players) > 0:
            last_active = datetime.datetime.now()
            logging.info("There are players online")

        if last_active < datetime.datetime.now() - datetime.timedelta(minutes=IDLE_MINUTES_SHUTOFF):
            try:
                stop_server()
            except Exception as e:
                logging.critical("Failed to stop server.")
                logging.critical(str(e))
        
        time.sleep(5)

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_my_headers()
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def send_my_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

    def do_GET(self):

        if self.path == '/':
            self.path = 'index.html'
        elif self.path == '/start':
            if server_online:
                self.path = 'running.html'
            else:
                try:
                    start_server()
                    self.path = 'start.html'
                except Exception as e:
                    logging.critical("Failed to start server!")
                    logging.critical(str(e))
                    self.path = 'error.html'

        return http.server.SimpleHTTPRequestHandler.do_GET(self)

if __name__ == "__main__":
    format = "[%(levelname)s] %(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")

    x = threading.Thread(target=refresh, args=())
    x.start()

    handler_object = MyHttpRequestHandler

    PORT = 8000
    http_server = socketserver.TCPServer(("", PORT), handler_object)
    http_server.serve_forever()