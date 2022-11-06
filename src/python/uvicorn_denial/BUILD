python_sources()

resources(name="package_data", sources=["py.typed"])

python_distribution(
    name="dist",
    dependencies=[
        ":uvicorn_denial",
        ":package_data",
    ],
    long_description_path="src/python/uvicorn_denial/README.md",
    provides=python_artifact(
        name="uvicorn-denial",
        version="0.0.0",
        description="Websocket Denial Response extension for Uvicorn 🔒",
    ),
    repositories=["@pypi"],
)
