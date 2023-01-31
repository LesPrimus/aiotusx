import typing
import string
import threading
import time
import random
from io import BytesIO

import pytest
import starlette.requests
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Route, Mount
from starlette.endpoints import HTTPEndpoint
from uvicorn import Config, Server


class Concatenate(HTTPEndpoint):
    async def post(self, request: starlette.requests.Request):
        location = f"{request.url}/{random.choice(string.ascii_letters).lower()}"
        headers = {"Location": location}
        return Response(status_code=201, headers=headers)

    async def patch(self, request: starlette.requests.Request):
        return Response(status_code=204)


app = Starlette(
    debug=True,
    routes=[
        # Concatenate
        Route("/concatenate/files", Concatenate),
        Route("/concatenate/files/{file_id}", Concatenate),
    ],
)


def serve_in_thread(server):
    thread = threading.Thread(target=server.run)
    thread.start()
    try:
        while not server.started:
            time.sleep(1e-3)
        yield server
    finally:
        server.should_exit = True
        thread.join()


@pytest.fixture(scope="function")
def server() -> typing.Iterator[Server]:
    config = Config(app=app, lifespan="off", loop="asyncio")
    server = Server(config)
    yield from serve_in_thread(server)
