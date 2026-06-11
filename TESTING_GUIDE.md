# FireBoard Integration - Testing Guide

## Prerequisites

- Home Assistant instance running
- FireBoard account with at least one active device and session
- Integration installed (see QUICK_START.md)

## Installation

```bash
cp -r custom_components/fireboard /config/custom_components/
# Restart HA, then add the integration via Settings → Devices & Services
```

---

## Configuration Tests

### Test 1: Authentication

Enter credentials in the config flow and click Submit.

**Pass**: "Configuration successful", taken to device list  
**Fail**: Check logs for specific error — bad credentials return "Invalid email or password"

### Test 2: Device Discovery

After configuration, verify devices appear under the integration.

**Pass**: One device entry per FireBoard device on your account  
**Fail**: Check HA logs in debug mode for API response details

---

## Sensor Tests

### Test 3: Temperature Sensors

For each active channel, a `sensor.<device>_<label>` entity should exist.

- Value matches the FireBoard app (within a few degrees)
- Unit is °F
- `channel` attribute shows the channel number
- `label` attribute shows the custom name from the FireBoard app
- Updates within 60 seconds

**Channels with no probe inserted**: show `unknown` — expected behavior.

### Test 4: Alert Threshold Sensors

For channels with alerts configured in the FireBoard app:

- `sensor.<device>_<label>_alert_max` shows the max threshold (e.g. 165.0°F)
- `sensor.<device>_<label>_alert_min` shows the min threshold (if set)
- Adding a new alert in the app → sensor appears in HA within 60 seconds (no reload needed)
- Renaming a channel in the app → sensor name updates in HA within 60 seconds

### Test 5: Channel Label Updates

1. Rename a channel in the FireBoard app
2. Wait up to 60 seconds
3. Verify the entity's friendly name updates in HA

### Test 6: Connectivity Sensor

`binary_sensor.<device>_connectivity`

- Should be `on` when device is online
- Turn off the FireBoard device, wait 60 seconds → should change to `off`
- Turn it back on, wait 60 seconds → should recover to `on`

### Test 7: Battery Sensor (wireless devices only)

`sensor.<device>_battery`

- Shows 0–100%
- Matches the FireBoard app reading

---

## Error Handling Tests

### Test 8: Invalid Credentials

Remove and re-add the integration with a wrong password.  
**Pass**: Clear "Invalid email or password" error in the config flow UI

### Test 9: Network Interruption

Disconnect internet while integration is running, wait 60 seconds, reconnect.  
**Pass**: Errors appear in logs, integration recovers automatically within one poll cycle

### Test 10: Token Expiration

Let the integration run for several hours.  
**Pass**: Continues working seamlessly — re-authentication happens transparently

---

## Dashboard Test

> Entity IDs are derived from your grill's name and channel labels in the FireBoard app. The examples below use "ike" — replace with your own grill name. Find exact IDs in **Developer Tools → States**.

Create a quick entities card to verify display:

```yaml
type: entities
title: FireBoard
entities:
  - entity: sensor.ike_meat_probe_1
  - entity: sensor.kitchen_ike_meat_probe_1_alert_max
  - entity: sensor.ike_pit
  - entity: binary_sensor.ike_connectivity
```

All entities should display values and update every 60 seconds.

---

## Automation Test

```yaml
automation:
  - alias: "Test FireBoard trigger"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ike_meat_probe_1
        above: 100
    action:
      - service: persistent_notification.create
        data:
          message: "FireBoard automation works!"
```

Heat a probe above 100°F and verify the notification appears.

---

## Log Reference

```bash
# Live logs filtered to FireBoard
tail -f /config/home-assistant.log | grep -i fireboard

# Errors only
grep -i "error" /config/home-assistant.log | grep -i fireboard
```

---

## Rate Limit Check

Default 60s interval = 60 API calls/hour. FireBoard allows 200/hour.  
If you see 429 errors, increase the polling interval by removing and re-adding the integration.
