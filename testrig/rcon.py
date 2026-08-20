"""Minimal Source RCON client. No dependencies.

Minecraft answers a command with the same text a console operator would see, so
this is a synchronous request/response channel into a running server.
"""
import socket
import struct

SERVERDATA_AUTH = 3
SERVERDATA_EXECCOMMAND = 2
SERVERDATA_RESPONSE_VALUE = 0


class RconError(Exception):
    pass


class Rcon:
    def __init__(self, host="127.0.0.1", port=25575, password="lcwiki", timeout=600.0):
        self.addr = (host, port)
        self.password = password
        self.timeout = timeout
        self.sock = None
        self._id = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()

    def connect(self) -> None:
        self.sock = socket.create_connection(self.addr, timeout=self.timeout)
        self.sock.settimeout(self.timeout)
        rid = self._send(SERVERDATA_AUTH, self.password)
        # The server replies to an auth packet twice; the id is -1 on failure.
        while True:
            pid, ptype, _ = self._recv()
            if ptype == 2 or pid == -1:
                break
        if pid == -1:
            raise RconError("rcon auth rejected")
        assert pid == rid

    def close(self) -> None:
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None

    def command(self, text: str) -> str:
        """Run one command and return the server's reply as plain text."""
        self._send(SERVERDATA_EXECCOMMAND, text)
        body = ""
        # A long reply arrives split across packets. An empty trailing packet
        # is how the server signals it is done.
        while True:
            _, _, chunk = self._recv()
            body += chunk
            if len(chunk) < 4000:
                break
        return body.strip()

    def _send(self, ptype: int, body: str) -> int:
        self._id += 1
        payload = struct.pack("<ii", self._id, ptype) + body.encode("utf8") + b"\x00\x00"
        self.sock.sendall(struct.pack("<i", len(payload)) + payload)
        return self._id

    def _recv(self):
        raw = self._read_exact(4)
        (length,) = struct.unpack("<i", raw)
        payload = self._read_exact(length)
        pid, ptype = struct.unpack("<ii", payload[:8])
        return pid, ptype, payload[8:-2].decode("utf8", "replace")

    def _read_exact(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise RconError("rcon connection closed")
            buf += chunk
        return buf
