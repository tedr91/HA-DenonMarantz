# HA-DenonMarantz

Home Assistant custom integration for Denon and Marantz AV receivers based on the Denon AVR command protocol.

## MVP entities

- `media_player.denon_marantz_avr`
  - Power (`PW`)
  - Volume + mute (`MV`, `MU`)
  - Source select (`SI`)
- `select.denon_marantz_avr_sound_mode`
  - Sound mode selection (`MS`)

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
3. Go to **Settings → Devices & Services**.
4. If your AVR advertises SSDP, Home Assistant should offer it automatically for confirmation.
5. You can still use **Add Integration** and search for **Denon Marantz AVR** to enter host/port manually.

## Notes

- Default AVR control port is typically `23` (telnet-like protocol).
- This is an MVP scaffold intended as a base for protocol expansion.
- Polling uses last-known-state fallback during transient connection failures.
