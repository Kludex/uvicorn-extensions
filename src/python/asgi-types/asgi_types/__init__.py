import sys
from typing import Awaitable, Callable, Dict, Iterable, Optional, Tuple, Type, Union

from typing_extensions import NotRequired

if sys.version_info >= (3, 8):  # pragma: no cover
    from typing import Literal, TypedDict
else:  # pragma: no cover
    from typing_extensions import Literal, TypedDict


__all__ = (
    "ASGIVersions",
    "HTTPScope",
    "WebSocketScope",
    "LifespanScope",
    "WWWScope",
    "Scope",
    "HTTPRequestEvent",
    "HTTPResponseStartEvent",
    "HTTPResponseBodyEvent",
    "HTTPResponseTrailersEvent",
    "HTTPServerPushEvent",
    "HTTPDisconnectEvent",
    "WebSocketConnectEvent",
    "WebSocketAcceptEvent",
    "WebSocketReceiveEvent",
    "WebSocketSendEvent",
    "WebSocketResponseStartEvent",
    "WebSocketResponseBodyEvent",
    "WebSocketDisconnectEvent",
    "WebSocketCloseEvent",
    "LifespanStartupEvent",
    "LifespanShutdownEvent",
    "LifespanStartupCompleteEvent",
    "LifespanStartupFailedEvent",
    "LifespanShutdownCompleteEvent",
    "LifespanShutdownFailedEvent",
    "ASGIReceiveEvent",
    "ASGISendEvent",
    "ASGIReceiveCallable",
    "ASGISendCallable",
    "ASGIApp",
)


class ASGIVersions(TypedDict):
    spec_version: NotRequired[str]
    version: Union[Literal["2.0"], Literal["3.0"]]


class HTTPScope(TypedDict):
    type: Literal["http"]
    asgi: ASGIVersions
    http_version: str
    method: str
    scheme: str
    path: str
    raw_path: bytes
    query_string: bytes
    root_path: str
    headers: Iterable[Tuple[bytes, bytes]]
    client: NotRequired[Optional[Tuple[str, int]]]
    server: NotRequired[Optional[Tuple[str, Optional[int]]]]
    extensions: NotRequired[Dict[str, Dict[object, object]]]


class WebSocketScope(TypedDict):
    type: Literal["websocket"]
    asgi: ASGIVersions
    http_version: str
    scheme: str
    path: str
    raw_path: bytes
    query_string: bytes
    root_path: str
    headers: Iterable[Tuple[bytes, bytes]]
    client: NotRequired[Optional[Tuple[str, int]]]
    server: NotRequired[Optional[Tuple[str, Optional[int]]]]
    subprotocols: Iterable[str]
    extensions: NotRequired[Dict[str, Dict[object, object]]]


class LifespanScope(TypedDict):
    type: Literal["lifespan"]
    asgi: ASGIVersions


WWWScope = Union[HTTPScope, WebSocketScope]
Scope = Union[HTTPScope, WebSocketScope, LifespanScope]


class HTTPRequestEvent(TypedDict):
    type: Literal["http.request"]
    body: NotRequired[bytes]
    more_body: NotRequired[bool]


class HTTPResponseStartEvent(TypedDict):
    type: Literal["http.response.start"]
    status: int
    headers: NotRequired[Iterable[Tuple[bytes, bytes]]]
    trailers: NotRequired[bool]


class HTTPResponseBodyEvent(TypedDict):
    type: Literal["http.response.body"]
    body: NotRequired[bytes]
    more_body: NotRequired[bool]


class HTTPResponseTrailersEvent(TypedDict):
    type: Literal["http.response.trailers"]
    headers: Iterable[Tuple[bytes, bytes]]
    more_trailers: NotRequired[bool]


class HTTPServerPushEvent(TypedDict):
    type: Literal["http.response.push"]
    path: str
    headers: Iterable[Tuple[bytes, bytes]]


class HTTPDisconnectEvent(TypedDict):
    type: Literal["http.disconnect"]


class WebSocketConnectEvent(TypedDict):
    type: Literal["websocket.connect"]


class WebSocketAcceptEvent(TypedDict):
    type: Literal["websocket.accept"]
    subprotocol: NotRequired[Optional[str]]
    headers: NotRequired[Iterable[Tuple[bytes, bytes]]]


class WebSocketReceiveEvent(TypedDict):
    type: Literal["websocket.receive"]
    bytes: NotRequired[Optional[bytes]]
    text: NotRequired[Optional[str]]


class WebSocketSendEvent(TypedDict):
    type: Literal["websocket.send"]
    bytes: NotRequired[Optional[bytes]]
    text: NotRequired[Optional[str]]


class WebSocketResponseStartEvent(TypedDict):
    type: Literal["websocket.http.response.start"]
    status: int
    headers: NotRequired[Iterable[Tuple[bytes, bytes]]]
    trailers: NotRequired[bool]


class WebSocketResponseBodyEvent(TypedDict):
    type: Literal["websocket.http.response.body"]
    body: NotRequired[bytes]
    more_body: NotRequired[bool]


class WebSocketDisconnectEvent(TypedDict):
    type: Literal["websocket.disconnect"]
    code: NotRequired[int]


class WebSocketCloseEvent(TypedDict):
    type: Literal["websocket.close"]
    code: NotRequired[int]
    reason: NotRequired[Optional[str]]


class LifespanStartupEvent(TypedDict):
    type: Literal["lifespan.startup"]


class LifespanShutdownEvent(TypedDict):
    type: Literal["lifespan.shutdown"]


class LifespanStartupCompleteEvent(TypedDict):
    type: Literal["lifespan.startup.complete"]


class LifespanStartupFailedEvent(TypedDict):
    type: Literal["lifespan.startup.failed"]
    message: NotRequired[str]


class LifespanShutdownCompleteEvent(TypedDict):
    type: Literal["lifespan.shutdown.complete"]


class LifespanShutdownFailedEvent(TypedDict):
    type: Literal["lifespan.shutdown.failed"]
    message: NotRequired[str]


ASGIReceiveEvent = Union[
    HTTPRequestEvent,
    HTTPDisconnectEvent,
    WebSocketConnectEvent,
    WebSocketReceiveEvent,
    WebSocketDisconnectEvent,
    LifespanStartupEvent,
    LifespanShutdownEvent,
]


ASGISendEvent = Union[
    HTTPResponseStartEvent,
    HTTPResponseBodyEvent,
    HTTPResponseTrailersEvent,
    HTTPServerPushEvent,
    HTTPDisconnectEvent,
    WebSocketAcceptEvent,
    WebSocketSendEvent,
    WebSocketResponseStartEvent,
    WebSocketResponseBodyEvent,
    WebSocketCloseEvent,
    LifespanStartupCompleteEvent,
    LifespanStartupFailedEvent,
    LifespanShutdownCompleteEvent,
    LifespanShutdownFailedEvent,
]


ASGIReceiveCallable = Callable[[], Awaitable[ASGIReceiveEvent]]
ASGISendCallable = Callable[[ASGISendEvent], Awaitable[None]]


ASGIApp = Callable[[Scope, ASGIReceiveCallable, ASGISendCallable], Awaitable[None]]
