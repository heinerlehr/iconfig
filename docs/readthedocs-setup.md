# Read the Docs Setup Guide

## Prerequisites

1. Push your repository to GitHub with all the documentation files
2. Have a Read the Docs account (sign up at readthedocs.org)

## Setup Steps

### 1. Import Your Project

1. Go to [Read the Docs](https://readthedocs.org/)
2. Sign in with your GitHub account
3. Click "Import a Project"
4. Select your `iconfig` repository
5. Click "Next"

### 2. Project Configuration

- **Name**: `iconfig`
- **Repository URL**: `https://github.com/heinerlehr/iconfig`
- **Repository type**: Git
- **Default branch**: `master`
- **Language**: English
- **Programming language**: Python

### 3. Advanced Settings (Optional)

- **Python version**: 3.13
- **Use system packages**: No
- **Requirements file**: `docs/requirements.txt`
- **Python configuration file**: Leave empty (uses .readthedocs.yml)

### 4. Build Settings

The `.readthedocs.yml` file in your repository root will automatically configure:
- Python 3.13
- uv for dependency management
- Sphinx for documentation building
- All required dependencies

### 5. Webhook Setup (Automatic)

Read the Docs automatically sets up webhooks with GitHub, so your documentation will rebuild automatically on every push to the master branch.

## Custom Domain (Optional)

If you want a custom domain like `docs.iconfig.com`:

1. Go to your project's Admin → Domains
2. Add your custom domain
3. Point your DNS CNAME record to `readthedocs.io`

## Troubleshooting

### Build Failures

1. Check the build logs in Read the Docs dashboard
2. Ensure all dependencies are listed in `docs/requirements.txt`
3. Test locally with `make build-docs`

### Missing Dependencies

If builds fail due to missing packages, add them to `docs/requirements.txt`:

```text
# Add any missing packages here
your-package>=1.0.0
```

### Environment Issues

The `.readthedocs.yml` file specifies:
- Ubuntu 22.04
- Python 3.13
- uv for dependency management

If you need to change these, edit `.readthedocs.yml`.

## URLs

After setup, your documentation will be available at:
- **Main URL**: `https://iconfig.readthedocs.io/`
- **Latest**: `https://iconfig.readthedocs.io/en/latest/`
- **Stable**: `https://iconfig.readthedocs.io/en/stable/` (after first release)

## Badge for README

Add this badge to your README.md:

```markdown
[![Documentation Status](https://readthedocs.org/projects/iconfig/badge/?version=latest)](https://iconfig.readthedocs.io/en/latest/?badge=latest)
```