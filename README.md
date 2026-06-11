# Home Assistant FireBoard Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Home Assistant integration for FireBoard wireless thermometers using direct cloud API communication.

> **Forked from**: [GarthDB/ha-fireboard](https://github.com/GarthDB/ha-fireboard)  
> **This fork**: [unibrain1/ha-fireboard](https://github.com/unibrain1/ha-fireboard)

## What's Different in This Fork

The following fixes and improvements were made on top of the original GarthDB integration:

### Bug Fix: Temperatures Always Showing as Unknown
The original integration relied on MQTT for temperature data. When MQTT was unavailable (which is typical), all temperature sensors showed `Unknown`. The fix extracts `current_temp` from the REST API channel data directly, so polling alone provides temperatures without requiring MQTT.

### Alert Threshold Sensors
Dedicated sensor entities are now created for FireBoard alert thresholds set in the FireBoard app. For each channel with an active alert, new entities appear automatically:
- `sensor.<device>_<channel>_alert_max` — maximum temperature alert threshold
- `sensor.<device>_<channel>_alert_min` — minimum temperature alert threshold (if set)

These can be used in automations and dashboard cards.

### Dynamic Entity Registration
New channels, probes, and alerts added in the FireBoard app appear in Home Assistant automatically within one polling cycle — no reload required.

### Dynamic Sensor Naming
Temperature and alert sensor names reflect the custom labels set in the FireBoard app. Renaming a probe in the FireBoard app updates the entity name in Home Assistant within one polling cycle.

### Configurable Polling Interval
The polling interval is now set during integration setup and defaults to **60 seconds**. The minimum is 60 seconds to respect FireBoard's API rate limit.

---

## Features

- **Temperature Monitoring**: Real-time temperature readings from all channels via REST API polling
- **Alert Threshold Sensors**: Dedicated entities for min/max alert thresholds set in the FireBoard app
- **Multiple Devices**: Support for FireBoard 2 Pro, Spark, Pellet, and other models
- **Battery Monitoring**: Track battery levels on wireless devices
- **Connectivity Status**: Binary sensor for device online/offline state
- **Cloud API**: Uses the official FireBoard Cloud API — no MQTT broker required
## Supported Devices

- **FireBoard 2 Pro**: 6-channel WiFi thermometer
- **FireBoard Spark**: Portable instant-read thermometer with leave-in probe
- **FireBoard Pellet (FBXPD)**: Pellet grill controller with integrated thermometer
- **Other FireBoard Models**: Any device compatible with FireBoard Cloud

## Installation

1. Copy the `custom_components/fireboard/` directory to your Home Assistant config directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration** and search for **FireBoard**

## Configuration

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **FireBoard**
4. Enter your FireBoard account credentials:
   - **Email**: Your FireBoard account email
   - **Password**: Your FireBoard account password
   - **Polling Interval**: How often to fetch data (default: 60 seconds)

> The minimum polling interval is 60 seconds to stay within FireBoard's API rate limit of 200 calls/hour.

## Entities

### Temperature Sensors
- One sensor per channel (up to 7 per device depending on model)
- Named from the custom label set in the FireBoard app (e.g. `sensor.ike_meat_probe_1`)
- Device class: `temperature` | Unit: Fahrenheit (°F)
- Attributes: `channel`, `label`, `target_temp`

### Alert Threshold Sensors
- Created automatically for channels that have active alerts configured in the FireBoard app
- Named `<device> <channel label> Alert Max` / `Alert Min`
- Device class: `temperature` | Unit: Fahrenheit (°F)
- Shows `unavailable` when the alert is disabled or removed

### Battery Sensors
- Battery level percentage for wireless devices
- Device class: `battery` | Unit: Percent (%)

### Binary Sensors
- **Connectivity**: Device online/offline status
- **Battery Low**: Alert when battery is below threshold

## Dashboard Examples

### Temperature with ApexCharts Gauge

Requires [custom:apexcharts-card](https://github.com/RomRider/apexcharts-card) from HACS.

Shows the meat probe temperature as a gauge that fills toward 250°F, with dynamic color zones based on the alert threshold set in the FireBoard app. The card hides automatically when the device goes offline.

```yaml
type: conditional
conditions:
  - condition: state
    entity: binary_sensor.ike_connectivity
    state: "on"
card:
  type: custom:apexcharts-card
  chart_type: radialBar
  header:
    title: Meat Probe
    show: true
    show_states: true
    colorize_states: true
  apex_config:
    colors:
      - |
        [[[
          const temp = Number(states['sensor.ike_meat_probe_1'].state);
          const alertState = states['sensor.kitchen_ike_meat_probe_1_alert_max'];
          const alertMax = alertState && alertState.state !== 'unavailable' && alertState.state !== 'unknown'
            ? Number(alertState.state) : NaN;
          if (isNaN(alertMax)) return '#4caf50';
          if (temp >= alertMax) return '#f44336';
          if (temp >= alertMax - 10) return '#ff9800';
          return '#4caf50';
        ]]]
    plotOptions:
      radialBar:
        startAngle: -135
        endAngle: 135
        hollow:
          size: '60%'
        dataLabels:
          name:
            show: false
          value:
            show: true
            fontSize: '22px'
            formatter: "EVAL:function(val) { return val.toFixed(0) + '%'; }"
    stroke:
      lineCap: round
  series:
    - entity: sensor.ike_meat_probe_1
      name: Meat Probe
      max: 250
```

Color logic:
- **Green** — normal, or no alert configured
- **Orange** — within 10°F of the alert max threshold
- **Red** — at or above the alert max threshold

### Simple Temperature Card

```yaml
type: entities
title: FireBoard Temperatures
entities:
  - entity: sensor.ike_meat_probe_1
    name: Meat Probe
  - entity: sensor.ike_pit
    name: Pit Temp
  - entity: sensor.ike_pit_2
    name: Pit 2
```

### Automation: Temperature Alert Using FireBoard Alert Sensor

```yaml
automation:
  - alias: "FireBoard: Meat Probe Approaching Target"
    trigger:
      - platform: template
        value_template: >
          {{ states('sensor.ike_meat_probe_1') | float >
             state_attr('sensor.kitchen_ike_meat_probe_1_alert_max', 'state') | float - 10 }}
    action:
      - service: notify.notify
        data:
          title: "FireBoard: Almost There"
          message: >
            Meat probe is at {{ states('sensor.ike_meat_probe_1') }}°F,
            approaching target of {{ states('sensor.kitchen_ike_meat_probe_1_alert_max') }}°F
```

### Automation: Device Offline Alert

```yaml
automation:
  - alias: "FireBoard: Device Offline"
    trigger:
      - platform: state
        entity_id: binary_sensor.ike_connectivity
        to: "off"
        for:
          minutes: 5
    action:
      - service: notify.notify
        data:
          title: "FireBoard Offline"
          message: "FireBoard has been offline for 5 minutes"
```

## Troubleshooting

### Temperatures Showing as Unknown
- Ensure the device is active in the FireBoard app with a live session
- Check the device is online (`binary_sensor.<device>_connectivity`)
- The REST API only returns `current_temp` for channels with active probe readings

### Authentication Errors
- Verify credentials at https://fireboard.io
- Ensure the email matches your FireBoard account exactly

### Rate Limit Errors
- Increase the polling interval in the integration options
- Default 60 seconds = 60 calls/hour, well within the 200 calls/hour limit
- If you have multiple HA instances they share the same rate limit

### Devices Not Showing Up
- Ensure devices are online in the FireBoard app
- Restart Home Assistant after adding the integration
- Check HA logs for errors under `custom_components.fireboard`

## Project Structure

```
ha-fireboard/
├── custom_components/
│   └── fireboard/
│       ├── __init__.py          # Integration setup
│       ├── api_client.py        # FireBoard Cloud API client
│       ├── config_flow.py       # UI configuration wizard
│       ├── const.py             # Constants and defaults
│       ├── coordinator.py       # Data update coordinator
│       ├── entity.py            # Base entity class
│       ├── sensor.py            # Temperature + alert sensors
│       ├── binary_sensor.py     # Connectivity + battery sensors
│       ├── manifest.json        # Integration metadata
│       └── strings.json         # UI strings
└── tests/                       # Test suite
```

## Changelog

### v0.2.0
- **Fix**: Temperatures no longer show as Unknown — `current_temp` now read from REST API directly
- **New**: Alert threshold sensors (`alert_max`, `alert_min`) created automatically per channel
- **New**: Dynamic entity registration — new channels and alerts appear without reload
- **New**: Dynamic sensor naming — probe renames in the FireBoard app reflect in HA automatically
- **Change**: Default polling interval updated to 60 seconds (was 40)
- **Change**: Minimum polling interval updated to 60 seconds

### v0.1.0
- Initial release (GarthDB)
- Direct FireBoard Cloud API integration
- UI-based configuration
- Temperature sensor support
- Battery monitoring
- Connectivity status
- Manual installation

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original integration by [@GarthDB](https://github.com/GarthDB/ha-fireboard)
- Based on the [fireboard2mqtt](https://github.com/gordlea/fireboard2mqtt) project
- Uses the official FireBoard Cloud API
