import argparse
import os
import requests
import pandas as pd
import openai

def main():
    parser = argparse.ArgumentParser(description="Generate repository summaries")
    parser.add_argument("--name", required=True, help="GitHub Username or Organization Name")
    parser.add_argument("--github_token", required=True, help="GitHub Personal Access Token")
    parser.add_argument("--openai_api_key", required=True, help="OpenAI API Key")
    parser.add_argument("--type", choices=["user", "org"], required=True, help="Type: 'user' or 'org'")
    args = parser.parse_args()

    name = args.name
    github_token = args.github_token
    openai_api_key = args.openai_api_key
    entity_type = args.type

    openai.api_key = openai_api_key

    repos = fetch_repositories(name, github_token, entity_type)
    if repos:
        print(f"Found {len(repos)} repositories:")
        for repo in repos:
            print(f"- {repo['name']} ({repo['html_url']})")

        # Convert to pandas DataFrame and include README contents
        repo_df = create_repo_dataframe(repos, name, github_token)
        
        # Add summaries to the DataFrame
        repo_df = add_summaries_to_dataframe(repo_df)

        print("\nRepository Metadata with Summaries as DataFrame:")
        print(repo_df)

        # Save DataFrame to a CSV file
        save_dataframe(repo_df, f"{name}_repo_summaries.csv")
    else:
        print("No repositories found or an error occurred.")

def fetch_repositories(name, token, entity_type):
    """Fetch all repositories for the given GitHub user or organization."""
    base_url = f"https://api.github.com/{'users' if entity_type == 'user' else 'orgs'}/{name}/repos"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching repositories: {e}")
        return []

def fetch_readme(name, repo_name, token):
    """Fetch the README file for a given repository."""
    url = f"https://api.github.com/repos/{name}/{repo_name}/readme"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        readme_data = response.json()
        return requests.get(readme_data['download_url']).text
    except requests.exceptions.RequestException as e:
        return f"Error fetching README: {e}"

def create_repo_dataframe(repos, name, token):
    """Convert repository metadata into a pandas DataFrame, including README contents."""
    repo_data = []
    for repo in repos:
        readme_content = fetch_readme(name, repo['name'], token)
        repo_data.append({
            "Name": repo["name"],
            "URL": repo["html_url"],
            "Description": repo.get("description", "N/A"),
            "Language": repo.get("language", "N/A"),
            "Stars": repo.get("stargazers_count", 0),
            "Forks": repo.get("forks_count", 0),
            "Open Issues": repo.get("open_issues_count", 0),
            "README": readme_content,
        })
    return pd.DataFrame(repo_data)

def summarize_readme(readme_content):
    """Use OpenAI API to generate a two-sentence summary of the README content."""
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Summarize the following repository README in two marketable sentences:\n\n{readme_content}",
            max_tokens=100,
            temperature=0.7
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Error generating summary: {e}"

def add_summaries_to_dataframe(df):
    """Add a summary column to the DataFrame with summaries of each README."""
    df["Summary"] = df["README"].apply(summarize_readme)
    return df

def save_dataframe(df, filename):
    """Save the DataFrame to a CSV file."""
    try:
        df.to_csv(filename, index=False)
        print(f"DataFrame saved to {filename}")
    except Exception as e:
        print(f"Error saving DataFrame: {e}")

if __name__ == "__main__":
    main()
