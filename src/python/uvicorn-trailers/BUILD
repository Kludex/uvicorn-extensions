resources(name="package_data", sources=["pyproject.toml", "README.md"])

python_distribution(
    name="dist",
    dependencies=[":package_data", "src/python/uvicorn-trailers/uvicorn_trailers"],
    provides=python_artifact(name="uvicorn-trailers"),
    generate_setup=False,
    repositories=["@pypi"],
)
