import logging
import sys
from pathlib import Path
from typing import List, Union

from github import Github
from pydantic import BaseModel, BaseSettings, SecretStr


class Settings(BaseSettings):
    github_repository: str
    github_event_path: Path
    github_event_name: Union[str, None] = None
    input_token: SecretStr
    input_files: List[str]


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

    files = [file for file in pr.get_files() if file.filename in settings.input_files]

    if len(files) == 0:
        logging.error("PR does not contain changes on any file, skipping")
        sys.exit(0)

    file = files[0]
    logging.info(f"Found file {file.filename}")

    index = settings.input_files.index(file.filename)
    old_filename = settings.input_files[index - 1]

    new_content = repo.get_contents(file.filename, ref=pr.head.sha)
    old_content = repo.get_contents(old_filename, ref=pr.head.sha)

    logging.info(f"Updating file {old_filename}")
    repo.update_file(
        old_filename,
        f'🚧 Update "{old_filename}" from "{file.filename}"',
        new_content.decoded_content,
        old_content.sha,
        branch=pr.head.ref,
    )
    logging.info("Finished")
