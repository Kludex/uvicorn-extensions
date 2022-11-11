# Uvicorn Extensions

This repository contains a collection of extensions for [Uvicorn](https://www.uvicorn.org/).

## Roadmap

### Features & Packages

- [ ] `uvicorn-worker`: A Uvicorn worker for [Gunicorn](https://gunicorn.org/).
- [ ] `uvicorn-trailers`: A package that implements [HTTP Trailers](https://tools.ietf.org/html/rfc7230#section-4.1.2).
- [ ] `uvicorn-httparse`: A package that uses a Rust-based HTTP parser.
- [ ] `uvicorn-denial`: A package that implements WebSocket Denial Response ASGI extension.
- [ ] `uvicorn-tls`: A package that implements TLS ASGI extension.
- [ ] `uvicorn-zero-copy`: A package that implements Zero-Copy Send ASGI extension.
- [ ] `uvicorn-http2`: A package that adds support for HTTP/2 to Uvicorn.
- [ ] `uvicorn-manager`: A multiprocess manager for Uvicorn.
- [ ] `uvicorn-extended`: A package that implements all of the above extensions.

### Infra & Extras

- [ ] Documentation
- [ ] CI/CD
    - [ ] Release only modified packages
    - [ ] Enforce changelog entry from each commit
    - [ ] Publish to PyPI
- [ ] Add .devcontainer
- [ ] Test setup
- [ ] Think about fork uvicorn & backport of changes

## License

This project is licensed under the terms of the MIT license.
