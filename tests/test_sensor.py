"""Tests for FireBoard sensor platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature

from custom_components.fireboard.const import DOMAIN


async def test_temperature_sensor_setup(
    hass, mock_coordinator_data, mock_config_entry_data
):
    """Test temperature sensor setup."""
    config_entry = ConfigEntry(
        domain=DOMAIN,
        title="Test",
        data=mock_config_entry_data,
    )

    with patch(
        "custom_components.fireboard.coordinator.FireBoardDataUpdateCoordinator"
    ) as mock_coordinator_class:
        mock_coordinator = AsyncMock()
        mock_coordinator.data = mock_coordinator_data
        mock_coordinator.last_update_success = True
        mock_coordinator_class.return_value = mock_coordinator

        # Store coordinator in hass data
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][config_entry.entry_id] = mock_coordinator

        # Setup sensor platform
        from custom_components.fireboard.sensor import async_setup_entry

        entities = []

        def add_entities(new_entities):
            entities.extend(new_entities)

        await async_setup_entry(hass, config_entry, add_entities)

        # Should create sensors for channels plus battery sensor
        assert len(entities) > 0

        # Check temperature sensors
        temp_sensors = [e for e in entities if "temp" in e.unique_id]
        assert len(temp_sensors) == 3  # 3 channels in mock data


async def test_temperature_sensor_value(
    hass, mock_coordinator_data, mock_config_entry_data
):
    """Test temperature sensor value."""
    from custom_components.fireboard.coordinator import FireBoardDataUpdateCoordinator
    from custom_components.fireboard.sensor import FireBoardTemperatureSensor

    config_entry = ConfigEntry(
        domain=DOMAIN,
        title="Test",
        data=mock_config_entry_data,
    )

    with patch("custom_components.fireboard.coordinator.FireBoardApiClient"):
        coordinator = FireBoardDataUpdateCoordinator(hass, config_entry)
        coordinator.data = mock_coordinator_data
        coordinator.last_update_success = True

        sensor = FireBoardTemperatureSensor(
            coordinator,
            "test-device-uuid-123",
            1,
        )

        assert sensor.native_value == 225.5
        assert sensor.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
        assert sensor.extra_state_attributes["channel"] == 1
        assert sensor.extra_state_attributes["label"] == "Probe 1"
        assert sensor.extra_state_attributes["target_temp"] == 225.0


async def test_temperature_sensor_unavailable(
    hass, mock_coordinator_data, mock_config_entry_data
):
    """Test temperature sensor when device is offline."""
    from custom_components.fireboard.coordinator import FireBoardDataUpdateCoordinator
    from custom_components.fireboard.sensor import FireBoardTemperatureSensor

    config_entry = ConfigEntry(
        domain=DOMAIN,
        title="Test",
        data=mock_config_entry_data,
    )

    # Mark device as offline
    mock_coordinator_data["test-device-uuid-123"]["online"] = False

    with patch("custom_components.fireboard.coordinator.FireBoardApiClient"):
        coordinator = FireBoardDataUpdateCoordinator(hass, config_entry)
        coordinator.data = mock_coordinator_data
        coordinator.last_update_success = True

        sensor = FireBoardTemperatureSensor(
            coordinator,
            "test-device-uuid-123",
            1,
        )

        assert sensor.available is False


async def test_alert_sensor_max(hass, mock_coordinator_data, mock_config_entry_data):
    """FireBoardAlertSensor returns the temp_max threshold for an active alert."""
    from custom_components.fireboard.coordinator import FireBoardDataUpdateCoordinator
    from custom_components.fireboard.sensor import FireBoardAlertSensor

    # Add an active max alert on channel 1
    mock_coordinator_data["test-device-uuid-123"]["device_info"]["channels"][0][
        "alerts"
    ] = [{"enabled": True, "temp_max": 165.0, "temp_min": None}]

    config_entry = ConfigEntry(
        domain=DOMAIN, title="Test", data=mock_config_entry_data
    )

    with patch("custom_components.fireboard.coordinator.FireBoardApiClient"):
        coordinator = FireBoardDataUpdateCoordinator(hass, config_entry)
        coordinator.data = mock_coordinator_data
        coordinator.last_update_success = True

        sensor = FireBoardAlertSensor(
            coordinator, "test-device-uuid-123", 1, "max"
        )

        assert sensor.native_value == 165.0
        assert sensor.native_unit_of_measurement == UnitOfTemperature.FAHRENHEIT
        assert sensor.unique_id == "test-device-uuid-123_alert_max_1"
        assert "Alert Max" in sensor.name


async def test_alert_sensor_min(hass, mock_coordinator_data, mock_config_entry_data):
    """FireBoardAlertSensor returns the temp_min threshold for an active alert."""
    from custom_components.fireboard.coordinator import FireBoardDataUpdateCoordinator
    from custom_components.fireboard.sensor import FireBoardAlertSensor

    mock_coordinator_data["test-device-uuid-123"]["device_info"]["channels"][0][
        "alerts"
    ] = [{"enabled": True, "temp_max": None, "temp_min": 40.0}]

    config_entry = ConfigEntry(
        domain=DOMAIN, title="Test", data=mock_config_entry_data
    )

    with patch("custom_components.fireboard.coordinator.FireBoardApiClient"):
        coordinator = FireBoardDataUpdateCoordinator(hass, config_entry)
        coordinator.data = mock_coordinator_data
        coordinator.last_update_success = True

        sensor = FireBoardAlertSensor(
            coordinator, "test-device-uuid-123", 1, "min"
        )

        assert sensor.native_value == 40.0
        assert "Alert Min" in sensor.name


async def test_alert_sensor_disabled_returns_none(
    hass, mock_coordinator_data, mock_config_entry_data
):
    """FireBoardAlertSensor returns None when no enabled alert matches."""
    from custom_components.fireboard.coordinator import FireBoardDataUpdateCoordinator
    from custom_components.fireboard.sensor import FireBoardAlertSensor

    # Alert exists but is disabled — should not contribute a value
    mock_coordinator_data["test-device-uuid-123"]["device_info"]["channels"][0][
        "alerts"
    ] = [{"enabled": False, "temp_max": 165.0, "temp_min": None}]

    config_entry = ConfigEntry(
        domain=DOMAIN, title="Test", data=mock_config_entry_data
    )

    with patch("custom_components.fireboard.coordinator.FireBoardApiClient"):
        coordinator = FireBoardDataUpdateCoordinator(hass, config_entry)
        coordinator.data = mock_coordinator_data
        coordinator.last_update_success = True

        sensor = FireBoardAlertSensor(
            coordinator, "test-device-uuid-123", 1, "max"
        )

        assert sensor.native_value is None


async def test_alert_sensor_setup_creates_entity_for_active_alert(
    hass, mock_coordinator_data, mock_config_entry_data
):
    """async_setup_entry creates an alert sensor when a channel has an active alert."""
    from custom_components.fireboard.sensor import (
        FireBoardAlertSensor,
        async_setup_entry,
    )

    mock_coordinator_data["test-device-uuid-123"]["device_info"]["channels"][0][
        "alerts"
    ] = [{"enabled": True, "temp_max": 165.0, "temp_min": None}]

    config_entry = ConfigEntry(
        domain=DOMAIN, title="Test", data=mock_config_entry_data
    )

    mock_coordinator = AsyncMock()
    mock_coordinator.data = mock_coordinator_data
    mock_coordinator.last_update_success = True
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = mock_coordinator

    entities = []
    await async_setup_entry(hass, config_entry, lambda new: entities.extend(new))

    alert_entities = [e for e in entities if isinstance(e, FireBoardAlertSensor)]
    assert len(alert_entities) == 1
    assert alert_entities[0].unique_id == "test-device-uuid-123_alert_max_1"


async def test_battery_sensor(hass, mock_coordinator_data, mock_config_entry_data):
    """Test battery sensor."""
    from custom_components.fireboard.coordinator import FireBoardDataUpdateCoordinator
    from custom_components.fireboard.sensor import FireBoardBatterySensor

    config_entry = ConfigEntry(
        domain=DOMAIN,
        title="Test",
        data=mock_config_entry_data,
    )

    with patch("custom_components.fireboard.coordinator.FireBoardApiClient"):
        coordinator = FireBoardDataUpdateCoordinator(hass, config_entry)
        coordinator.data = mock_coordinator_data
        coordinator.last_update_success = True

        sensor = FireBoardBatterySensor(
            coordinator,
            "test-device-uuid-123",
        )

        assert sensor.native_value == 85
        assert sensor.native_unit_of_measurement == "%"
