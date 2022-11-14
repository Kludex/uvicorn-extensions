import logging
import sys
from pathlib import Path
from time import sleep
from typing import List, Union

import httpx
from github import Github, GithubException
from github.PullRequest import PullRequest
from pydantic import BaseModel, BaseSettings, SecretStr

github_api = "https://api.github.com"


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
    with settings.github_event_path.open() as f:
        logging.info(f.read())

    event = PartialGitHubEvent.parse_file(settings.github_event_path)

    pr: PullRequest = repo.get_pull(event.number)
    for file in pr.get_files():
        print(file.filename, settings.input_files)
        if file.filename in settings.input_files:
            logging.info(f"Found file {file.filename}")
            index = settings.input_files.index(file.filename)
            print(file.contents_url)
            content = repo.get_contents(file.filename, ref=pr.head.ref)
            print(content.sha, pr.head.ref)
            repo.update_file(
                settings.input_files[index - 1],
                "Update",
                content.decoded_content,
                content.sha,
                branch=pr.head.ref,
            )
        print(file.filename)
    # try:
    # except ValidationError as e:
    #     logging.error(f"Error parsing event file: {e.errors()}")
    #     sys.exit(0)
    # use_pr: Union[PullRequest, None] = None
    # for pr in repo.get_pulls():
    #     if pr.head.sha == event.workflow_run.head_commit.id:
    #         use_pr = pr
    #         break
    # if not use_pr:
    #     logging.error(f"No PR found for hash: {event.workflow_run.head_commit.id}")
    #     sys.exit(0)
    # github_headers = {
    #     "Authorization": f"token {settings.input_token.get_secret_value()}"
    # }
    # url = f"{github_api}/repos/{settings.github_repository}/issues/{use_pr.number}/comments"
    # logging.info(f"Using comments URL: {url}")
    # response = httpx.post(
    #     url,
    #     headers=github_headers,
    #     json={
    #         "body": f"📝 Docs preview for commit {use_pr.head.sha} at: {settings.input_deploy_url}"
    #     },
    # )
    # if not (200 <= response.status_code <= 300):
    #     logging.error(f"Error posting comment: {response.text}")
    #     sys.exit(1)
    # logging.info("Finished")
