<!-- There's a synchronization between `docs/package/uvicorn-denial.md` and `src/python/uvicorn-denial/README.md` -->
# Uvicorn Denial

The `uvicorn-denial` package implements the **[Websocket Denial Response]** on **[Uvicorn]**.

## Installation

```bash
pip install uvicorn-denial
```

## Usage


=== "Server"

    You can run the following code with `python main.py`.

    ```py title="main.py"
    import uvicorn
    import uvicorn_denial


    async def app(scope, receive, send):
        await send(
            {
                "type": "websocket.http.response.start",
                "status": 200,
                "headers": [("content-length", "4")]
            }
        )
        await send({"type": "websocket.http.response.body", "body": b"haha"})


    if __name__ == "__main__":
        uvicorn.run(app, ws=uvicorn_denial.WSProtocol)
    ```

=== "Client"

    Then using **[curl]**, we can make calls to our server:

    ```bash
    curl --include \
        --no-buffer \
        --header "Connection: Upgrade" \
        --header "Upgrade: websocket" \
        --header "Host: example.com:80" \
        --header "Origin: http://example.com:80" \
        --header "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
        --header "Sec-WebSocket-Version: 13" \
        http://localhost:8000/
    ```

## License

This project is licensed under the terms of the MIT license.

[curl]: https://curl.se/
[Uvicorn]: https://www.uvicorn.org
[Websocket Denial Response]: https://asgi.readthedocs.io/en/latest/extensions.html#websocket-denial-response
