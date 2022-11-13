import asyncio

import pytest
import uvicorn_extended
import uvicorn_trailers

from tests.constants import SIMPLE_GET_REQUEST
from tests.protocol import get_connected_protocol

EXPECT_TRAILERS_REQUEST = b"\r\n".join(
    [b"GET / HTTP/1.1", b"Host: example.org", b"TE: trailers", b"", b""]
)

EXPECT_TRAILERS_HEAD_REQUEST = b"\r\n".join(
    [b"HEAD / HTTP/1.1", b"Host: example.org", b"TE: trailers", b"", b""]
)


@pytest.fixture(
    scope="module",
    params=[uvicorn_trailers.HTTPProtocol, uvicorn_extended.HTTPProtocol],
)
def http_protocol(request) -> asyncio.Protocol:
    return request.param


@pytest.mark.anyio
@pytest.mark.parametrize(
    "headers",
    [
        [],
        [(b"trailers", b"x-trailer-test")],
        [(b"transfer-encoding", b"chunked"), (b"trailers", b"x-trailer-test")],
    ],
)
async def test_request_with_trailers(headers, http_protocol: asyncio.Protocol) -> None:
    async def app(scope, receive, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": headers,
                "trailers": True,
            }
        )
        await send(
            {"type": "http.response.body", "body": b"Hello, world!", "more_body": False}
        )
        await send(
            {
                "type": "http.response.trailers",
                "headers": [(b"x-trailer-test", b"test")],
                "more_trailers": False,
            }
        )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(EXPECT_TRAILERS_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
    assert b"x-trailer-test: test" in protocol.transport.buffer


@pytest.mark.anyio
async def test_request_without_te_headers(http_protocol: asyncio.Protocol):
    async def app(scope, receive, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"transfer-encoding", b"chunked"),
                    (b"trailers", b"x-trailer-test"),
                ],
                "trailers": True,
            }
        )
        await send(
            {"type": "http.response.body", "body": b"Hello, world!", "more_body": False}
        )
        await send(
            {
                "type": "http.response.trailers",
                "headers": [(b"x-trailer-test", b"test")],
                "more_trailers": False,
            }
        )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
    assert b"x-trailer-test: test" not in protocol.transport.buffer


@pytest.mark.anyio
async def test_multiple_trailers(http_protocol: asyncio.Protocol):
    async def app(scope, receive, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"transfer-encoding", b"chunked"),
                    (b"trailers", b"x-trailer-test"),
                    (b"trailers", b"x-trailer-test2"),
                ],
                "trailers": True,
            }
        )
        await send(
            {"type": "http.response.body", "body": b"Hello, world!", "more_body": False}
        )
        await send(
            {
                "type": "http.response.trailers",
                "headers": [(b"x-trailer-test", b"test")],
                "more_trailers": True,
            }
        )
        await send(
            {
                "type": "http.response.trailers",
                "headers": [(b"x-trailer-test2", b"test2")],
                "more_trailers": False,
            }
        )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(EXPECT_TRAILERS_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
    assert b"x-trailer-test: test" in protocol.transport.buffer
    assert b"x-trailer-test2: test2" in protocol.transport.buffer


@pytest.mark.anyio
async def test_trailer_before_body_complete(http_protocol):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "trailers": True})
        await send({"type": "http.response.body", "body": b"", "more_body": True})
        await send(
            {
                "type": "http.response.trailers",
                "trailers": [(b"x-trailer-test", b"test")],
            }
        )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(EXPECT_TRAILERS_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"x-trailer-test" not in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_head_request_with_trailers(http_protocol):
    async def app(scope, receive, send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"transfer-encoding", b"chunked"),
                    (b"trailers", b"x-trailer-test"),
                ],
                "trailers": True,
            }
        )
        await send(
            {"type": "http.response.body", "body": b"Hello, world!", "more_body": False}
        )
        await send(
            {
                "type": "http.response.trailers",
                "headers": [(b"x-trailer-test", b"test")],
                "more_trailers": False,
            }
        )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(EXPECT_TRAILERS_HEAD_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" not in protocol.transport.buffer
    assert b"x-trailer-test: test" not in protocol.transport.buffer
