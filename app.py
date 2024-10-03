from common.az_logger.global_logger import CustomLogger
from git_hub.client import get_pull_request_commit_files, list_pull_requests
from git_local.git_local import local_code_reviewer
import logging
import os

from openai import OpenAI

from open_ai.prompt.llm_prompt import SYSTEM, USER

logger = CustomLogger(azure_connection_string=None, log_level_local="debug", log_level_azure="debug")
for logger_name in ['azure.core.pipeline.policies.http_logging_policy', 'azure.storage']:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

completion_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def run_local_code_reviewer():
    # Пример использования
    repo_path = "C:\\Users\\Genesis\\PycharmProjects\\codereviewer"  # Путь к локальному проекту
    branch_name = "rel_01"  # Имя локальной ветки
    output_file = "code_review_comments.txt"  # Путь для сохранения результатов

    local_code_reviewer(
        repo_path,
        branch_name,
        output_file,
        logger,
        completion_client,
        SYSTEM["code_review_assistant"],
        USER["code_review"],
        "gpt-4o-mini")


def run_github_code_reviewer():
    repo_name = 'wideGenesis/codereviewer'
    pr_list = list_pull_requests(repo_name)
    try:
        pr_number = int(input("Enter number of PR:\n"))
    except Exception as e:
        print(e)
        exit(1)
    commit_files = get_pull_request_commit_files(repo_name, pr_number)


if __name__ == '__main__':
    run_local_code_reviewer()
