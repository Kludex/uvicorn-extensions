import asyncio
import contextlib
import socket

import pytest
import uvicorn_denial
import uvicorn_extended
import uvicorn_httparse
import uvicorn_trailers
from uvicorn.config import LOGGING_CONFIG

# See: https://github.com/encode/uvicorn/blob/6496e6c1e3647c852bf993f7d62f2c65f9a8c2f5/tests/conftest.py#LL18-L26C61  # noqa: E501
LOGGING_CONFIG["loggers"]["uvicorn"]["propagate"] = True


@pytest.fixture(
    scope="session",
    params=[
        uvicorn_trailers.HTTPProtocol,
        uvicorn_extended.HTTPProtocol,
        uvicorn_httparse.HttparseProtocol,
    ],
)
def http_protocol(request) -> asyncio.Protocol:
    return request.param


@pytest.fixture(scope="session", params=[uvicorn_denial.WSProtocol])
def ws_protocol(request) -> asyncio.Protocol:
    return request.param


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _unused_port(socket_type: int) -> int:
    """Find an unused localhost port from 1024-65535 and return it."""
    with contextlib.closing(socket.socket(type=socket_type)) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# Copied from pytest-asyncio
# Ref.: https://github.com/pytest-dev/pytest-asyncio/blob/d6a9a72ef1749a864e64ac6222a8d0da99e67de5/pytest_asyncio/plugin.py#L516-L525  # noqa: E501
@pytest.fixture
def unused_tcp_port() -> int:
    return _unused_port(socket.SOCK_STREAM)
