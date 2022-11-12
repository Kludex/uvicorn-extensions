resources(name="package_data", sources=["pyproject.toml", "README.md"])

python_distribution(
    name="dist",
    dependencies=[":package_data", "src/python/asgi-trailers/asgi_trailers"],
    provides=python_artifact(name="asgi-trailers"),
    generate_setup=False,
    repositories=["@pypi"],
)
