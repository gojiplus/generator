#!/usr/bin/env python3
import argparse
import os
import sys
import requests
import pandas as pd
import openai
import json

# -------------------------------------
# Helpers to fetch GitHub data
# -------------------------------------

def fetch_repositories(org, token):
    """Fetch all repositories for a given GitHub organization."""
    url = f"https://api.github.com/orgs/{org}/repos"
    
    # Headers to include topics in response
    headers = {
        "User-Agent": "GitHubRepoSummarizer/1.0",
        "Accept": "application/vnd.github.mercy-preview+json"  # For topics
    }
    
    print(f"Attempting to fetch public repos without authentication")
    try:
        resp = requests.get(url, headers=headers)
        print(f"Public access status: {resp.status_code}")
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Public access attempt failed: {e}")
    
    # If that fails, try with token auth
    print(f"Attempting with token authentication")
    auth_headers = {
        "Authorization": f"token {token}",
        "User-Agent": "GitHubRepoSummarizer/1.0",
        "Accept": "application/vnd.github.mercy-preview+json"  # For topics
    }
    
    resp = requests.get(url, headers=auth_headers)
    print(f"Authenticated access status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"Response content: {resp.text[:500]}")
    
    resp.raise_for_status()
    return resp.json()


def fetch_specific_repos(repo_list, token):
    """Fetch individual repositories by full name (org/repo)."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.mercy-preview+json"  # For topics
    }
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
    headers = {"Authorization": f"token {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    download_url = data.get('download_url')
    if not download_url:
        return ""
    readme_resp = requests.get(download_url)
    return readme_resp.text

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
            'Topics': r.get('topics', []),  # GitHub topics/tags
            'README': readme,
        })
    return pd.DataFrame(rows)


def summarize_readme(content, repo_name, language, description, topics):
    """Generate a compelling portfolio summary of the README via OpenAI."""
    if not content and not description:
        return ""
    
    # Create a more comprehensive prompt for better summaries
    context_info = f"Repository: {repo_name}"
    if language:
        context_info += f" (Built with {language})"
    if description:
        context_info += f"\nGitHub Description: {description}"
    if topics:
        context_info += f"\nTopics/Tags: {', '.join(topics)}"
    
    prompt = f"""Create an engaging portfolio summary for this software project. Focus on:
- What the project does and its main purpose
- Key features and capabilities
- Technical implementation highlights
- Why it's impressive or noteworthy

{context_info}

README Content:
{content[:3000] if content else 'No README available'}

Write a compelling 3-4 sentence summary that would showcase this project well in a developer portfolio. Make it sound professional but engaging, highlighting the technical skills and problem-solving involved."""

    try:
        # Use the newer OpenAI client syntax
        client = openai.OpenAI()
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a technical writer specializing in creating compelling project descriptions for developer portfolios."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        # Fallback to use the basic description if OpenAI fails
        if description:
            return f"{description} This {language or 'software'} project demonstrates practical development skills and problem-solving capabilities."
        return f"[Error generating summary: {e}]"


def add_summaries(df):
    """Add portfolio-style summaries to the dataframe."""
    summaries = []
    for _, row in df.iterrows():
        summary = summarize_readme(
            row['README'], 
            row['Name'], 
            row['Language'], 
            row['Description'],
            row['Topics']
        )
        summaries.append(summary)
        print(f"✓ Generated summary for {row['Name']}")
    
    df['Summary'] = summaries
    return df

# -------------------------------------
# Main entry
# -------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate GitHub repo summaries for portfolio (JSON output)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--org_name', help="GitHub organization name to fetch all repos")
    group.add_argument('--repos', help="Comma-separated list of full repos (org/repo)")
    parser.add_argument('-o', '--output-file', default='portfolio_summaries.json',
                        help="Output JSON filename (default: portfolio_summaries.json)")
    parser.add_argument('--model', default='gpt-3.5-turbo',
                        help="OpenAI model to use (default: gpt-3.5-turbo)")
    args = parser.parse_args()

    gh_token = os.getenv('GITHUB_TOKEN')
    oa_key   = os.getenv('OPENAI_API_KEY')
    if not gh_token or not oa_key:
        print("Error: GITHUB_TOKEN and OPENAI_API_KEY must be set", file=sys.stderr)
        sys.exit(1)
    
    # Set up OpenAI client
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

    print(f"Building portfolio summaries for {len(repos_json)} repositories…")
    df = create_repo_dataframe(repos_json, gh_token)
    df = add_summaries(df)

    # Prepare JSON records with additional portfolio-friendly fields
    records = []
    for _, row in df.iterrows():
        record = {
            'name': row['Name'],
            'fullName': row['FullName'],
            'url': row['URL'],
            'description': row['Description'],
            'language': row['Language'],
            'stars': row['Stars'],
            'forks': row['Forks'],
            'openIssues': row['OpenIssues'],
            'topics': row['Topics'],  # Include topics in output
            'summary': row['Summary'],
            'featured': row['Stars'] > 5 or row['Forks'] > 2,  # Auto-mark popular repos as featured
        }
        records.append(record)
    
    # Sort by stars descending for better portfolio ordering
    records.sort(key=lambda x: x['stars'], reverse=True)
    
    with open(args.output_file, 'w') as f:
        json.dump(records, f, indent=2)

    print(f"✅ Saved portfolio summaries to {args.output_file}")
    print(f"📊 Generated summaries for {len(records)} repositories")
    featured_count = sum(1 for r in records if r['featured'])
    print(f"⭐ {featured_count} repositories marked as featured")

if __name__ == '__main__':
    main()
