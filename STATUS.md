# Project Status

## Current Version: 0.2.0

### ✅ Working

- **REST API polling** — temperature data fetched every 60 seconds (configurable)
- **Temperature sensors** — one per channel, named from FireBoard app labels
- **Alert threshold sensors** — `alert_max` and `alert_min` entities created automatically for channels with active alerts
- **Dynamic entity registration** — new channels and alerts appear within one poll cycle, no reload required
- **Dynamic sensor naming** — channel renames in the FireBoard app reflect in HA automatically
- **Binary sensors** — connectivity and battery low
- **Config flow** — UI setup with email/password/polling interval
- **GitHub Actions CI** — tests, linting, type checking

### ❌ Not Supported

- Write operations (setting target temperatures, controlling the pellet drive, etc.)

### 🧪 Tested With

- **FireBoard Pellet Drive (FBXPD)** — the only device this integration has been tested against. Other FireBoard models (2 Pro, Spark, etc.) use the same cloud API and should work, but are untested.

### 📋 Known Limitations

- Temperatures only update on poll interval (default 60s), not in real time
- `current_temp` is only present in the API response for channels with an active probe reading; channels with no probe show as `unknown`
- Battery sensor only created for devices that report `has_battery: true`

---

**Last Updated:** June 2026
**Version:** 0.2.0
**Repo:** <https://github.com/unibrain1/ha-fireboard>
