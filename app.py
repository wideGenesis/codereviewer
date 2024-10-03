import logging
import os
from common.az_logger.global_logger import CustomLogger
from git_hub.gh_client import git_hub_code_reviewer
from git_local.local_client import local_code_reviewer
from openai import OpenAI
from open_ai.prompt.llm_prompt import SYSTEM, USER

# Настройка логгера
AZURE_LOGGER_NAMES = ['azure.core.pipeline.policies.http_logging_policy', 'azure.storage']
for logger_name in AZURE_LOGGER_NAMES:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

# Инициализация клиентов
completion_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
logger = CustomLogger(azure_connection_string=None, log_level_local="debug", log_level_azure="debug")

# Константы
REPO_PATH = "C:\\Users\\Genesis\\PycharmProjects\\codereviewer"
BRANCH_NAME = "rel_01"
OUTPUT_FILE_FOR_LOCAL = "code_review_comments.txt"
OUTPUT_FILE_FOR_GITHUB = "code_review_comments_from github.txt"
REPO_NAME = 'wideGenesis/codereviewer'

MODEL_NAME = "gpt-4o-mini"
REVIEW_ASSISTANT = SYSTEM["code_review_assistant"]
USER_PROMPT = USER["code_review"]


def get_review_params():
    return logger, completion_client, REVIEW_ASSISTANT, USER_PROMPT, MODEL_NAME


def run_local_code_reviewer():
    """
    Выполняет локальный код-ревью для указанного репозитория, ветки и выходного файла.
    :return: None
    """
    local_code_reviewer(REPO_PATH, BRANCH_NAME, OUTPUT_FILE_FOR_LOCAL, *get_review_params())


def run_github_code_reviewer():
    """
    Выполняет GitHub код-ревью для указанного репозитория.
    :return: None
    """
    git_hub_code_reviewer(REPO_NAME, OUTPUT_FILE_FOR_GITHUB, *get_review_params())


if __name__ == '__main__':
    run_local_code_reviewer()
    run_github_code_reviewer()
    logger.info("Code review process completed successfully.")
