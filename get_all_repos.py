import requests

def main():
    org_name = input("Enter GitHub Organization Name (e.g., openai): ").strip()
    personal_access_token = input("Enter GitHub Personal Access Token: ").strip()

    if not org_name or not personal_access_token:
        print("Error: Both organization name and personal access token are required.")
    else:
        repos = fetch_repositories(org_name, personal_access_token)
        if repos:
            print(f"Found {len(repos)} repositories:")
            for repo in repos:
                print(f"- {repo['name']} ({repo['html_url']})")
        else:
            print("No repositories found or an error occurred.")

def fetch_repositories(org_name, token):
    """Fetch all repositories for the given GitHub organization."""
    url = f"https://api.github.com/orgs/{org_name}/repos"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories: {e}")
        return []

if __name__ == "__main__":
    main()
