# Development Guide

## Prerequisites

- Python 3.11 or later
- Home Assistant 2023.1.0 or later
- Git
- FireBoard account with at least one active device

## Setup

```bash
git clone https://github.com/unibrain1/ha-fireboard.git
cd ha-fireboard
pip install -r requirements-dev.txt
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=custom_components/fireboard --cov-report=html

# Run a specific file
pytest tests/test_api_client.py

# View coverage report
open htmlcov/index.html
```

## Code Quality

```bash
black custom_components/fireboard tests/
isort custom_components/fireboard tests/
flake8 custom_components/fireboard tests/
mypy custom_components/fireboard/
```

## Installing in Home Assistant

```bash
# Copy to your HA config directory
cp -r custom_components/fireboard /config/custom_components/

# Then restart Home Assistant and add the integration via UI
```

Or use a symlink during active development:

```bash
ln -s $(pwd)/custom_components/fireboard ~/.homeassistant/custom_components/fireboard
```

## Project Structure

```
ha-fireboard/
├── custom_components/fireboard/
│   ├── __init__.py          # Integration setup
│   ├── api_client.py        # FireBoard Cloud API client
│   ├── config_flow.py       # UI configuration wizard
│   ├── const.py             # Constants and defaults
│   ├── coordinator.py       # Data update coordinator (REST polling)
│   ├── entity.py            # Base entity class
│   ├── sensor.py            # Temperature + alert threshold sensors
│   ├── binary_sensor.py     # Connectivity + battery sensors
│   ├── manifest.json        # Integration metadata
│   └── strings.json         # UI strings
├── tests/                   # Test suite
├── requirements-dev.txt     # Development dependencies
├── requirements-test.txt    # Test dependencies
├── pyproject.toml           # Project configuration
└── README.md
```

## Code Standards

- Python 3.11+, type hints everywhere
- Line length: 88 (Black)
- Imports sorted with isort (`profile = "black"`)
- Async/await throughout — no blocking calls on the event loop
- Logging: `debug` for detail, `info` for significant events, `warning` for recoverable issues, `error` for failures

## API Guidelines

- FireBoard rate limit: 200 calls/hour
- Default polling interval: 60 seconds (~60 calls/hour)
- On 401 response: re-authenticate and retry once
- On 429 response: raise `UpdateFailed`, let the coordinator back off

## Debugging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.fireboard: debug
```

## Release Process

1. Update `version` in `manifest.json`
2. Update the `Changelog` section in `README.md`
3. Commit: `git commit -m "chore: release vX.Y.Z"`
4. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
5. Push: `git push && git push --tags`

## Getting Help

- [Issues](https://github.com/unibrain1/ha-fireboard/issues)
- [Home Assistant Community](https://community.home-assistant.io/)
