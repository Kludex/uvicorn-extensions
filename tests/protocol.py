from uvicorn.config import Config
from uvicorn.server import ServerState


class MockTransport:
    def __init__(self, sockname=None, peername=None, sslcontext=False):
        self.sockname = ("127.0.0.1", 8000) if sockname is None else sockname
        self.peername = ("127.0.0.1", 8001) if peername is None else peername
        self.sslcontext = sslcontext
        self.closed = False
        self.buffer = b""
        self.read_paused = False

    def get_extra_info(self, key):
        return {
            "sockname": self.sockname,
            "peername": self.peername,
            "sslcontext": self.sslcontext,
        }.get(key)

    def write(self, data):
        assert not self.closed
        self.buffer += data

    def close(self):
        assert not self.closed
        self.closed = True

    def pause_reading(self):
        self.read_paused = True

    def resume_reading(self):
        self.read_paused = False

    def is_closing(self):
        return self.closed

    def clear_buffer(self):
        self.buffer = b""

    def set_protocol(self, protocol):
        pass


class MockLoop:
    def __init__(self):
        self._tasks = []
        self._later = []

    def create_task(self, coroutine):
        self._tasks.insert(0, coroutine)
        return MockTask()

    def call_later(self, delay, callback, *args):
        self._later.insert(0, (delay, callback, args))

    async def run_one(self):
        return await self._tasks.pop()

    def run_later(self, with_delay):
        later = []
        for delay, callback, args in self._later:
            if with_delay >= delay:
                callback(*args)
            else:
                later.append((delay, callback, args))
        self._later = later


class MockTask:
    def add_done_callback(self, callback):
        pass


def get_connected_protocol(app, protocol_cls, **kwargs):
    loop = MockLoop()
    transport = MockTransport()
    config = Config(app=app, **kwargs)
    server_state = ServerState()
    protocol = protocol_cls(config=config, server_state=server_state, _loop=loop)
    protocol.connection_made(transport)
    return protocol
