CARTA Python Frontend/Backend Interface
---------------------------------------

A simple Python library for communicating with the CARTA backend using the protocol buffer messages defined in the frontend/backend ICD and found in `carta-protobuf`. Under construction. Intended for simple interactive tests; may be useful for automated testing.

(Not to be confused with `carta-python`, which is a wrapper for scripting CARTA by communicating with the frontend via a gRPC interface in the backend.)

You can install this by running `pip install .` (with an appropriate version of `pip`) in the top-level directory (after checking out the `carta-protobuf` submodule). This will automatically generate and install the protocol buffer message objects in the `cartaicdproto` module, in addition to the simple client in `cartaicd`.

Example scripts go in `examples`.
