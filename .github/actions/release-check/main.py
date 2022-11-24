import logging
import os
from pathlib import Path
from typing import Union

import rtoml
from github import Github
from pydantic import BaseModel, BaseSettings, SecretStr


class Settings(BaseSettings):
    github_repository: str
    github_event_path: Path
    github_event_name: Union[str, None] = None
    input_token: SecretStr


class PartialGitHubEvent(BaseModel):
    number: int


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    settings = Settings()
    logging.info(f"Using config: {settings.json()}")

    gh = Github(settings.input_token.get_secret_value())
    repo = gh.get_repo(settings.github_repository)

    event = PartialGitHubEvent.parse_file(settings.github_event_path)
    pr = repo.get_pull(event.number)

    for file in pr.get_files():
        if file.filename.endswith("pyproject.toml"):
            logging.info(f"Found pyproject.toml in {file.filename}")

            content = repo.get_contents(file.filename, ref=pr.head.sha)
            obj = rtoml.loads(content.decoded_content.decode("utf-8"))
            project = obj["project"]
            version = project["version"]
            name = project["name"]

            content = repo.get_contents(file.filename, ref="main")
            old_obj = rtoml.loads(content.decoded_content.decode("utf-8"))
            old_project = old_obj["project"]
            old_version = old_project["version"]

            if old_version == version:
                logging.info(f"Version {version} already exists, skipping")
                with open(os.environ["GITHUB_ENV"], "a") as fh:
                    print("release=false", file=fh)
                continue

            logging.info(f"Updating version from {old_version} to {version}")

            tag = f"{name}/{version}"

            with open(os.environ["GITHUB_OUTPUT"], "a") as fh:
                print(f"tag={tag}", file=fh)
                print(f"package={name}", file=fh)
                print("release=true", file=fh)
