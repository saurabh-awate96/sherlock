# Contributing to Sherlock

Thank you for your interest in contributing to Sherlock! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/sherlock.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make changes and commit: `git commit -m "feat: description"`
5. Push and create a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance

## Code Style

- Use `ruff` for linting
- Use type hints for all functions
- Write docstrings for public APIs

## Agent Development

When adding new agents:

1. Create the agent in `src/sherlock/agents/`
2. Inherit from the base agent pattern
3. Register in the orchestrator
4. Add tests and documentation

## Questions?

Open an issue for questions or suggestions.
