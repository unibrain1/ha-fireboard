# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A Home Assistant custom integration for FireBoard wireless thermometers. It polls the FireBoard Cloud REST API and exposes temperature sensors, alert threshold sensors, connectivity, and battery status as HA entities.

The running instance lives at `/Volumes/config/custom_components/fireboard/` on a Raspberry Pi (mounted over the network). After editing code, copy changed files there and reload the integration in HA — a full restart is only needed for new entity classes or dependency changes.

## Commands

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run a single test file
pytest tests/test_api_client.py

# Run a single test
pytest tests/test_api_client.py::test_authenticate_success

# Format and lint
black custom_components/fireboard tests/
isort custom_components/fireboard tests/
flake8 custom_components/fireboard tests/
mypy custom_components/fireboard/

# Coverage report
pytest --cov=custom_components/fireboard --cov-report=html
open htmlcov/index.html
```

Tests require 80% coverage (`--cov-fail-under=80` in pyproject.toml). The `asyncio_mode = "auto"` setting means async test functions work without decorators.

## Architecture

### Data flow

```
Config Flow → creates ConfigEntry (email, password, polling_interval)
                ↓
FireBoardDataUpdateCoordinator  ←  polls every 60s (default)
  └── FireBoardApiClient            GET /api/v1/devices.json
        └── authenticates via       POST /api/rest-auth/login/
                                    (token + session cookies)
                ↓
    coordinator.data = {
      device_uuid: {
        "device_info": <full device dict from API>,
        "channels":    [...],
        "latest_temps": [...],
        "online": True
      }
    }
                ↓
async_setup_entry listener   ← fires on every coordinator update
  └── creates new entities for new channels/alerts (tracked by unique_id set)
```

### Entity registration pattern

`sensor.py` uses a coordinator listener instead of a one-shot setup, so new channels and alerts discovered on subsequent polls get entities created without a reload:

```python
tracked: set[str] = set()

@callback
def _add_new_entities() -> None:
    # checks tracked set, appends only new entities
    ...

_add_new_entities()                        # run once at setup
coordinator.async_add_listener(_add_new_entities)  # run on every update
```

### Key files

| File | Responsibility |
|---|---|
| `coordinator.py` | Polls API, owns `coordinator.data`, handles auth lifecycle |
| `api_client.py` | HTTP calls, session cookies, CSRF token, custom exceptions |
| `sensor.py` | Temperature, alert threshold (max/min), and battery sensors |
| `binary_sensor.py` | Connectivity and battery-low sensors |
| `entity.py` | Base class: `_device_data`, `_temperatures`, `available`, `device_info` |
| `config_flow.py` | Validates credentials, stores `CONF_EMAIL`, `CONF_PASSWORD`, `CONF_POLLING_INTERVAL` |
| `const.py` | `DOMAIN`, `API_BASE_URL`, polling defaults/limits |

### Entity naming

Entity IDs and friendly names are **fully dynamic** — derived from the device `title` and `channel_label` fields returned by the API. Nothing is hardcoded. Renaming a grill or probe in the FireBoard app updates the entity name in HA within one poll cycle.

Pattern: `sensor.<grill_name>_<channel_label>` (e.g. `sensor.smoker_brisket`)

Alert sensors only exist for channels that have an active alert configured in the FireBoard app. They appear/disappear dynamically without a reload.

### API notes

- Auth endpoint is at `/api/rest-auth/login/` (not under `/v1/`)
- Device list with temperatures: `GET /api/v1/devices.json`
- `current_temp` is only present on channels with an active probe reading
- Rate limit: 200 calls/hour. Default 60s polling = ~60 calls/hour.
- On 401: re-authenticate and retry once. On 429: raise `UpdateFailed`.

### Tested hardware

Only tested with the **FireBoard Pellet Drive (model: FBXPD)**. Other models use the same API and should work but are unverified. See `docs/sample_api_response_FBXPD.json` for the full API response shape.

## Deploying to Running HA

```bash
# After editing integration files
cp custom_components/fireboard/<file>.py /Volumes/config/custom_components/fireboard/

# Then in HA UI: Settings → Devices & Services → FireBoard → Reload
# (Full restart only needed when adding new entity classes or changing manifest.json)
```

## GitHub

Remote: `https://github.com/unibrain1/ha-fireboard.git`
