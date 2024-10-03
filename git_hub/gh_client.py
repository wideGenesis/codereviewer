import os
import logging

from dotenv import load_dotenv
from github import Github

from open_ai.completion import create_completion

logging.basicConfig(level=logging.INFO)

load_dotenv(dotenv_path='settings/.env')

def get_github_client() -> Github:
    """
    Initialize the GitHub client using a Personal Access Token.
    The token should be stored as an environment variable for security.
    """
    access_token = os.getenv('GITHUB_TOKEN')  # Store your token in environment variables
    if not access_token:
        raise ValueError("GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    return Github(access_token)


def list_pull_requests(repo_name: str):
    """
    List all open pull requests for the specified repository.

    Args:
    - repo_name: The name of the repository in the format 'owner/repo'.

    Returns:
    - List of pull requests.
    """
    github_client = get_github_client()

    try:
        # Get the repository object
        repo = github_client.get_repo(repo_name)

        # Fetch all open pull requests
        pull_requests = repo.get_pulls(state='open')

        pr_list = []
        # Print pull request details
        for pr in pull_requests:
            logging.info(f"PR #{pr.number}: {pr.title} by {pr.user.login} (State: {pr.state})")
            logging.info(f"Created at: {pr.created_at}")
            logging.info(f"URL: {pr.html_url}")
            logging.info("-" * 50)
            pr_list.append(pr)

        return pr_list

    except Exception as e:
        logging.error(f"Error fetching pull requests: {e}")
        return None


def get_pull_request_commit_files(repo_name: str, pr_number: int):
    """
    Retrieve the changed files and content for each commit in a specified pull request.

    Args:
    - repo_name: The name of the repository in the format 'owner/repo'.
    - pr_number: The pull request number to fetch commits and files from.

    Returns:
    - A dictionary with commit SHAs as keys and lists of file details as values.
    """
    github_client = get_github_client()

    try:
        # Get the repository object
        repo = github_client.get_repo(repo_name)

        # Fetch the pull request by number
        pull_request = repo.get_pull(pr_number)

        logging.info(f"Fetching commits and files for PR #{pr_number}: {pull_request.title}")

        # Fetch the list of commits in the pull request
        commits = pull_request.get_commits()

        # Dictionary to store commit SHAs and their changed files
        commit_files = {}

        # Iterate over the commits and fetch changed files for each
        for commit in commits:
            sha = commit.sha
            logging.info(f"Fetching files for commit SHA: {sha}")

            # Get files changed in the commit
            files = commit.files
            changed_files = []

            for file in files:
                file_info = {
                    "filename": file.filename,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "changes": file.changes,
                    "status": file.status,
                    "patch": file.patch  # Contains the diff of changes
                }
                changed_files.append(file_info)

                # Log file information
                logging.info(f"File: {file.filename}, Additions: {file.additions}, Deletions: {file.deletions}")
                logging.info(f"Patch: {file.patch}")
                logging.info("-" * 50)

            # Store the changed files for this commit
            commit_files[sha] = changed_files

        return commit_files

    except Exception as e:
        logging.error(f"Error fetching commit files for PR #{pr_number}: {e}")
        return None

def local_code_reviewer(
        repo_path: str,
        branch_name: str,
        output_file: str,
        logger: Union[logging.Logger, CustomLogger],
        completion_client: Union[OpenAI, AsyncOpenAI],
        system_prompt: str,
        user_prompt:  str,
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

    # Получаем git diff
    diff_data = get_git_diff(repo_path, branch_name, logger)
    if not diff_data:
        logger.error("No changes found or error occurred while getting the diff.")
        return

    # Разделяем изменения на файлы и передаем их для анализа GPT
    comments = ""
    for file_diff in diff_data.split('diff --git'):
        if file_diff.strip():  # Игнорируем пустые строки
            file_comments = create_completion(
                openai_client=completion_client,
                system_prompt=system_prompt,
                user_prompt=user_prompt.format(file_diff),
                gpt_model=gpt_model
            )
            comments += f"Changes in file:\n{file_diff[:100]}\n\n{file_comments}\n\n"

    # Сохраняем комментарии в файл
    save_review_comments(comments, output_file, logger)