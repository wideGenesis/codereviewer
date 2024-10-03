import os
import logging
import re
from typing import Union, List, Dict

from dotenv import load_dotenv
from github import Github
from openai import OpenAI, AsyncOpenAI

from common.az_logger.global_logger import CustomLogger
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
        for pr in pull_requests:
            logging.info(f"PR #{pr.number}: {pr.title} by {pr.user.login} (State: {pr.state})")
            logging.info(f"Created at: {pr.created_at}")
            logging.info(f"URL: {pr.html_url}")
            logging.info("-" * 50)
            pr_list.append(pr)

        if len(pr_list) == 0:
            logging.info("No open pull requests found. Exiting.")
            exit(0)

        return pr_list

    except Exception as e:
        logging.error(f"Error fetching pull requests: {e}")
        return None


def get_pull_request_commit_files(repo_name: str, pr_number: int) -> Dict[str, List[Dict[str, Union[str, int]]]]:
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
        repo = github_client.get_repo(repo_name)
        pull_request = repo.get_pull(pr_number)
        logging.info(f"Fetching commits and files for PR #{pr_number}: {pull_request.title}")

        commits = pull_request.get_commits()
        commit_files = {}

        for commit in commits:
            sha = commit.sha
            logging.info(f"Fetching files for commit SHA: {sha}")
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
                logging.info(f"File: {file.filename}, Additions: {file.additions}, Deletions: {file.deletions}")
                logging.info(f"Patch: {file.patch}")
                logging.info("-" * 50)

            commit_files[sha] = changed_files

        return commit_files

    except Exception as e:
        logging.error(f"Error fetching commit files for PR #{pr_number}: {e}")
        return {}


def extract_python_files_from_commit(commit_data: Dict[str, List[Dict[str, Union[str, int]]]]) -> List[Dict[str, str]]:
    """
    Extracts changes of Python files from commit data.

    Args:
    - commit_data: The commit data in dictionary format.

    Returns:
    - List of dictionaries with 'filename' and 'changes' for each Python file.
    """
    python_files = []

    # Iterate over commits
    for sha, files in commit_data.items():
        for file_info in files:
            filename = file_info.get('filename')
            patch = file_info.get('patch', '')

            if filename and filename.endswith('.py'):
                python_files.append({
                    'filename': filename,
                    'changes': patch
                })

    return python_files


def format_changes_for_llm(python_files: List[Dict[str, str]]) -> str:
    """
    Formats the changes of Python files for LLM input.

    Args:
    - python_files: List of dictionaries with 'filename' and 'changes'.

    Returns:
    - Formatted string to be sent to the LLM.
    """
    formatted_output = ""
    for file_data in python_files:
        formatted_output += f"### Changes in {file_data['filename']}:\n\n"
        formatted_output += f"{file_data['changes']}\n\n"
    return formatted_output

def save_review_comments(comments: str, output_file: str, logger: logging.Logger) -> None:
    """
    Save the review comments to a specified file.

    Args:
    - comments: The review comments to save.
    - output_file: The path where the comments will be saved.
    """
    try:
        with open(output_file, 'w') as f:
            f.write(comments)
        logger.info(f"Review comments successfully saved to {output_file}")
    except Exception as e:
        logger.error(f"Error saving review comments to {output_file}: {e}")


def git_hub_code_reviewer(
        repo_name: str,
    output_file: str,
        logger: Union[logging.Logger, CustomLogger],
        completion_client: Union[OpenAI, AsyncOpenAI],
        system_prompt: str,
        user_prompt: str,
        gpt_model: str
):
    logger.info(f"Starting code review for repo {repo_name}")
    pr_list = list_pull_requests(repo_name)

    try:
        pr_number = int(input("Enter number of PR:\n"))
    except Exception as e:
        logger.exception(e)
        exit(1)

    try:
        commit_data = get_pull_request_commit_files(repo_name, pr_number)
    except Exception as e:
        logger.exception(e)
        exit(1)

    python_files = extract_python_files_from_commit(commit_data)

    # Initialize an empty string to hold all comments
    all_comments = ""

    # Loop through each Python file and send its content to OpenAI
    for file_data in python_files:
        file_diff = file_data['changes']
        filename = file_data['filename']

        try:
            # Send the diff to OpenAI for review
            file_comments = create_completion(
                openai_client=completion_client,
                system_prompt=system_prompt,
                user_prompt=user_prompt.format(file_diff),
                gpt_model=gpt_model
            )
            # Append the comments for this file to the overall comments
            all_comments += f"### Review for {filename}:\n\n"
            all_comments += f"{file_comments}\n\n"
        except Exception as e:
            logger.error(f"Error during GPT completion for file {filename}: {e}")

    # Save all the review comments to a file
    save_review_comments(all_comments, output_file, logger)
