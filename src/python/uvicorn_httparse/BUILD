python_sources()

resources(name="package_data", sources=["py.typed"])

python_distribution(
    name="dist",
    dependencies=[
        ":uvicorn_httparse",
        ":package_data",
    ],
    long_description_path="src/python/uvicorn_httparse/README.md",
    provides=python_artifact(
        name="uvicorn-httparse",
        version="0.0.0",
        description="Uvicorn HTTP implementation using httparse parser 🏃",
    ),
    repositories=["@pypi"],
)
