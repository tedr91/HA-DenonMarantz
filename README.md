# HA-DenonMarantz

Home Assistant custom integration for Denon and Marantz AV receivers based on the Denon AVR command protocol.

## MVP entities

- `media_player.denon_marantz_avr`
  - Power (`PW`)
  - Volume + mute (`MV`, `MU`)
  - Source select (`SI`)
- `select.denon_marantz_avr_sound_mode`
  - Sound mode selection (`MS`)
- `select.denon_marantz_avr_input_source`
  - Input source selection (`SI`)
  - Dynamically populated from AVR source metadata when available
  - Falls back to default source list if metadata query is unavailable

## Project structure

```text
custom_components/
  denon_marantz/
    __init__.py
    brand/
      icon.png
      icon@2x.png
      dark_icon.png
      dark_icon@2x.png
      logo.png
      logo@2x.png
      dark_logo.png
      dark_logo@2x.png
    manifest.json
    config_flow.py
    const.py
    coordinator.py
    denon_protocol.py
    media_player.py
    strings.json
    translations/
      en.json
```

## Branding

This integration includes local Home Assistant brand assets in `custom_components/denon_marantz/brand/`.
The square icon and landscape logo combine Denon and Marantz wordmarks so the integration is recognizable for both receiver families.

The composed assets were derived from the Wikimedia Commons `Denon logo.svg` and `Marantz logo.svg` text-logo files.
Denon and Marantz remain trademarks of their respective owners.

## Local install in Home Assistant

1. Copy `custom_components/denon_marantz` into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services**.
4. If your AVR advertises SSDP, Home Assistant should offer it automatically for confirmation.
5. You can still use **Add Integration** and search for **Denon Marantz AVR** to enter host/port manually.

## Notes

- Default AVR control port is typically `23` (telnet-like protocol).
- This is an MVP scaffold intended as a base for protocol expansion.
- Polling uses last-known-state fallback during transient connection failures.

## Registry identity migration

Existing installations migrate from host- and config-entry-based registry identities
to the receiver's normalized model and serial number. Entity unique IDs migrate before
the device identifier, preserving entity IDs, device names, areas, labels, and config
entry titles. Duplicate stale rows are removed only when a current entity already owns
the stable target identity.

Manual, SSDP, and DHCP setup now confirm the same hardware identity over the receiver's
HTTP API before creating an entry. This prevents a DHCP address change from offering the
same receiver as a new integration. If an existing receiver is offline during migration,
Home Assistant leaves the entry unchanged and retries on a later restart.
