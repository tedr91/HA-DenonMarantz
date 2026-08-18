from __future__ import annotations


def normalize_identity(value: str) -> str:
    """Normalize a Denon/Marantz identity component."""
    return "".join(value.split()).casefold()


def stable_id(model: str | None, serial: str | None) -> str | None:
    """Build the stable identity used by Home Assistant's Denon integration."""
    normalized_model = normalize_identity(model or "")
    normalized_serial = normalize_identity(serial or "")
    if not normalized_serial:
        return None
    return f"{normalized_model}-{normalized_serial}" if normalized_model else normalized_serial


def is_legacy_unique_id(unique_id: str | None) -> bool:
    """Return whether a config-entry unique ID is host-based."""
    return bool(unique_id and "-" not in unique_id)


def migrated_unique_id(domain: str, unique_id: str, entry_id: str, stable: str) -> str | None:
    """Return a stable replacement for a legacy entity unique ID."""
    if domain == "media_player":
        return stable if unique_id == entry_id else None

    prefix = f"{entry_id}_"
    if domain not in {"button", "select", "sensor", "switch"} or not unique_id.startswith(prefix):
        return None
    suffix = unique_id[len(prefix) :]
    return f"{stable}_{suffix}" if suffix else None
