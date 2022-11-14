<!-- There's a synchronization between `docs/package/asgi-trailers.md` and `src/python/asgi-trailers/README.md` -->
# ASGI Trailers

The `asgi-trailers` package implements a **[StreamingResponse]** that supports **[HTTP Trailers]**.

## Installation

```bash
pip install asgi-trailers
```

## Usage

The most common use case is to use the `StreamingResponse` as a drop-in replacement
for **Starlette**'s `StreamingResponse`.

It's also possible to use as a **standalone ASGI application**.

```py title="main.py"
import asyncio
import time
from contextvars import ContextVar

import asgi_trailers import StreamingResponse
from starlette.applications import Starlette

started_time: ContextVar[float] = ContextVar("started_time")


async def slow_numbers(numbers) -> str:
    yield('<html><body><ul>')
    for number in range(numbers):
        yield '<li>%d</li>' % number
        await asyncio.sleep(0.5)
    yield('</ul></body></html>')


async def trailers():
    start = started_time.get()
    elapsed = time.time() - start
    yield 'server-timing', f'total;dur={elapsed:.3f}'


async def app(scope, receive, send):
    assert scope['type'] == 'http'
    started_time.set(time.time())
    generator = slow_numbers(10)
    response = StreamingResponse(
        generator,
        headers={"trailers": "server-timing"},
        trailers=trailers,
    )
    await response(scope, receive, send)
```

On this example, the [`server-timing`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Server-Timing)
trailer will be sent after the **_response body_ is sent**.

## License

This project is licensed under the terms of the MIT license.

[StreamingResponse]: https://www.starlette.io/responses/#streamingresponse
[HTTP Trailers]: https://asgi.readthedocs.io/en/latest/extensions.html#http-trailers
