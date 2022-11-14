<!-- There's a synchronization between `docs/package/uvicorn-httparse.md` and `src/python/uvicorn-httparse/README.md` -->
# Uvicorn HTTParse

The `uvicorn-httparse` package uses **[httparse]** to parse HTTP requests in **[Uvicorn]**.

**[httparse]** is a Python binding of a **[Rust library]** that gives its name.

## Installation

```bash
pip install uvicorn-httparse
```

## Usage

```py
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", http="uvicorn_httparse.HttparseProtocol")
```

For more details, see the **[Uvicorn documentation]**.

## License

This project is licensed under the terms of the MIT license.

[Uvicorn]: https://www.uvicorn.org
[httparse]: https://github.com/adriangb/httparse
[Rust library]: https://github.com/seanmonstar/httparse
[Uvicorn documentation]: https://www.uvicorn.org
