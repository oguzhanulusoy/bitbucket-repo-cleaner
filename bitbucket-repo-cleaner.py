from atlassian import Bitbucket
from datetime import datetime

import argparse
import yaml

# Inputs from user
PROJECT_KEY = None
REPOSITORY_SLUG = None
FILENAME = None # Fill a file (ex. not-allowed-branches) within branches that not to be deleted

# API setup
BITBUCKET_WRAPPER = None
CONFIGURATION_FILE = "configuration.yml"

def configure_bitbucket_api():
    """
        Configures the Bitbucket API.

        Side Effects:
            Modifies the global variable BITBUCKET_WRAPPER.
    """
    with open(CONFIGURATION_FILE) as file:
        config = yaml.safe_load(file)

    global BITBUCKET_WRAPPER
    BITBUCKET_WRAPPER = Bitbucket(
        url=config["url"],
        username=config["username"],
        password=config["password"],
        verify_ssl=False
    )

def load_not_allowed_branches():
    """
        Reads lines from a file and returns a list of branches
        which are not allowed to delete.

        Args:
            No method input due to it uses a global filename

        Returns:
            list[str]: List of lines from a file after trimmed

        Raises:
            FileNotFoundError: If filename not found
            Exception: Unexpected exception
    """
    lines = []
    try:
        with open(FILENAME, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file]
    except FileNotFoundError:
        print(f"Failure during execution: {FILENAME} could not be found.")
    except Exception as exception:
        print(f"Unexpected exception: {exception}")
    return lines

def set_not_allowed_branches_file():
    """
        Prompts the user to enter a file name and stores it
        in the global FILENAME variable.

        The input value is taken from standard input and
        assigned to the global scope for later use.

        Side Effects:
            Modifies the global variable FILENAME.

        Returns:
            None
        """
    global FILENAME
    FILENAME = input("Please enter filename (i.e., not-allowed-branches): ").strip()
    print(f"File {FILENAME} is set.")

def set_project_key():
    """
        Prompts the user to enter a project key and stores it
        in the global PROJECT_KEY variable.

        The input value is taken from standard input and
        assigned to the global scope for later use.

        Side Effects:
            Modifies the global variable PROJECT_KEY.

        Returns:
            None
    """
    global PROJECT_KEY
    PROJECT_KEY = input("Please enter project key (i.e., ISPJ): ").strip()
    print(f"Project key {PROJECT_KEY} is set.")

def set_repository_slug():
    """
        Prompts the user to enter a repository slug and stores it
        in the global REPOSITORY_SLUG variable.

        The input value is taken from standard input and
        assigned to the global scope for later use.

        Side Effects:
            Modifies the global variable REPOSITORY_SLUG.

        Returns:
            None
    """
    global REPOSITORY_SLUG
    REPOSITORY_SLUG = input("Please enter repository slug (i.e., prov-onends-adapter): ").strip()
    print(f"Repository slug {REPOSITORY_SLUG} is set.")

def get_project_details():
    """
        Retrieves and prints Bitbucket project details
        using the globally defined PROJECT_KEY.

        The function queries the Bitbucket API for the project
        associated with the given project key.

        Returns:
            dict: Project details returned from the Bitbucket API.

        Raises:
            ValueError: If PROJECT_KEY is not set or invalid.
            Exception: If the Bitbucket API request fails.
    """
    project_details = BITBUCKET_WRAPPER.project(PROJECT_KEY)
    print(project_details)
    return project_details

def get_repository_details():
    """
        Retrieves and prints Bitbucket repository details using
        the globally defined PROJECT_KEY and REPOSITORY_SLUG.

        The function queries the Bitbucket API to fetch repository
        information for the given project and repository.

        Returns:
            dict: Repository details returned from the Bitbucket API.

        Raises:
            ValueError: If PROJECT_KEY or REPOSITORY_SLUG is not set or invalid.
            Exception: If the Bitbucket API request fails.
    """
    repository_details = BITBUCKET_WRAPPER.get_repo(PROJECT_KEY, REPOSITORY_SLUG)
    print(repository_details)
    return repository_details

def get_branches():
    """
        Retrieves branch information for the specified Bitbucket repository.

        The function fetches all branches associated with the repository
        identified by the global PROJECT_KEY and REPOSITORY_SLUG.

        Returns:
            list[dict]: A list of branches returned from the Bitbucket API.

        Raises:
            ValueError: If PROJECT_KEY or REPOSITORY_SLUG is not set or invalid.
            Exception: If the Bitbucket API request fails.
    """
    branches = BITBUCKET_WRAPPER.get_branches(PROJECT_KEY,
                                      REPOSITORY_SLUG,
                                      filter='',
                                      limit=99999,
                                      details=True,
                                      boost_matches=False)
    return branches

def save_branches():
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"branches-{REPOSITORY_SLUG}-{date_str}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        for item in get_branches():
            f.write(item["displayId"] + "\n")

def delete_branches():
    """
        Deletes non-default branches from the Bitbucket repository
        except those listed as protected milestone branches.

        The function retrieves all repository branches and deletes
        each branch that:
        - is not marked as default
        - is not included in the list of not allowed branches

        Protected branches are obtained via load_not_allowed_branches().

        Side Effects:
            Deletes branches from the remote Bitbucket repository.

        Returns:
            None

        Raises:
            Exception: If a branch deletion request fails.
    """
    not_allowed_branches = load_not_allowed_branches()
    for branch in get_branches():
        print(branch)
        branch_name = branch["displayId"]
        branch_is_default = branch["isDefault"]
        if branch_name in not_allowed_branches:
            continue
        if branch_is_default:
            continue
        else:
            try:
                BITBUCKET_WRAPPER.delete_branch(PROJECT_KEY, REPOSITORY_SLUG, branch_name, end_point=None)
            except Exception as exception:
                print(f"Failure while deleting branch '{branch_name}': {exception}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script enables to remove branches which are getting from Bitbucket. "
                    "You can specify the branches that not to be removed."
                    "While running the script, you need to apply each steps respectively."
    )
    parser.add_argument(
        "--filename",
        required=False,
        help="List of not allowed branches"
    )

    args = parser.parse_args()
    print(args)

    try:
        print("Please apply the steps respectively.")
        configure_bitbucket_api()
        while True:
            preference = input("\n0. Set filename"
                               "\n1. Set project key"
                               "\n2. Set repository slug"
                               "\n3. Get project details"
                               "\n4. Get repository details"
                               "\n5. Get branches"
                               "\n6. Save branches"
                               "\n7. Show not allowed branches"
                               "\n8. Delete branches"
                               "\nEnter your preference: ")
            if preference.strip() == "0":
                set_not_allowed_branches_file()
            elif preference.strip() == "1":
                set_project_key()
            elif preference.strip() == "2":
                set_repository_slug()
            elif preference.strip() == "3":
                get_project_details()
            elif preference.strip() == "4":
                get_repository_details()
            elif preference.strip() == "5":
                get_branches()
            elif preference.strip() == "6":
                save_branches()
            elif preference.strip() == "7":
                print(load_not_allowed_branches())
            elif preference.strip() == "8":
                delete_branches()
            else:
                print("Thanks for using me - bye!")
                break
    except Exception as exception:
        print(f"Unexpected exception: {exception}")

