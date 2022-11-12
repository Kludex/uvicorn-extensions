from __future__ import annotations

import asyncio
import logging
import urllib.parse
from typing import Callable, cast

import httptools
from asgi_types import (
    ASGISendEvent,
    HTTPResponseStartEvent,
    HTTPResponseTrailersEvent,
    HTTPScope,
)
from uvicorn.config import Config
from uvicorn.protocols.http.flow_control import (
    CLOSE_HEADER,
    FlowControl,
    service_unavailable,
)
from uvicorn.protocols.http.httptools_impl import (
    HEADER_RE,
    HEADER_VALUE_RE,
    STATUS_LINE,
    HttpToolsProtocol,
)
from uvicorn.protocols.http.httptools_impl import (
    RequestResponseCycle as _RequestResponseCycle,
)
from uvicorn.protocols.utils import get_client_addr, get_path_with_query_string
from uvicorn.server import ServerState


class HTTPProtocol(HttpToolsProtocol):
    def __init__(
        self,
        config: Config,
        server_state: ServerState,
        _loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        super().__init__(config, server_state, _loop)
        self.expect_trailers = False

    def on_message_begin(self) -> None:
        self.url = b""
        self.expect_100_continue = False
        self.headers = []
        self.scope = {
            "type": "http",
            "asgi": {"version": self.config.asgi_version, "spec_version": "2.3"},
            "http_version": "1.1",
            "server": self.server,
            "client": self.client,
            "scheme": self.scheme,
            "root_path": self.root_path,
            "headers": self.headers,
            "extensions": {"http.response.trailers": {}},
        }

    def on_header(self, name: bytes, value: bytes) -> None:
        name = name.lower()
        if name == b"expect" and value.lower() == b"100-continue":
            self.expect_100_continue = True
        if name == b"te" and b"trailers" in [
            v.strip() for v in value.lower().split(b",")
        ]:
            self.expect_trailers = True
        self.headers.append((name, value))

    def on_headers_complete(self) -> None:
        http_version = self.parser.get_http_version()
        method = self.parser.get_method()
        self.scope["method"] = method.decode("ascii")
        if http_version != "1.1":
            self.scope["http_version"] = http_version
        if self.parser.should_upgrade() and self._should_upgrade():
            return
        parsed_url = httptools.parse_url(self.url)
        raw_path = parsed_url.path
        path = raw_path.decode("ascii")
        if "%" in path:
            path = urllib.parse.unquote(path)
        self.scope["path"] = path
        self.scope["raw_path"] = raw_path
        self.scope["query_string"] = parsed_url.query or b""

        # Handle 503 responses when 'limit_concurrency' is exceeded.
        if self.limit_concurrency is not None and (
            len(self.connections) >= self.limit_concurrency
            or len(self.tasks) >= self.limit_concurrency
        ):
            app = service_unavailable
            message = "Exceeded concurrency limit."
            self.logger.warning(message)
        else:
            app = self.app

        existing_cycle = self.cycle
        self.cycle = RequestResponseCycle(
            scope=self.scope,
            transport=self.transport,
            flow=self.flow,
            logger=self.logger,
            access_logger=self.access_logger,
            access_log=self.access_log,
            default_headers=self.server_state.default_headers,
            message_event=asyncio.Event(),
            expect_100_continue=self.expect_100_continue,
            expect_trailers=self.expect_trailers,
            keep_alive=http_version != "1.0",
            on_response=self.on_response_complete,
        )
        if existing_cycle is None or existing_cycle.response_complete:
            # Standard case - start processing the request.
            task = self.loop.create_task(self.cycle.run_asgi(app))
            task.add_done_callback(self.tasks.discard)
            self.tasks.add(task)
        else:
            # Pipelined HTTP requests need to be queued up.
            self.flow.pause_reading()
            self.pipeline.appendleft((self.cycle, app))


class RequestResponseCycle(_RequestResponseCycle):
    def __init__(
        self,
        scope: HTTPScope,
        transport: asyncio.Transport,
        flow: FlowControl,
        logger: logging.Logger,
        access_logger: logging.Logger,
        access_log: bool,
        default_headers: list[tuple[bytes, bytes]],
        message_event: asyncio.Event,
        expect_100_continue: bool,
        expect_trailers: bool,
        keep_alive: bool,
        on_response: Callable[..., None],
    ) -> None:
        super().__init__(
            scope,
            transport,
            flow,
            logger,
            access_logger,
            access_log,
            default_headers,
            message_event,
            expect_100_continue,
            keep_alive,
            on_response,
        )
        self.expect_trailers = expect_trailers
        self.send_trailers = False

    async def send(self, message: ASGISendEvent) -> None:
        message_type = message["type"]

        if self.flow.write_paused and not self.disconnected:
            await self.flow.drain()  # pragma: to be covered

        if self.disconnected:
            return  # pragma: to be covered

        if not self.response_started:
            # Sending response status line and headers
            if message_type != "http.response.start":
                msg = "Expected ASGI message 'http.response.start', but got '%s'."
                raise RuntimeError(msg % message_type)
            message = cast(HTTPResponseStartEvent, message)

            self.response_started = True
            self.waiting_for_100_continue = False

            status_code = message["status"]
            headers = self.default_headers + list(message.get("headers", []))

            self.send_trailers = (
                message.get("trailers", False) and self.scope["method"] != "HEAD"
            )

            if CLOSE_HEADER in self.scope["headers"] and CLOSE_HEADER not in headers:
                headers = headers + [CLOSE_HEADER]  # pragma: to be covered

            if self.access_log:
                self.access_logger.info(
                    '%s - "%s %s HTTP/%s" %d',
                    get_client_addr(self.scope),
                    self.scope["method"],
                    get_path_with_query_string(self.scope),
                    self.scope["http_version"],
                    status_code,
                )

            # Write response status line and headers
            content = [STATUS_LINE[status_code]]

            for name, value in headers:
                if HEADER_RE.search(name):  # pragma: to be covered
                    raise RuntimeError("Invalid HTTP header name.")
                if HEADER_VALUE_RE.search(value):  # pragma: to be covered
                    raise RuntimeError("Invalid HTTP header value.")

                name = name.lower()
                if name == b"content-length" and self.chunked_encoding is None:
                    self.expected_content_length = int(value.decode())
                    self.chunked_encoding = False
                elif name == b"transfer-encoding" and value.lower() == b"chunked":
                    self.expected_content_length = 0
                    self.chunked_encoding = True
                elif name == b"connection" and value.lower() == b"close":
                    self.keep_alive = False
                content.extend([name, b": ", value, b"\r\n"])

            if (
                self.chunked_encoding is None
                and self.scope["method"] != "HEAD"
                and status_code not in (204, 304)
            ):
                # Neither content-length nor transfer-encoding specified
                self.chunked_encoding = True
                content.append(b"transfer-encoding: chunked\r\n")

            content.append(b"\r\n")
            self.transport.write(b"".join(content))

        elif not self.response_complete:
            # Sending response body
            if message_type != "http.response.body":
                msg = "Expected ASGI message 'http.response.body', but got '%s'."
                raise RuntimeError(msg % message_type)

            body = cast(bytes, message.get("body", b""))
            more_body = message.get("more_body", False)

            # Write response body
            if self.scope["method"] == "HEAD":
                self.expected_content_length = 0
            elif self.chunked_encoding:
                if body:
                    content = [b"%x\r\n" % len(body), body, b"\r\n"]
                else:
                    content = []
                if not more_body:
                    content.append(b"0\r\n\r\n")
                self.transport.write(b"".join(content))
            else:
                num_bytes = len(body)
                if num_bytes > self.expected_content_length:
                    raise RuntimeError("Response content longer than Content-Length")
                else:
                    self.expected_content_length -= num_bytes
                self.transport.write(body)

            # Handle response completion
            if not more_body:
                if self.expected_content_length != 0:
                    raise RuntimeError("Response content shorter than Content-Length")
                self.response_complete = True
                self.message_event.set()

                if not self.send_trailers:
                    if not self.keep_alive:
                        self.transport.close()
                    self.on_response()

        elif self.send_trailers:
            if message_type != "http.response.trailers":  # pragma: to be covered
                msg = "Expected ASGI message 'http.response.trailers', but got '%s'."
                raise RuntimeError(msg % message_type)
            message = cast("HTTPResponseTrailersEvent", message)

            trailers = list(message.get("headers", []))
            more_trailers = message.get("more_trailers", False)
            content = []

            for name, value in trailers:
                if HEADER_RE.search(name):  # pragma: to be covered
                    raise RuntimeError("Invalid HTTP header name.")
                if HEADER_VALUE_RE.search(value):  # pragma: to be covered
                    raise RuntimeError("Invalid HTTP header value.")

                name = name.lower()
                if name == b"connection" and value.lower() == b"close":
                    self.keep_alive = False  # pragma: to be covered
                content.extend([name, b": ", value, b"\r\n"])

            if not more_trailers:
                content.append(b"\r\n")

            # Server should only send if the client sent a TE header.
            if self.expect_trailers:
                self.transport.write(b"".join(content))

            if not more_trailers:
                self.send_trailers = False
                if not self.keep_alive:
                    self.transport.close()  # pragma: to be covered
                self.on_response()

        else:
            # Response already sent
            msg = "Unexpected ASGI message '%s' sent, after response already completed."
            raise RuntimeError(msg % message_type)
