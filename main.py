async def app(scope, receive, send):
    await send(
        {
            "type": "websocket.http.response.start",
            "status": 200,
            "headers": [("content-length", "4")],
        }
    )
    await send({"type": "websocket.http.response.body", "body": b"haha"})


if __name__ == "__main__":
    import uvicorn
    import uvicorn_denial

    uvicorn.run(app, ws=uvicorn_denial.WSProtocol)
