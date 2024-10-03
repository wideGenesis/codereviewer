import logging
from typing import Union
import git
from openai import OpenAI, AsyncOpenAI
from common.az_logger.global_logger import CustomLogger
from open_ai.completion import create_completion

MAIN_BRANCH = 'main'


def check_branch_exists(repository, branch_name):
    """Проверяет, существует ли указанная ветка в репозитории."""
    if branch_name not in repository.branches:
        raise ValueError(f"Branch {branch_name} not found in the repository")


def get_git_diff(repo_path: str, branch_name: str, logger: logging.Logger) -> dict:
    """
    Получает различия между указанной веткой и основной веткой (main) в виде словаря.
    Args:
    - repo_path: Путь к локальному репозиторию.
    - branch_name: Имя ветки, которая будет проанализирована.
    Returns:
    - Словарь с именами файлов и их изменениями.
    """
    try:
        repository = git.Repo(repo_path)
        check_branch_exists(repository, branch_name)
        repository.git.checkout(branch_name)
        differences = repository.git.diff(MAIN_BRANCH, branch_name, unified=0)
        return differences
    except Exception as e:
        logger.error(f"Error getting git diff: {e}")
        return {}


def save_review_comments(comments: str, output_file: str, logger: logging.Logger):
    """
    Сохраняет предложенные изменения в текстовый файл.
    Args:
    - comments: Строка с комментариями для сохранения.
    - output_file: Путь к файлу, в который будут сохранены комментарии.
    """
    try:
        with open(output_file, 'w') as f:
            f.write(comments)
        logger.info(f"Comments successfully saved to {output_file}")
    except Exception as e:
        logger.error(f"Error writing to file {output_file}: {e}")


def local_code_reviewer(
        repo_path: str,
        branch_name: str,
        output_file: str,
        logger: Union[logging.Logger, CustomLogger],
        completion_client: Union[OpenAI, AsyncOpenAI],
        system_prompt: str,
        user_prompt: str,
        gpt_model: str
):
    """
    Основная функция агента. Получает изменения между веткой и main,
    анализирует их с помощью GPT и сохраняет результат.
    Args:
    - repo_path: Путь к локальному репозиторию.
    - branch_name: Имя ветки для анализа.
    - output_file: Путь к файлу для сохранения результатов.
    """
    logger.info(f"Starting code review for branch {branch_name} in repo {repo_path}")
    differences = get_git_diff(repo_path, branch_name, logger)
    if not differences:
        logger.error("No changes found or error occurred while getting the diff.")
        return
    comments = ""
    for file_difference in differences.split('diff --git'):
        if file_difference.strip():
            file_comments = create_completion(
                openai_client=completion_client,
                system_prompt=system_prompt,
                user_prompt=user_prompt.format(file_difference),
                gpt_model=gpt_model
            )
            comments += f"Changes in file:\n{file_difference[:100]}\n\n{file_comments}\n\n"
    save_review_comments(comments, output_file, logger)
