#!/usr/bin/env python3

# Usage example: requesting spatial profiles

import os
import argparse
import sys

from cartaicd.client import Client
import cartaicdproto as cp

parser = argparse.ArgumentParser(description='Test spatial profiles.')
parser.add_argument('image', help='path to image file')
parser.add_argument('x', type=int, help='Cursor X position')
parser.add_argument('y', type=int, help='Cursor Y position')
parser.add_argument('--x-start', type=int, default=0, help='X profile start index (inclusive)')
parser.add_argument('--x-end', type=int, default=0, help='X profile end index (exclusive)')
parser.add_argument('--y-start', type=int, default=0, help='Y profile start index (inclusive)')
parser.add_argument('--y-end', type=int, default=0, help='Y profile end index (exclusive)')
parser.add_argument('--mip', type=int, default=0, help='Mip (used for both profiles)')

args = parser.parse_args()
    
# Create the client -- this automatically connects and registers with the backend
client = Client("localhost", 3002, 24) # TODO: parse ICD version dynamically out of the protobuf docs

ack = client.received_history[-1]
if "Invalid ICD version number" in ack.message:
    sys.exit(ack.message)
    
file_path = args.image
file_dir, file_name = os.path.split(file_path)

# You have to construct the message objects yourself, but don't worry about the event headers -- the client will add them automatically.
client.send(cp.open_file.OpenFile(
    file=file_name, 
    directory=file_dir, 
    file_id=1
))

client.send(cp.region_requirements.SetSpatialRequirements(
    file_id=1, 
    region_id=0, 
    spatial_profiles=(
        cp.region_requirements.SetSpatialRequirements.SpatialConfig(coordinate="x", start=args.x_start, end=args.x_end, mip=args.mip),
        cp.region_requirements.SetSpatialRequirements.SpatialConfig(coordinate="y", start=args.y_start, end=args.y_end, mip=args.mip)
    )
))

client.send(cp.set_cursor.SetCursor(
    file_id=1, 
    point=cp.defs.Point(
        x=args.x, 
        y=args.y
    )
))

# If the backend is slow, for example because you're running it in valgrind, put a sleep here before you check for messages.
# No concurrent listening for streamed messages from the backend is implemented.

client.receive()

last = client.received_history[-1]

print(last.profiles)

