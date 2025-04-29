## 🏭 Generator: AutoCreate and Update GitHub Website With Summary of All the Public Repositories

Tired of manually updating your organization's website with repository details? Say hello to the ultimate GitHub repository summary generator! 

### ✨ Features

- **Automated Discovery**: Crawls through all public repositories in an organization
- **AI-Powered Summaries**: Generates crisp, compelling two-sentence descriptions using OpenAI
- **Flexible Output**: Produces a clean CSV ready for website integration
- **GitHub Actions Ready**: Seamlessly runs as a workflow

## 🚦 Roadmap

### Immediate Future
- 🌐 Create a Jekyll-ready repository for easy website deployment

### Upcoming Features
- 📈 Commit-based change tracking
- 🎛 Granular repository filtering:
  - Limit to public repositories
  - Filter by star count
  - Custom inclusion/exclusion rules

## 🔧 Configuration

### Prerequisites
- GitHub Token
- OpenAI API Key

### GitHub Actions Setup
```yaml
- name: Generate Repo Summaries
  uses: yourusername/repo-summarizer@v1
  with:
    org_name: 'your-org-name'
```

## 💡 Why Use This?

Keeping your organization's digital presence up-to-date shouldn't be a chore. This tool automates the mundane, letting you focus on what matters - building awesome software!

## 📄 License

MIT @ MatmulAI
