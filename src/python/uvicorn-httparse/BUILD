resource(name="pyproject", source="pyproject.toml")

python_distribution(
    name="dist",
    dependencies=[":pyproject"],
    provides=python_artifact(name="uvicorn-httparse"),
    wheel_config_settings={"--global-option": ["--python-tag", "py37.py38.py39.py310.py311"]},
    generate_setup = False,
    repositories=["@pypi"],
)
