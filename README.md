# HA-DenonMarantz

Home Assistant custom integration for Denon and Marantz AV receivers based on the Denon AVR command protocol.

## MVP entities

- `media_player.denon_marantz_avr`
  - Power (`PW`)
  - Volume + mute (`MV`, `MU`)
  - Source select (`SI`)
- `select.denon_marantz_avr_sound_mode`
  - Sound mode selection (`MS`)
- Optional zone entities (auto-discovered)
  - `media_player.<name>_zone_2` when Zone2 is supported (`Z2`)
  - `media_player.<name>_zone_3` when Zone3 is supported (`Z3`)
  - Per-zone controls are enabled only when supported by the AVR:
    - Power on/off
    - Volume step
    - Mute
    - Source select

## Project structure

```text
custom_components/
  denon_marantz/
    __init__.py
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

## Local install in Home Assistant

1. Copy `custom_components/denon_marantz` into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration**.
4. Search for **Denon Marantz AVR** and enter host/port.

## Notes

- Default AVR control port is typically `23` (telnet-like protocol).
- This is an MVP scaffold intended as a base for protocol expansion.
