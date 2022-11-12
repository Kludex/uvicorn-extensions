import asyncio

import pytest
import uvicorn_extended
import uvicorn_trailers


@pytest.fixture(
    scope="session",
    params=[uvicorn_trailers.HTTPProtocol, uvicorn_extended.HTTPProtocol],
)
def http_protocol(request) -> asyncio.Protocol:
    return request.param


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
