import asyncio

import pytest
import uvicorn_trailers


@pytest.fixture(scope="session", params=[uvicorn_trailers.HttpToolsProtocol])
def http_protocol(request) -> asyncio.Protocol:
    return request.param


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
