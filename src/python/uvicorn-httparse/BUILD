resources(name="package_data", sources=["pyproject.toml", "README.md"])

python_distribution(
    name="dist",
    dependencies=[":package_data", "src/python/uvicorn-httparse/uvicorn_httparse"],
    provides=python_artifact(name="uvicorn-httparse"),
    wheel_config_settings={
        "--global-option": ["--python-tag", "py37.py38.py39.py310.py311"]
    },
    generate_setup=False,
    repositories=["@pypi"],
)
