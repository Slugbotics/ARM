import config
import requests
import socket
import http.server
import webbrowser
from urllib.parse import urlparse, parse_qs, quote_plus
import threading
from irc import *

code = None

print("Twitch main run!!!")

def run_irc():
    print("Requesting token...")
    res = requests.post("https://id.twitch.tv/oauth2/token",
                  data={
                      "client_id": config.CLIENT_ID,
                      "client_secret": config.CLIENT_SECRET,
                      "code": code,
                      "grant_type": "authorization_code",
                      "redirect_uri": "http://localhost:3000"
                  })

    print("res.json(): " + str(res.json()))

    access_token = res.json()["access_token"]

    print("Connecting to chat...")
    irc_client = IRCClient("irc.chat.twitch.tv")
    irc_client.send(IRCMessage("CAP", ["REQ", "twitch.tv/membership twitch.tv/tags twitch.tv/commands"]))
    irc_client.send(IRCMessage("PASS", ["oauth:" + access_token]))
    irc_client.send(IRCMessage("NICK", ["thearmteam"]))
    irc_client.send(IRCMessage("JOIN", ["#ucscarm"]))
    # irc_client.send(IRCMessage("JOIN", ["#ucscarm"]))
    print("Connected.")
    while(True):
        message = irc_client.recv()
        if message.command == "PRIVMSG":
            print(message.tags["display-name"] + ": " + message.params[1])
        elif message.command == "PING":
            irc_client.send(IRCMessage("PONG", message.params))
        else:
            print(message)

class RequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global code
        qs = urlparse(self.path).query
        code_param = parse_qs(qs).get("code")
        if code_param is not None and len(code_param) == 1:
            code = code_param[0]
            threading.Thread(target=run_irc).start()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><script>window.close();</script></body></html>")

    def log_message(self, format: str, *args) -> None:
        pass

print("Starting HTTP server...")
http_server = http.server.HTTPServer(("localhost", 3000), RequestHandler)

webbrowser.open("https://id.twitch.tv/oauth2/authorize?client_id="
                + config.CLIENT_ID + "&redirect_uri=http://localhost:3000&response_type=code&scope=" + quote_plus("chat:read chat:edit"))

print("Waiting for client auth...")
http_server.serve_forever()
