import os
import logging

from dotenv import load_dotenv
from github import Github


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



def get_pull_requests(repo_name: str):
    """
    Retrieve all pull requests from the specified repository with logging.

    Args:
    - repo_name: The name of the repository in the format 'owner/repo'.

    Returns:
    - List of pull requests.
    """
    github_client = get_github_client()
    try:
        repo = github_client.get_repo(repo_name)
        logging.info(f"Fetching pull requests for repository: {repo_name}")

        pull_requests = repo.get_pulls(state='open')

        for pr in pull_requests:
            logging.info(f"PR #{pr.number}: {pr.title} by {pr.user.login}")
            logging.info(f"Created at: {pr.created_at}")
            logging.info(f"URL: {pr.html_url}")
            logging.info("-" * 50)

        return pull_requests

    except Exception as e:
        logging.error(f"Error fetching pull requests: {e}")
        return None
