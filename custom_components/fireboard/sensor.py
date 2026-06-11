"""Sensor platform for FireBoard integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FireBoardDataUpdateCoordinator
from .entity import FireBoardEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up FireBoard sensor entities."""
    coordinator: FireBoardDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    tracked: set[str] = set()

    @callback
    def _add_new_entities() -> None:
        new_entities: list[SensorEntity] = []

        for device_uuid, device_data in coordinator.data.items():
            device_info = device_data.get("device_info", {})

            for channel in device_info.get("channels", []):
                channel_number = channel.get("channel")
                if channel_number is None:
                    continue

                temp_uid = f"{device_uuid}_temp_{channel_number}"
                if temp_uid not in tracked:
                    tracked.add(temp_uid)
                    new_entities.append(
                        FireBoardTemperatureSensor(
                            coordinator, device_uuid, channel_number
                        )
                    )

                for alert_type in ("max", "min"):
                    field = f"temp_{alert_type}"
                    has_threshold = any(
                        a.get(field) is not None
                        for a in channel.get("alerts", [])
                        if a.get("enabled")
                    )
                    if has_threshold:
                        alert_uid = f"{device_uuid}_alert_{alert_type}_{channel_number}"
                        if alert_uid not in tracked:
                            tracked.add(alert_uid)
                            new_entities.append(
                                FireBoardAlertSensor(
                                    coordinator, device_uuid, channel_number, alert_type
                                )
                            )

            if device_info.get("has_battery", False):
                battery_uid = f"{device_uuid}_battery"
                if battery_uid not in tracked:
                    tracked.add(battery_uid)
                    new_entities.append(
                        FireBoardBatterySensor(coordinator, device_uuid)
                    )

        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()
    coordinator.async_add_listener(_add_new_entities)


def _channel_label(device_info: dict[str, Any], channel_number: int) -> str:
    """Return the channel label from device info, falling back to 'Channel N'."""
    for ch in device_info.get("channels", []):
        if ch.get("channel") == channel_number:
            return ch.get("channel_label", f"Channel {channel_number}")
    return f"Channel {channel_number}"


class FireBoardTemperatureSensor(FireBoardEntity, SensorEntity):
    """Representation of a FireBoard temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    def __init__(
        self,
        coordinator: FireBoardDataUpdateCoordinator,
        device_uuid: str,
        channel_number: int,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, device_uuid, channel_number)
        self._attr_unique_id = f"{device_uuid}_temp_{channel_number}"

    @property
    def name(self) -> str:
        """Return the sensor name, reflecting any rename in the Fireboard app."""
        device_info = self._device_data.get("device_info", {})
        label = _channel_label(device_info, self._channel_number)
        return f"{self._device_title} {label}"

    def _get_channel_info(self) -> dict[str, Any]:
        """Return merged channel info from REST data and MQTT updates."""
        device_info = self._device_data.get("device_info", {})
        channel_info: dict[str, Any] = {}

        for channel in device_info.get("channels", []):
            if channel.get("channel") == self._channel_number:
                channel_info = {
                    "label": channel.get(
                        "channel_label", f"Channel {self._channel_number}"
                    ),
                    "channel": channel.get("channel"),
                    "current_temp": channel.get("current_temp"),
                }
                break

        for temp_channel in self._temperatures.get("channels", []):
            if temp_channel.get("channel") == self._channel_number:
                channel_info.update(temp_channel)
                break

        return channel_info

    @property
    def native_value(self) -> float | None:
        """Return the temperature value."""
        temp = self._get_channel_info().get("current_temp")
        if temp is not None:
            try:
                return float(temp)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid temperature value for %s: %s", self.name, temp)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        channel_info = self._get_channel_info()
        attributes: dict[str, Any] = {"channel": self._channel_number}

        target_temp = channel_info.get("target_temp")
        if target_temp is not None:
            attributes["target_temp"] = target_temp

        label = channel_info.get("label")
        if label:
            attributes["label"] = label

        return attributes


class FireBoardAlertSensor(FireBoardEntity, SensorEntity):
    """Alert threshold sensor for a FireBoard channel."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT

    def __init__(
        self,
        coordinator: FireBoardDataUpdateCoordinator,
        device_uuid: str,
        channel_number: int,
        alert_type: str,
    ) -> None:
        """Initialize the alert sensor. alert_type is 'max' or 'min'."""
        super().__init__(coordinator, device_uuid, channel_number)
        self._alert_type = alert_type
        self._attr_unique_id = f"{device_uuid}_alert_{alert_type}_{channel_number}"

    @property
    def name(self) -> str:
        """Return the sensor name, reflecting any rename in the Fireboard app."""
        device_info = self._device_data.get("device_info", {})
        label = _channel_label(device_info, self._channel_number)
        suffix = "Alert Max" if self._alert_type == "max" else "Alert Min"
        return f"{self._device_title} {label} {suffix}"

    @property
    def native_value(self) -> float | None:
        """Return the alert threshold value."""
        device_info = self._device_data.get("device_info", {})
        field = f"temp_{self._alert_type}"

        for ch in device_info.get("channels", []):
            if ch.get("channel") == self._channel_number:
                active = next(
                    (
                        a
                        for a in ch.get("alerts", [])
                        if a.get("enabled") and a.get(field) is not None
                    ),
                    None,
                )
                return float(active[field]) if active else None

        return None


class FireBoardBatterySensor(FireBoardEntity, SensorEntity):
    """Representation of a FireBoard battery level sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"

    def __init__(
        self,
        coordinator: FireBoardDataUpdateCoordinator,
        device_uuid: str,
    ) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, device_uuid)
        self._attr_unique_id = f"{device_uuid}_battery"
        self._attr_name = f"{self._device_title} Battery"

    @property
    def native_value(self) -> int | None:
        """Return the battery level."""
        battery_level = self._device_data.get("device_info", {}).get("battery_level")
        if battery_level is not None:
            try:
                return int(battery_level)
            except (ValueError, TypeError):
                _LOGGER.warning(
                    "Invalid battery level for %s: %s", self._attr_name, battery_level
                )
        return None
