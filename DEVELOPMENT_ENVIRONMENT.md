# Development Environment Setup

This guide covers setting up a Docker-based Home Assistant environment for testing the integration locally, without affecting your production HA instance.

## Prerequisites

- Docker Desktop with Docker Compose
- FireBoard account credentials

## Quick Start

```bash
# Start Home Assistant in Docker
docker-compose up -d

# Watch logs
docker-compose logs -f homeassistant
```

First startup takes 2–3 minutes. Once running, open http://localhost:8123 and complete the onboarding.

The integration is automatically mounted into the container — any file changes take effect after a container restart.

## Development Workflow

```bash
# After editing integration code, restart HA to reload it
docker-compose restart homeassistant

# Watch for FireBoard log output
docker-compose logs -f homeassistant | grep -E "(fireboard|ERROR)"
```

## Enable Debug Logging

Already configured in `dev-config/configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.fireboard: debug
```

## Reset to Clean State

```bash
docker-compose down
rm -rf dev-config/.storage dev-config/home-assistant.log* dev-config/home-assistant_v2.db*
docker-compose up -d
```

## Installing in Development Container

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration** → search **FireBoard**
3. Enter credentials and polling interval (default 60s)

## Testing Checklist

- [ ] Integration appears in Add Integration UI
- [ ] Authentication succeeds
- [ ] Devices discovered
- [ ] Temperature sensors show values matching FireBoard app
- [ ] Alert threshold sensors appear for channels with active alerts
- [ ] Sensors update every 60 seconds
- [ ] Connectivity sensor changes state when device goes offline
- [ ] No errors in logs during normal operation

## Useful Commands

```bash
# Shell into the container
docker exec -it homeassistant /bin/bash

# Check integration files are mounted
docker exec homeassistant ls -la /config/custom_components/fireboard/

# View current log
docker exec homeassistant cat /config/home-assistant.log | grep fireboard
```

## Docker vs Production

| | Docker | Production |
|---|---|---|
| Safety | Isolated | Risk to production |
| Restart speed | ~2 seconds | ~30 seconds |
| Log access | Easy | Harder |
| Reset | Delete folder | Risky |

Deploy to production only after all Docker tests pass.

## Production Deploy

```bash
# Copy to production (adjust host/path)
scp -r custom_components/fireboard pi@homeassistant.local:/config/custom_components/

# Restart via SSH
ssh pi@homeassistant.local "ha core restart"
```
