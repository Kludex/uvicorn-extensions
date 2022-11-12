import logging
import socket
import threading
import time

import pytest
from uvicorn.config import WS_PROTOCOLS, Config
from uvicorn.protocols.http.h11_impl import H11Protocol
from uvicorn.protocols.http.httptools_impl import HttpToolsProtocol
from uvicorn.server import Server

from tests.constants import (
    FINISH_POST_REQUEST,
    GET_REQUEST_HUGE_HEADERS,
    GET_REQUEST_WITH_RAW_PATH,
    HTTP10_GET_REQUEST,
    INVALID_REQUEST_TEMPLATE,
    LARGE_POST_REQUEST,
    SIMPLE_GET_REQUEST,
    SIMPLE_HEAD_REQUEST,
    SIMPLE_POST_REQUEST,
    START_POST_REQUEST,
    UPGRADE_HTTP2_REQUEST,
    UPGRADE_REQUEST,
)
from tests.protocol import get_connected_protocol
from tests.response import Response

WEBSOCKET_PROTOCOLS = WS_PROTOCOLS.keys()


@pytest.mark.anyio
async def test_get_request(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer


@pytest.mark.skip(reason="Issue with capture logs fixture.")
@pytest.mark.anyio
@pytest.mark.parametrize("path", ["/", "/?foo", "/?foo=bar", "/?foo=bar&baz=1"])
async def test_request_logging(path, http_protocol, caplog):  # pragma: no cover
    get_request_with_query_string = b"\r\n".join(
        ["GET {} HTTP/1.1".format(path).encode("ascii"), b"Host: example.org", b"", b""]
    )
    caplog.set_level(logging.INFO, logger="uvicorn.access")
    logging.getLogger("uvicorn.access").propagate = True

    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol, log_config=None)
    protocol.data_received(get_request_with_query_string)
    await protocol.loop.run_one()
    assert '"GET {} HTTP/1.1" 200'.format(path) in caplog.records[0].message


