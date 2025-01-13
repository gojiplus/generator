### RepoSum: AutoCreate and Update GitHub Website With Summary of All the Public Repositories

Keeping your GitHub website updated can be a pain. The [script](./gen_repo_summaries.py) iterates over all the repositories in the 'organization' to get the URL and metadata, uses OpenAI to come up with a whippy 2 sentence summary based on the readme of the repository, and generates a CSV. This CSV can be used to power the website. 

The script can be configured to be run using GitHub Actions. See [Github Workflows](.github/workflows). You will need to set your Github and OpenAI tokens.

#### Future

* Look at commits or the changelog to summarize changes since the last update.
* Users can control what is published via a YAML that takes in arguments such as:
1. List only public repositories
2. List only repositories with a minimum number of stars
