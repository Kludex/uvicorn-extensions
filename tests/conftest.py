import asyncio

import pytest
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


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
