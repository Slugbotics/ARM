from collections import deque
import threading
from functools import partial
from typing import Callable
import cv2

import sys
import http.server
import webbrowser
from urllib.parse import urlparse, parse_qs, quote_plus
import threading
import traceback
import Modules.twitch.irc    
import requests

from Modules.Base.TextIn import TextIn

class TwitchChat(TextIn):  
    
    def __init__(self, twitch_client_id: str, twitch_secret: str) -> None:
        self.keep_running = False
        self.irc_client = None
        self.http_server = None
        self.message_queue = deque()
        
        self.code = None
        self.process_msg_fnc = None

        self.twitch_client_id = twitch_client_id
        self.twitch_secret = twitch_secret
    
    # read a line from the twitch chat
    # will return None if no message is available, or else the oldest message stored.
    def read_line(self) -> str:
        if len(self.message_queue) == 0:
            return None
        return self.message_queue.popleft()

    def stop_twitch_chat(self) -> None:

        self.keep_running = False
        if self.irc_client is not None:
            self.irc_client.close()
            
        if self.http_server is not None:
            # http_server.shutdown()
            self.http_server.socket.close()
            self.http_server.server_close()
        else:
            print("Not shutting down http server, no reference <---------------------")

    def connect_to_twitch(self, channel_name: str, process_msg_fnc: Callable[[str], None] = None) -> None:
        self.process_msg_fnc = process_msg_fnc
        self.channel_name = channel_name
        self.keep_running = True
        self.thread = threading.Thread(target=self.host_login_prompt)
        self.thread.daemon = True  # Mark the thread as a daemon
        self.thread.start()

    def run_irc(self, _) -> None:
        print("Requesting token...")
        res = requests.post("https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": self.twitch_client_id,
                    "client_secret": self.twitch_secret,
                    "code": self.code,
                    "grant_type": "authorization_code",
                    "redirect_uri": "http://localhost:3000"
                })

        print("res.json(): " + str(res.json()))

        access_token = res.json()["access_token"]

        print("Connecting to chat...")
        self.irc_client = Modules.twitch.irc.IRCClient("irc.chat.twitch.tv")
        self.irc_client.send(Modules.twitch.irc.IRCMessage("CAP", ["REQ", "twitch.tv/membership twitch.tv/tags twitch.tv/commands"]))
        self.irc_client.send(Modules.twitch.irc.IRCMessage("PASS", ["oauth:" + access_token]))
        self.irc_client.send(Modules.twitch.irc.IRCMessage("NICK", ["thearmteam"]))
        self.irc_client.send(Modules.twitch.irc.IRCMessage("JOIN", ["#" + self.channel_name]))
        print("Connected.")
        while(self.keep_running):
            try:
                message = self.irc_client.recv()
                if message.command == "PING":
                    self.irc_client.send(Modules.twitch.irc.IRCMessage("PONG", message.params))
                elif message.command == "PRIVMSG":
                    self.message_queue.append(message.params[1])
                    if self.process_msg_fnc is not None:
                        self.process_msg_fnc(message.params[1])
                    print(message.params[1])
                else:
                    # print("Twitich recived some other message: \"" + str(message) + "\"")
                    pass
            except Exception as e:
                print("Exception in run_irc: " + str(e))
                traceback.print_exc()
                break
        print("twitch_chat_keep_running exited!!!")

    class RequestHandler(http.server.BaseHTTPRequestHandler):
        
        def __init__(self, *args, source_self, run_irc, set_code, twitch_client_id, **kwargs) -> None:
            self.source_self = source_self
            self.run_irc = run_irc
            self.set_code = set_code
            self.twitch_client_id = twitch_client_id
            super().__init__(*args, **kwargs)            
            
        def do_GET(self) -> None:
            qs = urlparse(self.path).query
            code_param = parse_qs(qs).get("code")
            if code_param is not None and len(code_param) == 1:
                code = code_param[0]
                self.set_code(self.source_self, code)
                threading.Thread(target=self.run_irc, args=(self.source_self,)).start()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><script>window.close();</script></body></html>")

        def log_message(self, format: str, *args) -> None:
            pass

    def set_code(_, self, code: str) -> None:
        self.code = code

    def host_login_prompt(self) -> None:

        self.code = None           

        print("Starting HTTP server...")
        # Create a partial function to include the extra argument
        handler_with_arg = partial(self.RequestHandler, source_self=self, run_irc=self.run_irc, set_code=self.set_code, twitch_client_id=self.twitch_client_id)
        self.timeout = 1
        self.http_server = http.server.HTTPServer(("localhost", 3000), handler_with_arg)
        self.http_server.timeout = 1  # Set a timeout for the server's socket

        webbrowser.open("https://id.twitch.tv/oauth2/authorize?client_id="
                        + self.twitch_client_id + "&redirect_uri=http://localhost:3000&response_type=code&scope=" + quote_plus("chat:read chat:edit"))

        print("Waiting for client auth.")
        # self.http_server.serve_forever()
        while self.keep_running:
            self.http_server.handle_request()  # Handle one request at a time
            print("handeling one request")

        print("EXITING MAIN TWITCH THREAD!!! <-------------------------")
