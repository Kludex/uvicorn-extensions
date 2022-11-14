# Welcome to Uvicorn Extensions

This repository contains a collection of experimental features for **[Uvicorn]**.

Each feature is implemented as a **separate package**, and can be installed **independently**.

## Packages

- **[uvicorn-httparse]**: Uvicorn HTTP implementation that uses **[httparse]** to parse HTTP requests.
- **[uvicorn-trailers]**: Uvicorn with **[HTTP Trailers extension]** support.
- **[asgi-trailers]**: An ASGI framework that supports **[HTTP Trailers]**.


[Uvicorn]: https://www.uvicorn.org
[HTTP Trailers extension]: https://asgi.readthedocs.io/en/latest/extensions.html#http-trailers
[uvicorn-httparse]: packages/uvicorn-httparse.md
[uvicorn-trailers]: packages/uvicorn-trailers.md
[asgi-trailers]: packages/asgi-trailers.md
[HTTP Trailers]: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Trailer
[httparse]: https://github.com/adriangb/httparse
