#!/usr/bin/env python3

# Usage example: testing changes to the spatial profile implementation. This requires ICD version > 18.0. To change the version, check out the appropriate version of the carta-protobuf submodule, and reinstall this module with pip. That will automatically regenerate the protocol buffer code.

import os
import argparse
import sys
import time

from cartaicd.client import Client
import cartaicdproto as cp
import numpy as np
from astropy.io import fits
import h5py

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

# Here we fetch the reference data from the image. The test is being run against a local backend, so the same path is used here and passed to the backend.
file_path = args.image
mipmap_data = None

def downsampled(v):
    return int(np.ceil(v / args.mip))

if file_path.endswith(".fits"):
    hdu_list = fits.open(file_path)
    image_data = hdu_list[0].data
elif file_path.endswith(".hdf5"):
    with h5py.File(file_path, "r") as f:
        image_data = f["0/DATA"][:] # make a copy to force read
        try:
            mipmap_data = f[f"0/MipMaps/DATA/DATA_XY_{args.mip}"][:]
        except KeyError:
            pass # no mipmaps

image_profile = {}
image_profile["x"] = image_data[args.y]
image_profile["y"] = image_data[:, args.x]

if mipmap_data is not None:
    image_profile["mm_x"] = mipmap_data[downsampled(args.y)]
    image_profile["mm_y"] = mipmap_data[:, downsampled(args.x)]
    
# Create the client -- this automatically connects and registers with the backend
client = Client("localhost", 3002, 18)

ack = client.received_history[-1]
if "Invalid ICD version number" in ack.message:
    sys.exit(ack.message)

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

for p in last.profiles:
    print("Coordinate", p.coordinate, "Bounds", p.start, p.end, "Mip", p.mip)
    got = np.fromstring(p.raw_values_fp32, dtype=np.float32)
    if p.mip < 2:
        expected = image_profile[p.coordinate][p.start:p.end]
    else:
        try:
            expected = image_profile[f"mm_{p.coordinate}"][downsampled(p.start):downsampled(p.end)]
        except KeyError:
            sys.exit("Something weird happened; we received a downsampled profile but there are no mipmaps in the file.")
        
    if not np.array_equal(got, expected):
        print("Got", len(got), "values:\n", got)
        print("Expected", len(expected), "values:\n", expected)
        if len(got) == len(expected):
            diff = expected - got
            print(np.count_nonzero(diff), "/", len(diff), "values differ:\n", diff)
    else:
        print("Expected values match.")
