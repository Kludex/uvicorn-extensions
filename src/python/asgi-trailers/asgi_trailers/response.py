from __future__ import annotations

from functools import partial
from typing import AsyncIterable, Awaitable, Callable, Iterable, Mapping, Tuple, Union

import anyio
from starlette.background import BackgroundTask
from starlette.concurrency import iterate_in_threadpool
from starlette.responses import ContentStream
from starlette.responses import StreamingResponse as _StreamingResponse
from starlette.types import Receive, Scope, Send

Trailers = Tuple[str, str]
SyncTrailersStream = Iterable[Trailers]
AsyncTrailersStream = AsyncIterable[Trailers]
TrailersStream = Union[SyncTrailersStream, AsyncTrailersStream]


class StreamingResponse(_StreamingResponse):
    def __init__(
        self,
        content: ContentStream,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
        *,
        trailers: TrailersStream | None = None,
    ) -> None:
        super().__init__(content, status_code, headers, media_type, background)
        if trailers is None:
            self.trailers_iterator = None
        elif isinstance(trailers, AsyncIterable):
            self.trailers_iterator = trailers
        else:
            self.trailers_iterator = iterate_in_threadpool(trailers)

    async def stream_response(self, send: Send, support_trailers: bool = False) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
                "trailers": self.trailers_iterator is not None,
            }
        )

        async for chunk in self.body_iterator:  # pragma: to be covered
            if not isinstance(chunk, bytes):
                chunk = chunk.encode(self.charset)
            await send({"type": "http.response.body", "body": chunk, "more_body": True})

        await send({"type": "http.response.body", "body": b"", "more_body": False})

        if self.trailers_iterator is not None and support_trailers:
            async for key, name in self.trailers_iterator:
                await send(
                    {
                        "type": "http.response.trailers",
                        "headers": [
                            (key.encode(self.charset), name.encode(self.charset))
                        ],
                        "more_trailers": True,
                    }
                )
            await send(
                {
                    "type": "http.response.trailers",
                    "headers": [],
                    "more_trailers": False,
                }
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        support_trailers = "http.response.trailers" in scope.get("extensions", {})
        async with anyio.create_task_group() as task_group:

            async def wrap(func: Callable[[], Awaitable[None]]) -> None:
                await func()
                task_group.cancel_scope.cancel()

            stream_response = partial(self.stream_response, send, support_trailers)
            listen_for_disconnect = partial(self.listen_for_disconnect, receive)

            task_group.start_soon(wrap, stream_response)
            await wrap(listen_for_disconnect)
