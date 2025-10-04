# GitHub Templates

This directory contains templates for GitHub issues and pull requests.

## Issue Templates

### Bug Report
Use the bug report template when you encounter a problem with the application. This helps us gather all the necessary information to reproduce and fix the issue.

**When to use:**
- Application crashes or errors
- Unexpected behavior
- Performance issues
- Installation problems

### Feature Request
Use the feature request template to suggest new functionality or enhancements.

**When to use:**
- Proposing new features
- Suggesting improvements to existing features
- Requesting new integrations
- UI/UX enhancements

## Pull Request Template

The pull request template ensures all PRs include necessary information for review.

**Required information:**
- Description of changes
- Related issue(s)
- Type of change
- Testing performed
- Checklist completion

## Creating Issues

1. Go to the [Issues](../../issues) page
2. Click "New Issue"
3. Select the appropriate template
4. Fill in all required sections
5. Submit the issue

## Creating Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters (`make all`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request using the template

## Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. The hooks will automatically:
- Format code with Black and isort
- Check for common issues
- Run linters (flake8)
- Perform security checks (bandit)

### Installing Pre-commit Hooks

```bash
make pre-commit-install
# or
pre-commit install
```

### Running Pre-commit Manually

```bash
make pre-commit-run
# or
pre-commit run --all-files
```

The hooks will run automatically on every commit, ensuring code quality standards are met before changes are committed.