@pytest.mark.anyio
async def test_head_request(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_HEAD_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" not in protocol.transport.buffer


@pytest.mark.anyio
async def test_post_request(http_protocol):
    async def app(scope, receive, send):
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
        response = Response(b"Body: " + body, media_type="text/plain")
        await response(scope, receive, send)

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_POST_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b'Body: {"hello": "world"}' in protocol.transport.buffer


@pytest.mark.anyio
async def test_keepalive(http_protocol):
    app = Response(b"", status_code=204)

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()

    assert b"HTTP/1.1 204 No Content" in protocol.transport.buffer
    assert not protocol.transport.is_closing()


@pytest.mark.anyio
async def test_keepalive_timeout(http_protocol):
    app = Response(b"", status_code=204)

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 204 No Content" in protocol.transport.buffer
    assert not protocol.transport.is_closing()
    protocol.loop.run_later(with_delay=1)
    assert not protocol.transport.is_closing()
    protocol.loop.run_later(with_delay=5)
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_close(http_protocol):
    app = Response(b"", status_code=204, headers={"connection": "close"})

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 204 No Content" in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_chunked_encoding(http_protocol):
    app = Response(
        b"Hello, world!", status_code=200, headers={"transfer-encoding": "chunked"}
    )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"0\r\n\r\n" in protocol.transport.buffer
    assert not protocol.transport.is_closing()


@pytest.mark.anyio
async def test_chunked_encoding_empty_body(http_protocol):
    app = Response(
        b"Hello, world!", status_code=200, headers={"transfer-encoding": "chunked"}
    )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert protocol.transport.buffer.count(b"0\r\n\r\n") == 1
    assert not protocol.transport.is_closing()


@pytest.mark.anyio
async def test_chunked_encoding_head_request(http_protocol):
    app = Response(
        b"Hello, world!", status_code=200, headers={"transfer-encoding": "chunked"}
    )

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_HEAD_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert not protocol.transport.is_closing()


@pytest.mark.anyio
async def test_pipelined_requests(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    protocol.data_received(SIMPLE_GET_REQUEST)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
    protocol.transport.clear_buffer()
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
    protocol.transport.clear_buffer()
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
    protocol.transport.clear_buffer()


@pytest.mark.anyio
async def test_undersized_request(http_protocol):
    app = Response(b"xxx", headers={"content-length": "10"})

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_oversized_request(http_protocol):
    app = Response(b"xxx" * 20, headers={"content-length": "10"})

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_large_post_request(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(LARGE_POST_REQUEST)
    assert protocol.transport.read_paused
    await protocol.loop.run_one()
    assert not protocol.transport.read_paused


@pytest.mark.anyio
async def test_invalid_http(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(b"x" * 100000)
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_app_exception(http_protocol):
    async def app(scope, receive, send):
        raise Exception()

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 500 Internal Server Error" in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_exception_during_response(http_protocol):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b"1", "more_body": True})
        raise Exception()

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 500 Internal Server Error" not in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_no_response_returned(http_protocol):
    async def app(scope, receive, send):
        pass

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 500 Internal Server Error" in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_partial_response_returned(http_protocol):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 500 Internal Server Error" not in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_duplicate_start_message(http_protocol):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.start", "status": 200})

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 500 Internal Server Error" not in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_missing_start_message(http_protocol):
    async def app(scope, receive, send):
        await send({"type": "http.response.body", "body": b""})

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 500 Internal Server Error" in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_message_after_body_complete(http_protocol):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b""})
        await send({"type": "http.response.body", "body": b""})

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_value_returned(http_protocol):
    async def app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200})
        await send({"type": "http.response.body", "body": b""})
        return 123

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_early_disconnect(http_protocol):
    got_disconnect_event = False

    async def app(scope, receive, send):
        nonlocal got_disconnect_event

        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                break

        got_disconnect_event = True

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_POST_REQUEST)
    protocol.eof_received()
    protocol.connection_lost(None)
    await protocol.loop.run_one()
    assert got_disconnect_event


@pytest.mark.anyio
async def test_early_response(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(START_POST_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    protocol.data_received(FINISH_POST_REQUEST)
    assert not protocol.transport.is_closing()


@pytest.mark.anyio
async def test_read_after_response(http_protocol):
    message_after_response = None

    async def app(scope, receive, send):
        nonlocal message_after_response

        response = Response("Hello, world", media_type="text/plain")
        await response(scope, receive, send)
        message_after_response = await receive()

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_POST_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert message_after_response == {"type": "http.disconnect"}


@pytest.mark.anyio
async def test_http10_request(http_protocol):
    async def app(scope, receive, send):
        content = "Version: %s" % scope["http_version"]
        response = Response(content, media_type="text/plain")
        await response(scope, receive, send)

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(HTTP10_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Version: 1.0" in protocol.transport.buffer


@pytest.mark.anyio
async def test_root_path(http_protocol):
    async def app(scope, receive, send):
        path = scope.get("root_path", "") + scope["path"]
        response = Response("Path: " + path, media_type="text/plain")
        await response(scope, receive, send)

    protocol = get_connected_protocol(app, http_protocol, root_path="/app")
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Path: /app/" in protocol.transport.buffer


@pytest.mark.anyio
async def test_raw_path(http_protocol):
    async def app(scope, receive, send):
        path = scope["path"]
        raw_path = scope.get("raw_path", None)
        assert "/one/two" == path
        assert b"/one%2Ftwo" == raw_path

        response = Response("Done", media_type="text/plain")
        await response(scope, receive, send)

    protocol = get_connected_protocol(app, http_protocol, root_path="/app")
    protocol.data_received(GET_REQUEST_WITH_RAW_PATH)
    await protocol.loop.run_one()
    assert b"Done" in protocol.transport.buffer


@pytest.mark.anyio
async def test_max_concurrency(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol, limit_concurrency=1)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 503 Service Unavailable" in protocol.transport.buffer


@pytest.mark.anyio
async def test_shutdown_during_request(http_protocol):
    app = Response(b"", status_code=204)

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    protocol.shutdown()
    await protocol.loop.run_one()
    assert b"HTTP/1.1 204 No Content" in protocol.transport.buffer
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_shutdown_during_idle(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.shutdown()
    assert protocol.transport.buffer == b""
    assert protocol.transport.is_closing()


@pytest.mark.anyio
async def test_100_continue_sent_when_body_consumed(http_protocol):
    async def app(scope, receive, send):
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)
        response = Response(b"Body: " + body, media_type="text/plain")
        await response(scope, receive, send)

    protocol = get_connected_protocol(app, http_protocol)
    EXPECT_100_REQUEST = b"\r\n".join(
        [
            b"POST / HTTP/1.1",
            b"Host: example.org",
            b"Expect: 100-continue",
            b"Content-Type: application/json",
            b"Content-Length: 18",
            b"",
            b'{"hello": "world"}',
        ]
    )
    protocol.data_received(EXPECT_100_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 100 Continue" in protocol.transport.buffer
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b'Body: {"hello": "world"}' in protocol.transport.buffer


@pytest.mark.anyio
async def test_100_continue_not_sent_when_body_not_consumed(http_protocol):
    app = Response(b"", status_code=204)

    protocol = get_connected_protocol(app, http_protocol)
    EXPECT_100_REQUEST = b"\r\n".join(
        [
            b"POST / HTTP/1.1",
            b"Host: example.org",
            b"Expect: 100-continue",
            b"Content-Type: application/json",
            b"Content-Length: 18",
            b"",
            b'{"hello": "world"}',
        ]
    )
    protocol.data_received(EXPECT_100_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 100 Continue" not in protocol.transport.buffer
    assert b"HTTP/1.1 204 No Content" in protocol.transport.buffer


@pytest.mark.anyio
async def test_supported_upgrade_request(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol, ws="wsproto")
    protocol.data_received(UPGRADE_REQUEST)
    assert b"HTTP/1.1 426 " in protocol.transport.buffer


@pytest.mark.anyio
async def test_unsupported_ws_upgrade_request(http_protocol):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol, ws="none")
    protocol.data_received(UPGRADE_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer


@pytest.mark.skip(reason="Issue with capture logs fixture.")
@pytest.mark.anyio
async def test_unsupported_ws_upgrade_request_warn_on_auto(
    caplog: pytest.LogCaptureFixture, http_protocol
):  # pragma: no cover
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol, ws="auto")
    protocol.ws_protocol_class = None
    protocol.data_received(UPGRADE_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
    warnings = [
        record.msg
        for record in filter(
            lambda record: record.levelname == "WARNING", caplog.records
        )
    ]
    assert "Unsupported upgrade request." in warnings
    msg = "No supported WebSocket library detected. Please use 'pip install uvicorn[standard]', or install 'websockets' or 'wsproto' manually."  # noqa: E501
    assert msg in warnings


@pytest.mark.anyio
@pytest.mark.parametrize("ws", WEBSOCKET_PROTOCOLS)
async def test_http2_upgrade_request(http_protocol, ws):
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(UPGRADE_HTTP2_REQUEST)
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer


async def asgi3app(scope, receive, send):
    pass


def asgi2app(scope):
    async def asgi(receive, send):
        pass

    return asgi


asgi_scope_data = [
    (asgi3app, {"version": "3.0", "spec_version": "2.3"}),
    (asgi2app, {"version": "2.0", "spec_version": "2.3"}),
]


@pytest.mark.anyio
@pytest.mark.parametrize("asgi2or3_app, expected_scopes", asgi_scope_data)
async def test_scopes(asgi2or3_app, expected_scopes, http_protocol):
    protocol = get_connected_protocol(asgi2or3_app, http_protocol)
    protocol.data_received(SIMPLE_GET_REQUEST)
    await protocol.loop.run_one()
    assert expected_scopes == protocol.scope.get("asgi")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "request_line",
    [
        pytest.param(b"G?T / HTTP/1.1", id="invalid-method"),
        pytest.param(b"GET /?x=y z HTTP/1.1", id="invalid-path"),
        pytest.param(b"GET / HTTP1.1", id="invalid-http-version"),
    ],
)
async def test_invalid_http_request(request_line, http_protocol, caplog):
    app = Response("Hello, world", media_type="text/plain")
    request = INVALID_REQUEST_TEMPLATE % request_line

    caplog.set_level(logging.INFO, logger="uvicorn.error")
    logging.getLogger("uvicorn.error").propagate = True

    protocol = get_connected_protocol(app, http_protocol)
    protocol.data_received(request)
    assert b"HTTP/1.1 400 Bad Request" in protocol.transport.buffer
    assert b"Invalid HTTP request received." in protocol.transport.buffer


def test_fragmentation(http_protocol):
    if not issubclass(http_protocol, HttpToolsProtocol):
        pytest.skip("HTTP class is not httptools based.")  # pragma: no cover

    def receive_all(sock):
        chunks = []
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)

    app = Response("Hello, world", media_type="text/plain")

    def send_fragmented_req(path):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 8000))
        d = (
            f"GET {path} HTTP/1.1\r\n" "Host: localhost\r\n" "Connection: close\r\n\r\n"
        ).encode()
        split = len(path) // 2
        sock.sendall(d[:split])
        time.sleep(0.01)
        sock.sendall(d[split:])
        resp = receive_all(sock)
        # see https://github.com/kmonsoor/py-amqplib/issues/45
        # we skip the error on bsd systems if python is too slow
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except Exception:  # pragma: no cover
            pass
        sock.close()
        return resp

    config = Config(app=app, http="httptools")
    server = Server(config=config)
    t = threading.Thread(target=server.run)
    t.daemon = True
    t.start()
    time.sleep(1)  # wait for uvicorn to start

    path = "/?param=" + "q" * 10
    response = send_fragmented_req(path)
    bad_response = b"HTTP/1.1 400 Bad Request"
    assert bad_response != response[: len(bad_response)]
    server.should_exit = True
    t.join()


@pytest.mark.anyio
async def test_huge_headers_h11protocol_failure():
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, H11Protocol)
    # Huge headers make h11 fail in it's default config
    # h11 sends back a 400 in this case
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[0])
    assert b"HTTP/1.1 400 Bad Request" in protocol.transport.buffer
    assert b"Connection: close" in protocol.transport.buffer
    assert b"Invalid HTTP request received." in protocol.transport.buffer


