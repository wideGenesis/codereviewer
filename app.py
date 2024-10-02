from git_hub.client import get_pull_request_commit_files, list_pull_requests

if __name__ == '__main__':
    repo_name = 'wideGenesis/codereviewer'
    pr_list = list_pull_requests(repo_name)
    try:
        pr_number = int(input("Enter number of PR:\n"))
    except Exception as e:
        print(e)
        exit(1)
    commit_files = get_pull_request_commit_files(repo_name, pr_number)

