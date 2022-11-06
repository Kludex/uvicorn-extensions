python_sources()

resources(name="package_data", sources=["README.md", "py.typed"])

python_distribution(
    name="dist",
    dependencies=[
        ":uvicorn_trailers",
        ":package_data",
    ],
    provides=python_artifact(
        name="uvicorn-trailers",
        version="0.0.0",
        description="ASGI Trailers extension for Uvicorn 🚂",
    ),
    repositories=["@pypi"],
)
