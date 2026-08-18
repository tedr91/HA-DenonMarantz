from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "custom_components" / "denon_marantz" / "migration.py"
)
SPEC = importlib.util.spec_from_file_location("denon_marantz_migration", MIGRATION_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MIGRATION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATION)


def test_normalizes_model_and_serial() -> None:
    assert MIGRATION.normalize_identity(" AVR-X 4800H ") == "avr-x4800h"
    assert MIGRATION.stable_id("AVR-X4800H", " AB 123 ") == "avr-x4800h-ab123"
    assert MIGRATION.stable_id(None, "AB123") == "ab123"
    assert MIGRATION.stable_id("AVR-X4800H", "") is None


def test_migrates_media_player_and_suffix_entities() -> None:
    assert MIGRATION.migrated_unique_id("media_player", "entry", "entry", "stable") == "stable"
    assert (
        MIGRATION.migrated_unique_id("sensor", "entry_active_speakers", "entry", "stable")
        == "stable_active_speakers"
    )
    assert (
        MIGRATION.migrated_unique_id("button", "entry_control_up", "entry", "stable")
        == "stable_control_up"
    )


def test_mapping_is_idempotent_and_domain_sensitive() -> None:
    assert MIGRATION.migrated_unique_id("media_player", "stable", "entry", "stable") is None
    assert MIGRATION.migrated_unique_id("sensor", "stable_media_player", "entry", "stable") is None
    assert MIGRATION.migrated_unique_id("light", "entry_power", "entry", "stable") is None
    assert MIGRATION.migrated_unique_id("sensor", "entry_", "entry", "stable") is None


def test_detects_host_based_config_entry_ids() -> None:
    assert MIGRATION.is_legacy_unique_id("192.168.1.20")
    assert MIGRATION.is_legacy_unique_id("receiver.local")
    assert not MIGRATION.is_legacy_unique_id("avr-x4800h-ab123")
    assert not MIGRATION.is_legacy_unique_id(None)


def test_identity_probe_uses_supported_denonavr_fields() -> None:
    class FakeDenonAVR:
        def __init__(self, host: str, timeout: float) -> None:
            self.host = host
            self.timeout = timeout
            self.model_name = "AVR-X4800H"
            self.serial_number = "AB123"
            self.name = "Media Room AVR"
            self.manufacturer = "Denon"

        async def async_setup(self) -> None:
            return None

    denonavr = types.ModuleType("denonavr")
    denonavr.DenonAVR = FakeDenonAVR
    package = types.ModuleType("custom_components.denon_marantz")
    package.__path__ = [str(MIGRATION_PATH.parent)]

    old_denonavr = sys.modules.get("denonavr")
    old_package = sys.modules.get("custom_components.denon_marantz")
    sys.modules["denonavr"] = denonavr
    sys.modules["custom_components.denon_marantz"] = package
    sys.modules["custom_components.denon_marantz.migration"] = MIGRATION
    try:
        identity_path = MIGRATION_PATH.with_name("identity.py")
        spec = importlib.util.spec_from_file_location(
            "custom_components.denon_marantz.identity", identity_path
        )
        assert spec is not None
        assert spec.loader is not None
        identity_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = identity_module
        spec.loader.exec_module(identity_module)

        import asyncio

        identity = asyncio.run(identity_module.async_probe_identity("receiver.local"))
        assert identity.stable_id == "avr-x4800h-ab123"
        assert identity.name == "Media Room AVR"
        assert identity.manufacturer == "Denon"
        assert identity.model == "AVR-X4800H"
        assert identity.serial == "AB123"
    finally:
        sys.modules.pop("custom_components.denon_marantz.identity", None)
        if old_denonavr is None:
            sys.modules.pop("denonavr", None)
        else:
            sys.modules["denonavr"] = old_denonavr
        if old_package is None:
            sys.modules.pop("custom_components.denon_marantz", None)
        else:
            sys.modules["custom_components.denon_marantz"] = old_package
