# Contributing to Transcription and Summary App

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- pip

### Setup Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/abnew123/transcription-and-summary.git
   cd transcription-and-summary
   ```

2. **Install dependencies**
   ```bash
   make install
   # or
   pip install -r requirements.txt
   pre-commit install
   ```

3. **Configure the application**
   - Copy `.env.example` to `.env`
   - Add your API keys (OpenAI, Claude, Google)
   - Adjust `config.yaml` as needed

## Development Workflow

### Pre-commit Hooks

This project uses pre-commit hooks to maintain code quality. They run automatically on every commit and check:
- Code formatting (Black, isort)
- Linting (flake8)
- Security issues (bandit)
- Common file issues (trailing whitespace, EOF, etc.)

**Install hooks:**
```bash
make pre-commit-install
```

**Run manually:**
```bash
make pre-commit-run
```

**Skip hooks (not recommended):**
```bash
SKIP=flake8,bandit git commit -m "message"
```

### Code Quality

**Run tests:**
```bash
make test
# or with coverage
make test-cov
```

**Run linters:**
```bash
make lint
```

**Format code:**
```bash
make format
```

**Run everything:**
```bash
make all
```

## Making Changes

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clear, concise code
- Follow existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run tests
make test

# Run linters
make lint

# Format code
make format
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "Brief description of changes

Detailed explanation if needed.

Co-authored-by: Ona <no-reply@ona.com>"
```

The pre-commit hooks will run automatically. Fix any issues they find.

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub using the PR template.

## Pull Request Guidelines

- Fill out the PR template completely
- Link related issues
- Ensure all tests pass
- Ensure code is formatted and linted
- Add screenshots for UI changes
- Request review from maintainers

## Code Style

### Python
- Follow PEP 8
- Use Black for formatting (line length: 120)
- Use isort for import sorting
- Use type hints where appropriate
- Write docstrings for public functions/classes

### Naming Conventions
- Classes: `PascalCase`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Comments
- Document the "why," not the "what"
- Avoid redundant comments
- Use docstrings for public APIs

## Testing

### Writing Tests
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use fixtures from `conftest.py`
- Mock external dependencies

### Test Structure
```python
class TestMyFeature:
    """Tests for MyFeature."""

    def test_basic_functionality(self, test_config):
        """Test basic functionality."""
        # Arrange
        obj = MyFeature(test_config)

        # Act
        result = obj.do_something()

        # Assert
        assert result == expected
```

## Reporting Issues

Use the issue templates:
- **Bug Report**: For bugs and errors
- **Feature Request**: For new features or enhancements

Include:
- Clear description
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details
- Error messages/logs
- Screenshots if applicable

## Project Structure

```
transcription-and-summary/
├── src/                    # Source code
│   ├── audio_capture.py    # Audio recording
│   ├── transcription.py    # Speech-to-text
│   ├── summarization.py    # AI summarization
│   ├── google_docs.py      # Google Docs integration
│   ├── web_ui.py           # Web interface
│   └── ...
├── tests/                  # Test suite
│   ├── test_config.py
│   ├── test_audio_capture.py
│   └── ...
├── .github/                # GitHub templates
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── config.yaml             # Configuration
├── requirements.txt        # Dependencies
├── Makefile               # Development commands
└── pyproject.toml         # Tool configuration
```

## Getting Help

- Check existing issues and PRs
- Read the documentation
- Ask questions in issue comments
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## Recognition

Contributors will be acknowledged in release notes and the README.

Thank you for contributing! 🎉
