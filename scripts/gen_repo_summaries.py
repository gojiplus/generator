#!/usr/bin/env python3
import argparse
import os
import sys
import requests
import pandas as pd
import openai
import yaml

# -------------------------------------
# Helpers to fetch GitHub data
# -------------------------------------

def fetch_repositories(org, token):
    """Fetch all repositories for a given GitHub organization."""
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {
        "Authorization": f"token {token}",  # Changed from Bearer to token
        "User-Agent": "GitHubRepoSummarizer/1.0"  # Added User-Agent
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()


def fetch_specific_repos(repo_list, token):
    """Fetch individual repositories by full name (org/repo)."""
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    for full in repo_list:
        try:
            org, repo = full.split('/', 1)
        except ValueError:
            print(f"⚠️  Invalid repository format: '{full}', skipping.", file=sys.stderr)
            continue
        url = f"https://api.github.com/repos/{org}/{repo}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            results.append(resp.json())
        else:
            print(f"⚠️  Could not fetch '{full}' (status {resp.status_code}), skipping.", file=sys.stderr)
    return results


def fetch_readme(org, repo, token):
    """Fetch the README text for a given repository."""
    url = f"https://api.github.com/repos/{org}/{repo}/readme"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return requests.get(data['download_url']).text

# -------------------------------------
# Build DataFrame and summarize
# -------------------------------------

def create_repo_dataframe(repos, token):
    """Convert repository metadata into a DataFrame, including README."""
    rows = []
    for r in repos:
        full = r.get('full_name', '')
        if '/' not in full:
            continue
        org, name = full.split('/', 1)
        try:
            readme = fetch_readme(org, name, token)
        except Exception:
            readme = ""
        rows.append({
            'Name': name,
            'FullName': full,
            'URL': r.get('html_url', ''),
            'Description': r.get('description') or '',
            'Language': r.get('language') or '',
            'Stars': r.get('stargazers_count', 0),
            'Forks': r.get('forks_count', 0),
            'OpenIssues': r.get('open_issues_count', 0),
            'README': readme,
        })
    return pd.DataFrame(rows)


def summarize_readme(content):
    """Generate a two-sentence summary of the README via OpenAI."""
    if not content:
        return ""
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You are a helpful assistant."},
                {"role":"user","content":
                    "Summarize the following repository README in two concise sentences:\n\n" + content
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error summarizing: {e}]"


def add_summaries(df):
    df['Summary'] = df['README'].apply(summarize_readme)
    return df

# -------------------------------------
# Main
# -------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate GitHub repo summaries (YAML output)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--org_name', help="GitHub organization name")
    group.add_argument('--repos', help="Comma-separated list of full repos (org/repo)")
    parser.add_argument('-o', '--output-file', default='repo_summaries.yaml',
                        help="Output YAML filename (default: repo_summaries.yaml)")
    args = parser.parse_args()

    gh_token = os.getenv('GITHUB_TOKEN')
    oa_key   = os.getenv('OPENAI_API_KEY')
    if not (gh_token and oa_key):
        print("Error: GITHUB_TOKEN and OPENAI_API_KEY must be set", file=sys.stderr)
        sys.exit(1)
    openai.api_key = oa_key

    if args.repos:
        repo_list = [r.strip() for r in args.repos.split(',') if r.strip()]
        print(f"🔍 Fetching specific repos: {repo_list}")
        repos_json = fetch_specific_repos(repo_list, gh_token)
    else:
        print(f"🔍 Fetching all repos for org: {args.org_name}")
        repos_json = fetch_repositories(args.org_name, gh_token)

    if not repos_json:
        print("No repositories found or fetched.", file=sys.stderr)
        sys.exit(1)

    print(f"Building DataFrame for {len(repos_json)} repositories…")
    df = create_repo_dataframe(repos_json, gh_token)
    df = add_summaries(df)

    # Drop README field and prepare YAML records
    records = df.drop(columns=['README']).to_dict(orient='records')
    with open(args.output_file, 'w') as f:
        yaml.safe_dump(records, f, sort_keys=False)

    print(f"✅ Saved summaries to {args.output_file}")

if __name__ == '__main__':
    main()
