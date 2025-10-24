#!/usr/bin/env python3
import subprocess
import argparse
import json
import os

def get_app_sink():
    result =  subprocess.run(['pactl', '--format=json', 'list', 'source-outputs'], capture_output=True, text=True)
    data = json.loads(result.stdout)
    return data

def get_monitor():
    result =  subprocess.run(['pactl', 'get-default-sink'], capture_output=True, text=True)
    return result.stdout

def stop_sounds():
    subprocess.run(["killall", "pw-play"])

def play_on_sink(target, volume, filename):
    return subprocess.Popen(["pw-play", "--volume", str(volume), "--target", target, filename])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plays sound to all app sinks', )
    parser.add_argument('filename', nargs='?', help='The file to play')
    parser.add_argument('--stop', action='store_true', help='Stop all sounds')
    parser.add_argument('--local_vol', type=int, metavar='FLOAT', help='Volume of local sound')
    parser.add_argument('--remote_vol', type=int, metavar='FLOAT', help='Volume of remote sound')
    parser.add_argument('--json', type=int, metavar='INT', help='JSON integer value')
    args = parser.parse_args()
    if args.stop:
        stop_sounds()
        exit()
    if args.json is not None:
        with open('/home/rory/Music/sound_board/sound_board.json', 'r') as file:
            data = json.load(file)[args.json-1]
            if 'file' in data: args.filename = data['file']
            else: exit()
            if 'local_vol' in data: args.local_vol = data['local_vol']
            elif args.local_vol is None: args.local_vol =1.0
            if 'remote_vol' in data: args.remote_vol = data['remote_vol']
            elif args.remote_vol is None: args.remote_vol = 0.1
    elif args.filename is None:
        parser.error("the following arguments are required: filename")
        if args.local_vol is None: args.local_vol =1.0
        if args.remote_vol is None: args.remote_vol = 0.1

    monitor_sink = get_monitor()
    app_sinks = get_app_sink()
    children = []
    monitor = play_on_sink(monitor_sink, args.local_vol, args.filename)
    children.append(monitor.pid)
    for sink in app_sinks:
        print("playing on", sink['properties']['application.name'])
        sink_index = str(sink['index'])
        children.append(play_on_sink(sink_index, args.remote_vol, args.filename).pid)
    monitor.wait()

