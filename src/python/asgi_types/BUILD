python_sources()

resources(name="package_data", sources=["py.typed"])

python_distribution(
    name="dist",
    dependencies=[
        ":asgi_types",
        ":package_data",
    ],
    long_description_path="src/python/asgi_types/README.md",
    provides=python_artifact(
        name="uvicorn-denial",
        version="0.1.0",
        description="ASGI typing module focused on correctness! 📋",
    ),
    repositories=["@pypi"],
)
