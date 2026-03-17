# Git Branching Strategy Guide
## FinShield AI - Financial Intelligence & Fraud Detection Engine

---


## 📋 Overview

    This guide will help you set up a professional Git branching workflow for your project with separate **development** and **testing** branches, protecting your main branch from direct changes.

---

## 🌳 Branching Strategy

### Branch Structure

```
main (production-ready code)
├── testing (QA/staging environment)
└── development (active development)
    ├── feature/fraud-detection-model
    ├── feature/dashboard-ui
    └── bugfix/transaction-validation
```

### Branch Purposes

| Branch | Purpose | Protected | Deploy To |
|--------|---------|-----------|-----------|
| **main** | Production-ready, stable releases | ✅ Yes | Production (Azure) |
| **testing** | QA testing, integration testing | ✅ Yes | Testing/Staging environment |
| **development** | Active development, feature integration | ⚠️ Optional | Development environment |
| **feature/** | Individual features | ❌ No | Local/Dev |
| **bugfix/** | Bug fixes | ❌ No | Local/Dev |
| **hotfix/** | Urgent production fixes | ❌ No | Direct to main after testing |

---

## 🚀 Step-by-Step Setup

### Step 1: Create Development Branch

```bash
# Navigate to your project directory
cd Project-7-AI-Financial-Intelligence-Fraud-Detection-Engine

# Ensure you're on main and it's up to date
git checkout main
git pull origin main

# Create and checkout development branch
git checkout -b development

# Push development branch to remote
git push -u origin development
```

### Step 2: Create Testing Branch

```bash
# Create testing branch from main
git checkout main
git checkout -b testing

# Push testing branch to remote
git push -u origin testing
```

### Step 3: Set Default Branch (Optional)

Go to GitHub → Settings → Branches → Default branch → Change to **development**

This makes `development` the default for new pull requests.

---

## 🔄 Workflow Process

### For New Features

```bash
# 1. Start from development branch
git checkout development
git pull origin development

# 2. Create feature branch
git checkout -b feature/transaction-monitoring

# 3. Work on your feature, commit changes
git add .
git commit -m "feat: add real-time transaction monitoring"

# 4. Push feature branch
git push -u origin feature/transaction-monitoring

# 5. Create Pull Request: feature/transaction-monitoring → development
# (Do this on GitHub)

# 6. After PR approval, merge to development
# (Done via GitHub PR interface)

# 7. Delete feature branch after merge
git branch -d feature/transaction-monitoring
git push origin --delete feature/transaction-monitoring
```

### Moving Code Through Environments

```bash
# Development → Testing (when ready for QA)
git checkout testing
git pull origin testing
git merge development
git push origin testing

# Testing → Main (when QA passes)
git checkout main
git pull origin main
git merge testing
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin main --tags
```

---

## 🛡️ Branch Protection Rules

### For Main Branch

Set up on GitHub → Settings → Branches → Branch protection rules:

- ✅ Require pull request before merging
- ✅ Require approvals (at least 1)
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Do not allow bypassing the above settings

### For Testing Branch

- ✅ Require pull request before merging
- ✅ Require approvals (at least 1)
- ✅ Require status checks to pass

---

## 📝 Commit Message Convention

Use conventional commits for better changelog generation:

```
feat: add fraud scoring algorithm
fix: resolve transaction validation bug
docs: update API documentation
style: format code with prettier
refactor: optimize ML model inference
test: add unit tests for risk engine
chore: update dependencies
```

---

## 🏗️ Project-Specific Workflow

### Frontend Development (Next.js)

```bash
# Create feature branch
git checkout -b feature/dashboard-real-time-updates

# Work in frontend directory
cd frontend
npm install
npm run dev

# Commit changes
git add .
git commit -m "feat(frontend): add real-time transaction dashboard"
git push -u origin feature/dashboard-real-time-updates
```

### Backend Development (FastAPI)

```bash
# Create feature branch
git checkout -b feature/fraud-detection-api

# Work in backend directory
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Commit changes
git add .
git commit -m "feat(backend): implement fraud detection endpoint"
git push -u origin feature/fraud-detection-api
```

### ML Model Development

```bash
git checkout -b feature/xgboost-fraud-model

# Work on models
cd backend/ml_models
# ... train and test models ...

git add .
git commit -m "feat(ml): add XGBoost fraud detection model"
git push -u origin feature/xgboost-fraud-model
```

---

## 🔧 Quick Commands Reference

```bash
# Check current branch
git branch

# Check all branches (including remote)
git branch -a

# Switch to a branch
git checkout development

# Create and switch to new branch
git checkout -b feature/new-feature

# Update current branch with latest from remote
git pull origin development

# Push current branch
git push origin HEAD

# Merge another branch into current
git merge feature/my-feature

# Delete local branch
git branch -d feature/old-feature

# Delete remote branch
git push origin --delete feature/old-feature

# View commit history
git log --oneline --graph --all
```

---

## 🎯 Best Practices

1. **Never commit directly to main or testing** - Always use feature branches
2. **Pull before you push** - Always `git pull` before pushing to avoid conflicts
3. **Small, focused commits** - Each commit should do one thing
4. **Write descriptive commit messages** - Future you will thank present you
5. **Review your own code** - Before creating PR, review your changes
6. **Keep branches short-lived** - Merge and delete feature branches quickly
7. **Sync regularly** - Pull from development daily to avoid large merge conflicts
8. **Tag releases** - Use semantic versioning (v1.0.0, v1.1.0, etc.)

---

## 🚨 Emergency Hotfix Process

For critical production bugs:

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-patch

# 2. Fix the issue
# ... make changes ...
git commit -m "hotfix: patch SQL injection vulnerability"

# 3. Merge to main
git checkout main
git merge hotfix/critical-security-patch
git tag -a v1.0.1 -m "Security hotfix"
git push origin main --tags

# 4. Merge to testing and development
git checkout testing
git merge hotfix/critical-security-patch
git push origin testing

git checkout development
git merge hotfix/critical-security-patch
git push origin development

# 5. Delete hotfix branch
git branch -d hotfix/critical-security-patch
git push origin --delete hotfix/critical-security-patch
```

---

## 📊 Workflow Diagram

```
Developer Work:
feature branch → development (PR + Review)

QA Testing:
development → testing (Merge when stable)

Production Release:
testing → main (Merge after QA approval + Tag version)
```

---

## 🎓 Next Steps

1. ✅ Create `development` and `testing` branches (follow Step 1 & 2 above)
2. ✅ Set up branch protection rules on GitHub
3. ✅ Configure CI/CD pipelines for each branch
4. ✅ Create your first feature branch
5. ✅ Document this workflow in your team's wiki

---

## 📞 Need Help?

- Review conflicts: `git status` → manually resolve → `git add .` → `git commit`
- Undo last commit (keep changes): `git reset --soft HEAD~1`
- Discard all local changes: `git reset --hard HEAD`
- See what changed: `git diff`

---

**Good luck with your FinShield AI project! 🚀**
