import asyncio
import re
import struct
import uuid

import numpy as np
import websockets

import cartaicdproto as cp
from google.protobuf.pyext.cpp_message import GeneratedProtocolMessageType

MSG_CLASS_TO_EVENT_TYPE = {}
EVENT_TYPE_TO_MSG_CLASS = {}

for cp_key, cp_val in cp.__dict__.items():
    if cp_key.endswith("_pb2") and cp_key not in ("enums_pb2", "defs_pb2"):
        for key, val in cp_val.__dict__.items():
            if isinstance(val, GeneratedProtocolMessageType):
                event_name = re.sub('([a-z])([A-Z])', r'\1_\2', key).upper()
                event_type = getattr(cp.enums.EventType, event_name, None)
                if event_type is not None:
                    MSG_CLASS_TO_EVENT_TYPE[val] = event_type
                    EVENT_TYPE_TO_MSG_CLASS[event_type] = val

class Client:
    def __init__(self, host, port, icd_version):
        self.url = f"ws://{host}:{port}/websocket"
        self.icd_version = icd_version
        self.sent_history = []
        self.received_history = []

        asyncio.get_event_loop().run_until_complete(self.connect(self.url))
        asyncio.get_event_loop().run_until_complete(self.register())
        
    async def connect(self, url):
        self.socket = await websockets.connect(url, ping_interval=None)
        
    async def register(self):
        message = cp.register_viewer.RegisterViewer()
        message.session_id = np.uint32(uuid.uuid4().int % np.iinfo(np.uint32()).max) # why?
        
        await self.send_(message)
        self.sent_history.append(message)
        data = await self.socket.recv()
        
        reply = self.unpack(data)
        print("RECEIVED", reply.__class__.__name__)
        self.received_history.append(reply)
                
    async def send_(self, message):
        print("SENDING", message.__class__.__name__)
        await self.socket.send(self.pack(message))
        self.sent_history.append(message)
        
    def send(self, message):
        asyncio.get_event_loop().run_until_complete(self.send_(message))
                
    async def receive_(self):
        messages = []
        
        while True:
            try:
                data = await asyncio.wait_for(self.socket.recv(), timeout=1)
                message = self.unpack(data)
                print("RECEIVED", message.__class__.__name__)
                messages.append(message)
                await asyncio.sleep(1)
            except asyncio.TimeoutError:
                break
        
        self.received_history.extend(messages)
        return messages
            
    def receive(self):
        return asyncio.get_event_loop().run_until_complete(self.receive_())
        
    def pack(self, message):
        try:
            event_type = MSG_CLASS_TO_EVENT_TYPE[message.__class__]
        except KeyError:
            raise ValueError(f"{message.__class__.__name__} is not a valid event class.")
        
        header = struct.Struct('HHI').pack(event_type, self.icd_version, uuid.uuid4().int % np.iinfo(np.uint32()).max)
        
        return header + message.SerializeToString()
        
    def unpack(self, data):
        event_type, icd_version, message_id = struct.Struct('HHI').unpack(data[:8])
        try:
            event_class = EVENT_TYPE_TO_MSG_CLASS[event_type]
        except KeyError:
            raise ValueError(f"{event_type} is not a valid event type.")
        
        message = event_class()
        message.ParseFromString(data[8:])
        
        return message
    
    def clear(self):
        self.sent_history = []
        self.received_history = []
