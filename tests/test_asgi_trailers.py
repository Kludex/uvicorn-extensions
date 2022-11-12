from __future__ import annotations

from typing import AsyncIterator, Iterator

import anyio
import pytest
from asgi_trailers import StreamingResponse


def iterator() -> Iterator[tuple[str, str]]:
    yield "x-trailer-test", "value"
    yield "x-trailer-test2", "value2"


async def async_iterator() -> AsyncIterator[tuple[str, str]]:
    yield "x-trailer-test", "value"
    yield "x-trailer-test2", "value2"


@pytest.mark.anyio
@pytest.mark.parametrize("trailers", [iterator, async_iterator])
async def test_streaming_response(trailers):
    messages: list[dict] = []
    sleep_forever = anyio.Event()

    async def send(message):
        messages.append(message)

    async def receive():
        await sleep_forever.wait()

    response = StreamingResponse(content=iter(()), trailers=trailers())

    await response({"extensions": {"http.response.trailers": {}}}, receive, send)

    http_response_start = messages.pop(0).items()
    assert ("type", "http.response.start") in http_response_start
    assert ("trailers", True) in http_response_start

    http_response_body = messages.pop(0).items()
    assert ("type", "http.response.body") in http_response_body
    assert ("more_body", False) in http_response_body

    http_response_trailers = messages.pop(0).items()
    assert ("type", "http.response.trailers") in http_response_trailers
    assert ("more_trailers", True) in http_response_trailers
    assert ("headers", [(b"x-trailer-test", b"value")]) in http_response_trailers

    http_response_trailers = messages.pop(0).items()
    assert ("type", "http.response.trailers") in http_response_trailers
    assert ("more_trailers", True) in http_response_trailers
    assert ("headers", [(b"x-trailer-test2", b"value2")]) in http_response_trailers

    http_response_trailers = messages.pop(0).items()
    assert ("type", "http.response.trailers") in http_response_trailers
    assert ("more_trailers", False) in http_response_trailers
    assert ("headers", []) in http_response_trailers


@pytest.mark.anyio
async def test_streaming_response_without_trailers():
    messages: list[dict] = []
    sleep_forever = anyio.Event()

    async def send(message):
        messages.append(message)

    async def receive():
        await sleep_forever.wait()

    response = StreamingResponse(content=iter(()))

    await response({"extensions": {"http.response.trailers": {}}}, receive, send)

    http_response_start = messages.pop(0).items()
    assert ("type", "http.response.start") in http_response_start
    assert ("trailers", False) in http_response_start

    http_response_body = messages.pop(0).items()
    assert ("type", "http.response.body") in http_response_body
    assert ("more_body", False) in http_response_body

    assert not messages
