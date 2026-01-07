# Contributing to MadyStripe

First off, thank you for considering contributing to MadyStripe! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/MadyStripe.git
   cd MadyStripe
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/NullMeDev/MadyStripe.git
   ```

## How to Contribute

### Types of Contributions

- 🐛 **Bug Fixes**: Fix issues and bugs
- ✨ **Features**: Add new features or gateways
- 📚 **Documentation**: Improve or add documentation
- 🧪 **Tests**: Add or improve tests
- 🎨 **Code Quality**: Refactoring and improvements

### Contribution Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow the style guidelines
   - Add tests if applicable

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new gateway support"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Go to GitHub and create a PR
   - Fill out the PR template
   - Wait for review

## Development Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### 3. Set Up Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your test credentials
```

### 5. Run Tests

```bash
python -m pytest tests/
```

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] No sensitive data in commits
- [ ] Commit messages follow convention

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No breaking changes
```

### Review Process

1. Maintainers will review your PR
2. Address any requested changes
3. Once approved, PR will be merged

## Style Guidelines

### Python Code Style

- Follow PEP 8
- Use type hints where possible
- Maximum line length: 100 characters
- Use meaningful variable names

```python
# Good
def check_card(card_number: str, gateway_id: int = 1) -> tuple:
    """
    Check a card using the specified gateway.
    
    Args:
        card_number: Card in format XXXX|MM|YY|CVV
        gateway_id: Gateway to use (default: 1)
    
    Returns:
        Tuple of (status, message, card_type)
    """
    pass

# Bad
def chk(c, g=1):
    pass
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new Shopify gateway
fix: resolve timeout issue in checkout
docs: update README with new examples
test: add unit tests for gateway manager
refactor: simplify error handling
```

### Documentation

- Use docstrings for all public functions
- Update README for new features
- Add examples where helpful

## Reporting Bugs

### Before Reporting

1. Check existing issues
2. Try the latest version
3. Gather relevant information

### Bug Report Template

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. ...

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10]
- Version: [e.g., 1.0.0]

## Additional Context
Any other relevant information
```

## Suggesting Features

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives Considered
Other approaches you've thought about

## Additional Context
Any other relevant information
```

## Questions?

- **Telegram**: [@MissNullMe](https://t.me/MissNullMe)
- **GitHub Issues**: For bugs and features
- **GitHub Discussions**: For questions

---

Thank you for contributing! 🙏
