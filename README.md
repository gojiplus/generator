### AutoCreate GitHub Website

Keeping your GitHub website updated can be a pain. We provide a script that runs using GitHub Actions on a regular cadence to:

1. Iterate over all the repositories in the 'organization' to get the URL and metadata
2. Uses ChatGPT to summarize each repository
3. Updates a CSV

This CSV is behind what is published online.

Users can control what is published via a YAML that takes in arguments such as:
1. List only public repositories
2. List only repositories with a minimum number of stars

#### Future

Look at commits or the changelog to summarize changes since the last update.
