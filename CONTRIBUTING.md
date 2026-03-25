# Contributing to ComCan

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/ComCan.git
cd ComCan
python -m venv venv
venv\Scripts\activate   # Windows
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Security Checks

```bash
bandit -r comcan/ -ll
```

## Code Style

- Python 3.9+ compatible
- Type hints on all public functions
- Docstrings on all public functions (Google style)

## Pull Request Process

1. Fork the repo and create a branch from `main`
2. Add tests for any new functionality
3. Ensure all tests pass and Bandit reports zero issues
4. Submit a PR with a clear description of changes
