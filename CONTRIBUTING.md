# Contributing to TrafficPredictor

Thank you for your interest in contributing to TrafficPredictor! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

## Code of Conduct

Be respectful, inclusive, and professional when interacting with the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/TrafficPredictor.git`
3. Add the upstream remote: `git remote add upstream https://github.com/vinhky123/TrafficPredictor.git`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Make (optional, but recommended)

### Backend Setup

```bash
# Create virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Install dev dependencies
pip install pytest pytest-cov ruff mypy
```

### Frontend Setup

```bash
cd web
npm install
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

## Making Changes

1. **Keep commits focused**: Each commit should address a single concern
2. **Write clear commit messages**: Follow conventional commits format
3. **Update tests**: Add or update tests for your changes
4. **Update documentation**: Document any new features or changes

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer(s)]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(backend): add caching layer to segment mapping

- Implement LRU cache for DynamoDB segment lookups
- Add cache TTL configuration
- Add cache hit/miss metrics

Closes #123
```

## Submitting Changes

1. Push your branch: `git push origin feature/your-feature-name`
2. Open a Pull Request against `main`
3. Fill out the PR template
4. Wait for CI checks to pass
5. Address review comments

### PR Requirements

- [ ] Tests pass
- [ ] Linting passes
- [ ] Documentation updated
- [ ] Description of changes provided
- [ ] Related issues linked

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints where possible
- Maximum line length: 120 characters
- Use docstrings for functions and classes

```python
def calculate_speed(distance: float, time: float) -> float:
    """Calculate speed in km/h.

    Args:
        distance: Distance in kilometers.
        time: Time in hours.

    Returns:
        Speed in km/h.
    """
    if time == 0:
        return 0.0
    return distance / time
```

### TypeScript/React

- Use functional components with hooks
- Define proper types for props
- Use async/await for async operations
- Follow the existing component structure

```typescript
interface Props {
  segmentId: number;
  onSpeedUpdate: (speed: number) => void;
}

export function SpeedDisplay({ segmentId, onSpeedUpdate }: Props) {
  const [speed, setSpeed] = useState<number>(0);

  useEffect(() => {
    fetchSpeed(segmentId).then(setSpeed);
  }, [segmentId]);

  return <div>{speed} km/h</div>;
}
```

### Terraform

- Use consistent naming conventions
- Add descriptions for variables and outputs
- Format with `terraform fmt`
- Validate with `terraform validate`

## Testing

### Running Tests

```bash
# All backend tests
make backend-test

# Specific test file
pytest tests/unit/test_schemas.py -v

# With coverage
pytest tests/ --cov=backend --cov-report=html
```

### Writing Tests

- Write tests for new features
- Maintain test coverage above 80%
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)

```python
def test_get_current_speed_returns_kmh(self):
    """Test that speed is correctly converted to km/h."""
    # Arrange
    repo = MockRepository()
    repo.add_speed(10.0)  # 10 m/s

    # Act
    service = TrafficService(repo=repo, mapper=MockMapper())
    speed = service.get_current_speed_kmh(1)

    # Assert
    assert speed == 36.0  # 10 m/s = 36 km/h
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update API documentation for endpoint changes
- Include examples for new features

## Questions?

Feel free to open an issue for questions or join discussions in existing issues.