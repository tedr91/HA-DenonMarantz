# Changelog

All notable changes to this project will be documented in this file.

## 1.0.3 - 2026-06-14

### Added

- The "Active speakers" sensor (with its computed `layout` attribute) is now part of the default entity set and no longer requires the "Add Extended Entities" option.
- Help text for the "Add Extended Entities" option explaining what it adds and noting the potential performance impact of the extra polling.

### Changed

- The "Input Filter" option now uses a chip-style picker (like the "Add Label" UI): choose input sources from a dropdown populated with the receiver's actual sources, or type your own.
- Input source filtering is now an exact, case-insensitive match against the selected sources instead of a partial substring match.
- In the Options dialog, "Add Extended Entities" now appears below "Input Filter".

## 1.0.2 - 2026-06-13

### Added

- New read-only "Active speakers" sensor (extended entities) that reports the channels currently active for the present surround mode, queried via the `CV?` (Channel Volume) command.
- The Active speakers sensor exposes `channels` (raw channel codes), `speaker_count`, and a computed `layout` attribute (e.g. `5.1.2`) derived from the active bed, subwoofer, and height channels.

## 1.0.1 - 2026-06-13

### Fixed

- Corrected a consistent 1-unit volume offset by mapping the Denon/Marantz absolute `MV` value on a 0–100 scale instead of 0–98, so the reported volume matches the receiver's displayed value.

## 1.0.0 - 2026-04-09

### Added

- Local Home Assistant brand assets for the Denon Marantz integration, including icon, logo, dark variants, and @2x variants.

### Changed

- Promoted the integration and Python package version to 1.0.0.
- Documented bundled branding assets and their source wordmarks in the README.

### Notes

- Branding assets combine Denon and Marantz wordmarks so the integration is recognizable for both receiver families.
