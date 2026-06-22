# GitHub Setup Instructions

Use these commands after downloading this folder.

## Option 1: GitHub CLI

```bash
cd carebridge-ai
git init
git add .
git commit -m "Initial commit: CareBridge AI healthcare data pipeline"
gh repo create carebridge-ai --public --source=. --remote=origin --push
```

## Option 2: GitHub website

1. Go to GitHub.
2. Click **New repository**.
3. Repository name: `carebridge-ai`.
4. Description: `HIPAA-aware healthcare payer data pipeline and executive insight layer.`
5. Choose Public or Private.
6. Do not add a README because this project already has one.
7. Create repository.
8. Run:

```bash
cd carebridge-ai
git init
git add .
git commit -m "Initial commit: CareBridge AI healthcare data pipeline"
git branch -M main
git remote add origin https://github.com/<your-username>/carebridge-ai.git
git push -u origin main
```
