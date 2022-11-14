<!-- There's a synchronization between `docs/package/uvicorn-trailers.md` and `src/python/uvicorn-trailers/README.md` -->
# Uvicorn Trailers

The `uvicorn-trailers` package adds support for [HTTP Trailers] to [Uvicorn].

## Installation

```bash
pip install uvicorn-trailers
```

## Usage

```py
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", http="uvicorn_trailers.HTTPProtocol")
```

## License

This project is licensed under the terms of the MIT license.

[Uvicorn]: https://www.uvicorn.org
[HTTP Trailers]: https://asgi.readthedocs.io/en/latest/extensions.html#http-trailers
