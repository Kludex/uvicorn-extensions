import asyncio
from contextlib import asynccontextmanager

from uvicorn.config import Config
from uvicorn.server import Server


@asynccontextmanager
async def run_server(config: Config, sockets=None):
    server = Server(config=config)
    task = asyncio.create_task(server.serve(sockets=sockets))
    await asyncio.sleep(0.1)
    try:
        yield server
    finally:
        await server.shutdown()
        task.cancel()
