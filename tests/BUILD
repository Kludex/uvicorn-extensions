python_sources()

python_test_utils(name="test_utils")

python_tests(
    name="run",
    dependencies=["src/python/uvicorn-trailers:dist", "//:root#wsproto", ":tests"],
)
