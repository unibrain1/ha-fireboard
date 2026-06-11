# FireBoard Integration - Quick Start

## Prerequisites

- Home Assistant instance with `custom_components` support
- FireBoard account with at least one active device
- Device must have an active session in the FireBoard app (so `current_temp` values are present in the API)

---

## Step 1: Copy Integration Files

```bash
cp -r custom_components/fireboard /config/custom_components/
```

Adjust the path if your HA config directory is elsewhere (e.g. `~/.homeassistant/custom_components/`).

---

## Step 2: Restart Home Assistant

**Via UI**: Settings → System → Restart

**Via command line**:
```bash
# Home Assistant OS
ha core restart

# Docker
docker restart homeassistant
```

---

## Step 3: Add the Integration

1. Go to **Settings → Devices & Services**
2. Click **+ Add Integration**
3. Search for **FireBoard**
4. Enter your credentials:
   - **Email**: Your FireBoard account email
   - **Password**: Your FireBoard account password
   - **Polling Interval**: 60 seconds (default — leave as-is)
5. Click **Submit**

---

## Step 4: Verify Entities

After a successful setup, check **Developer Tools → States** and search for your grill's name (as set in the FireBoard app) to find your entities. Entity IDs are generated dynamically from your device name and channel labels — nothing is hardcoded in the integration.

The pattern is `sensor.<grill_name>_<channel_label>`. The examples below use "ike" as the grill name — substitute your own.

| Entity type | Example (grill named "ike") | Notes |
|---|---|---|
| Temperature sensor | `sensor.ike_meat_probe_1` | One per channel with an active reading |
| Alert max sensor | `sensor.kitchen_ike_meat_probe_1_alert_max` | Only for channels with an active alert |
| Connectivity | `binary_sensor.ike_connectivity` | `on` = device online |
| Battery | `sensor.ike_battery` | Only for devices with a battery |

Channels with no probe inserted will show `unknown` — this is expected.

---

## Step 5: Check Temperature Updates

1. Note a current temperature value
2. Wait 60 seconds
3. Refresh — the value should update

---

## Step 6: Enable Debug Logging (if needed)

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.fireboard: debug
```

Then restart HA and check `home-assistant.log` for detailed output.

---

## Troubleshooting

### Integration not appearing in UI
- Clear browser cache or try an incognito window
- Verify `custom_components/fireboard/manifest.json` exists
- Check HA logs for Python import errors

### Temperatures showing as Unknown
- Confirm the device has an active session in the FireBoard app
- Check that probes are physically inserted
- Verify the device is online in the FireBoard app

### Authentication fails
- Test credentials at https://fireboard.io
- Check HA logs for the specific error

### Rate limit errors
- Increase the polling interval (remove and re-add the integration to change it)
- Default 60s = 60 calls/hour, well within the 200/hour limit
