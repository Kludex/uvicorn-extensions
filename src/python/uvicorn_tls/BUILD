python_sources()

resources(name="package_data", sources=["py.typed"])

python_distribution(
    name="dist",
    dependencies=[
        ":uvicorn_tls",
        ":package_data",
    ],
    long_description_path="src/python/uvicorn_tls/README.md",
    provides=python_artifact(
        name="uvicorn-tls",
        version="0.0.0",
        description="ASGI TLS extension for Uvicorn 🔒",
    ),
    repositories=["@pypi"],
)
