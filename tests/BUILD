python_sources()

python_test_utils(name="test_utils")

python_tests(
    name="run",
    dependencies=[":tests", "//:root#wsproto"],
    runtime_package_dependencies=[
        "src/python/uvicorn-trailers:dist",
        "src/python/uvicorn-extended:dist",
        "src/python/uvicorn-httparse:dist",
        "src/python/asgi-trailers:dist",
        "src/python/asgi-types:dist",
    ],
)
