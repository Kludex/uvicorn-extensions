import httpx
import pytest
from httpx_ws import WebSocketUpgradeError, aconnect_ws
from uvicorn.config import Config

from tests.utils import run_server


@pytest.mark.anyio
async def test_websocket_denial(
    ws_protocol, http_protocol, unused_tcp_port: int
) -> None:
    async def app(scope, receive, send):
        message = await receive()
        assert message["type"] == "websocket.connect"

        await send(
            {"type": "websocket.http.response.start", "status": 200, "headers": []}
        )
        await send({"type": "websocket.http.response.body", "body": b""})

    config = Config(
        app=app,
        ws=ws_protocol,
        http=http_protocol,
        lifespan="off",
        port=unused_tcp_port,
    )
    async with run_server(config):
        async with httpx.AsyncClient() as client:
            try:
                address = f"http://localhost:{unused_tcp_port}"
                async with aconnect_ws(client, address):
                    ...  # pragma: no cover

            except WebSocketUpgradeError as exc:
                assert exc.response.status_code == 200

    # NOTE: Tests here are lacking. The websocket clients do not read the body.
