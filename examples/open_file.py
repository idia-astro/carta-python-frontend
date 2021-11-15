#!/usr/bin/env python3

# Usage example: open the specified file. 

import os
import sys

from cartaicd.client import Client
import cartaicdproto as cp
    
# Create the client -- this automatically connects and registers with the backend
client = Client("localhost", 3002, report_icd_version) # TODO: parse ICD version dynamically out of the protobuf docs

ack = client.received_history[-1]
if "Invalid ICD version number" in ack.message:
    sys.exit(ack.message)

file_path = sys.argv[1]
file_dir, file_name = os.path.split(file_path)

# You have to construct the message objects yourself, but don't worry about the event headers -- the client will add them automatically.
client.send(cp.open_file.OpenFile(
    file=file_name, 
    directory=file_dir, 
    file_id=1
))

client.receive()

last = client.received_history[-1]

print(last)
