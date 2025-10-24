#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import subprocess
import threading
import argparse
import json

HOST = "0.0.0.0"
PORT = 8080

class SoundPlayer():

    def __init__(self):
        sounds = {}
        with open('soundboard.json') as f:
            self.sounds = json.load(f)

    def play_sound(self, sound_name):
        filename = self.sounds[sound_name]['file']
        monitor_sink = self.get_monitor()
        app_sinks = self.get_app_sink()
        t2 = None
        t1 = threading.Thread(target=self.play_on_sink, args=(monitor_sink, 1.0, filename,))
        for sink in app_sinks:
            print("playing on", sink['properties']['application.name'])
            sink_index = str(sink['index'])
            t2 = threading.Thread(target=self.play_on_sink, args=(sink_index, 0.1, filename,))
            t2.start()
        t1.start()
        t1.join()
        if t2:
            t2.join()

    def get_app_sink(self):
        result =  subprocess.run(['pactl', '--format=json', 'list', 'source-outputs'], capture_output=True, text=True)
        data = json.loads(result.stdout)
        return data

    def get_monitor(self):
        result =  subprocess.run(['pactl', 'get-default-sink'], capture_output=True, text=True)
        return result.stdout

    def stop_sounds(self):
        subprocess.run(["killall", "pw-play"])

    def play_on_sink(self, target, volume, filename):
        subprocess.run(["pw-play", "--volume", str(volume), "--target", target, filename])

class CommandHandler(BaseHTTPRequestHandler):

    soundPlayer = SoundPlayer()

    def do_GET(self):
        # Parse the URL and query
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        cmd = query.get("play", [None])[0]

        if cmd:
            try:
                self.respond(200)
                self.soundPlayer.play_sound(cmd)
            except Exception as e:
                self.respond(404, f"No entry for {cmd}")
        else:
            self.respond(204)

    def respond(self, code, body=""):
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(body.encode())

def run():
    print(f"Serving on http://{HOST}:{PORT}")
    server = HTTPServer((HOST, PORT), CommandHandler)
    server.serve_forever()

if __name__ == "__main__":
    run()
