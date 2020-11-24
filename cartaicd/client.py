import asyncio
import re
import struct
import uuid
import threading
import queue

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

ICD_VERSION = 17
HEADER = struct.Struct('HHI')

class Client:
    def __init__(self, host, port):
        self.url = f"ws://{host}:{port}/websocket"
        self.send_queue = queue.Queue()
        self._stop = False

        # TODO handle matching replies
        asyncio.get_event_loop().run_until_complete(self.connect(self.url))
        asyncio.get_event_loop().run_until_complete(self.register())
        
        t = threading.Thread(target=asyncio.get_event_loop().run_until_complete, args=(asyncio.gather(self.listen(), self.send_messages()),))
        t.start()
        
    async def connect(self, url):
        self.socket = await websockets.connect(url, ping_interval=None)
        
    async def register(self):
        message = cp.register_viewer.RegisterViewer()
        message.session_id = np.uint32(uuid.uuid4().int % np.iinfo(np.uint32()).max) # why?
        
        await self.send_(message)
        data = await self.socket.recv()
        
        reply = self.unpack(data)
        print("RECEIVED", reply)
                
    async def send_(self, message):
        print("SENDING", message)
        await self.socket.send(self.pack(message))
        
    def send(self, message):
        self.send_queue.put(message)
                
    async def listen(self):
        while not self._stop:
            data = await self.socket.recv()
            message = self.unpack(data)
            print("RECEIVED", message)
            
    async def send_messages(self):
        while not self._stop:
            try:
                message = self.send_queue.get()
                await self.send_(message)
            except queue.Empty:
                pass
            await asyncio.sleep(10)
    
    def stop(self):
        self._stop = True
        
    def pack(self, message):
        try:
            event_type = MSG_CLASS_TO_EVENT_TYPE[message.__class__]
        except KeyError:
            raise ValueError(f"{message.__class__.__name__} is not a valid event class.")
        
        header = HEADER.pack(event_type, ICD_VERSION, uuid.uuid4().int % np.iinfo(np.uint32()).max) # why? session_id?
        
        return header + message.SerializeToString()
        
    def unpack(self, data):
        event_type, icd_version, message_id = HEADER.unpack(data[:8])
        try:
            event_class = EVENT_TYPE_TO_MSG_CLASS[event_type]
        except KeyError:
            raise ValueError(f"{event_type} is not a valid event type.")
        
        message = event_class()
        message.ParseFromString(data[8:])
        
        return message
        
        
