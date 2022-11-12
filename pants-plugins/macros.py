def hatch_distribution(name, package, **kwargs):
    resources(name="package_data", sources=["pyproject.toml", "README.md"])

    python_distribution(
        name="dist",
        dependencies=[":package_data", f"src/python/{name}/{package}"],
        provides=python_artifact(name=name),
        generate_setup=False,
        repositories=["@pypi"],
    )

def typed_python_sources(**kwargs):
    resource(name="stubs", source="py.typed")

    python_sources(dependencies=[":stubs"], **kwargs)
