import pytest
from uvicorn_httparse import HttparseProtocol

from tests.constants import GET_REQUEST_HUGE_HEADERS
from tests.protocol import get_connected_protocol
from tests.response import Response


@pytest.mark.anyio
async def test_huge_headers_httparse():
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, HttparseProtocol)
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[0])
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[1])
    protocol.eof_received()
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