@pytest.mark.anyio
async def test_huge_headers_httptools_will_pass(http_protocol):
    if not issubclass(http_protocol, HttpToolsProtocol):
        pytest.skip("HTTP class is not httptools based.")  # pragma: no cover
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, http_protocol)
    # Huge headers make h11 fail in it's default config
    # httptools protocol will always pass
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[0])
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[1])
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer


@pytest.mark.anyio
async def test_huge_headers_h11protocol_failure_with_setting():
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(
        app, H11Protocol, h11_max_incomplete_event_size=20 * 1024
    )
    # Huge headers make h11 fail in it's default config
    # h11 sends back a 400 in this case
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[0])
    assert b"HTTP/1.1 400 Bad Request" in protocol.transport.buffer
    assert b"Connection: close" in protocol.transport.buffer
    assert b"Invalid HTTP request received." in protocol.transport.buffer


@pytest.mark.anyio
async def test_huge_headers_httptools(http_protocol):
    if not issubclass(http_protocol, HttpToolsProtocol):
        pytest.skip("HTTP class is not httptools based.")  # pragma: no cover
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(app, HttpToolsProtocol)
    # Huge headers make h11 fail in it's default config
    # httptools protocol will always pass
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[0])
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[1])
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer


@pytest.mark.anyio
async def test_huge_headers_h11_max_incomplete(http_protocol):  # pragma: no cover
    if not issubclass(http_protocol, H11Protocol):
        pytest.skip("HTTP class is not h11 based.")
    app = Response("Hello, world", media_type="text/plain")

    protocol = get_connected_protocol(
        app, http_protocol, h11_max_incomplete_event_size=64 * 1024
    )
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[0])
    protocol.data_received(GET_REQUEST_HUGE_HEADERS[1])
    await protocol.loop.run_one()
    assert b"HTTP/1.1 200 OK" in protocol.transport.buffer
    assert b"Hello, world" in protocol.transport.buffer
