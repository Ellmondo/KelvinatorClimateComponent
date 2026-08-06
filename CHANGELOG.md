# Changelog

All notable changes to **Kelvinator Climate Component**, relative to
[DotEfekts/ElectroluxClimateComponent](https://github.com/DotEfekts/ElectroluxClimateComponent)
at the point it was forked (master, ~Oct 2025).

## [0.2.0] — 2026-08-06 — Consistent device/entity naming

### Fixed

- **Device name was nondeterministic.** The climate and switch (LED)
  entities for one AC share a device (they resolve to the same physical unit
  via a shared MAC connection), but each reported a *different* name in its
  own `device_info` - the climate entity reported the config entry's title,
  the switch entity reported that title plus `" LED"`. Since the `switch`
  platform loads after `climate`, its name silently won every time,
  leaving every device in the UI named after its LED sub-entity instead of
  something sensible. Both entities now report an identical `device_info`
  (name, manufacturer, suggested area), so the result no longer depends on
  platform load order.

### Changed

- **New naming structure**, matching a "location as Area, generic device
  name, entity domain-prefixed by location" pattern:
  - Device name: **"Air Conditioner"** (was: config entry title, or that
    title + " LED" depending on load order)
  - Area: suggested from the location you enter during setup
  - Climate entity: displays as just the device name ("Air Conditioner"),
    via `has_entity_name` + `name=None`
  - Switch (LED) entity: displays as "Air Conditioner LED", via
    `has_entity_name` + `name="LED"`
  - New installs get entity IDs of the form `climate.<location>_air_conditioner`
    / `switch.<location>_air_conditioner_led`, generated from the location
    you enter during setup
- The config flow's "Name" field is relabelled **"Location"** (e.g. "Living
  Room"), since that's what it actually feeds into now (entry title,
  suggested Area, and the entity ID prefix for new installs). Its default
  value - previously the AC's own OEM-reported device name, which was never
  a sensible location - has been removed; you now have to type one.
- `manufacturer` in the device registry is now "Kelvinator" instead of
  "Electrolux", matching this fork's branding.

### Migration note for existing installs

Home Assistant does not retroactively change an already-registered entity's
`entity_id` just because the code's naming logic changed - only newly
created entities pick up the new `climate.<location>_air_conditioner`
pattern automatically. The **device and entity display names** in the UI
will self-heal on the next restart (since both entities now agree on what to
report) *unless* you'd previously renamed a device manually in the UI, in
which case that manual name takes permanent precedence and needs to be
cleared/reset by hand.

If you want your existing entities' `entity_id`s to match the new pattern
too, that's a one-time manual step per entity: Settings → Devices &
Services → Entities → open the entity → the settings/gear icon → edit
**Entity ID**. Check `automations.yaml`/`scripts.yaml`/your dashboards for
the old entity_id first - Home Assistant does not rewrite raw YAML
references to a renamed entity_id for you.

## [0.1.0] — 2026-08-06 — Initial release

First release under this name. No behavioural change to what the integration
*controls* — same entities, same protocol, same config flow as upstream.
Everything below is either a rename or a robustness/correctness fix, not a
feature change.

### Renamed

- Repository, HACS listing, and the integration's HA display name changed
  from "Electrolux Climate" to **"Kelvinator Climate"**, to match the actual
  branding on the hardware this fork is run against.
- The internal domain (`electrolux_climate`), the `custom_components` folder,
  and all entity IDs were **deliberately left unchanged** — this is a
  cosmetic rename, not a domain migration, so nobody's existing entity IDs,
  automations, or dashboards break by adopting it. See the README's
  ["A note on the rename"](README.md#a-note-on-the-rename) for the reasoning.

### Fixed

1. **Blocking network calls in the event loop.** `climate.py` and `switch.py`
   each independently called `broadlink.discover()` and fetched device status
   directly inside `async_setup_entry`, without an executor job — both
   blocking calls, running on Home Assistant's event loop, twice (once per
   platform), on every startup and reload. Moved this into `__init__.py`,
   run once via `hass.async_add_executor_job`, and shared with both platforms
   through `hass.data`.

2. **No error handling around the poll loop.** `update()` in both entities
   called `self.device.get_status()` with no exception handling. With
   `SCAN_INTERVAL` at 5 seconds, any transient network hiccup — including the
   brief (~1–2s) Wi-Fi disassociate/reassociate cycle these units do every
   few minutes as normal behaviour — raised an unhandled exception straight
   into the log. Both `update()` methods now catch
   `NetworkTimeoutError` / `OSError` / `BroadlinkException`, log at debug
   level, and mark the entity unavailable, the way a well-behaved polling
   entity should. Action methods (`turn_on`, `set_temperature`, etc.) now
   route through a small `_run()` helper that converts the same class of
   error into a clean `HomeAssistantError` instead of a raw traceback in the
   UI if a command happens to land during that reconnect window.

3. **`KeyError` in `switch.py`.** Its `update()` read `state["sn"]` directly;
   `climate.py`'s equivalent already guarded with `"sn" in state`. Applied
   the same guard to `switch.py`.

4. **Cleanup.**
   - Removed `from pickle import NONE` in `config_flow.py` — unused, and not
     a real thing you'd ever want (almost certainly a leftover autocomplete
     mistake for `None`).
   - Replaced a stray `print('DHCP called')` with `_LOGGER.debug(...)`.
   - Switched `climate.py`/`switch.py` from the root logger
     (`logging.info(...)`) to a module-level `_LOGGER`, so log output can be
     filtered per-integration via HA's `logger:` config.
   - Fixed a copy-paste bug in `strings.json` where both the min-temp and
     max-temp config flow labels pointed at the common "Name" translation
     key.

5. **Config entry migration.** `async_migrate_entry` set
   `config_entry.version = 2` and `config_entry.title = "..."` via direct
   attribute assignment, which current Home Assistant core doesn't guarantee
   works. Migration now goes through
   `hass.config_entries.async_update_entry(config_entry, title=..., data=..., version=2)`.

### Also changed

- `async_setup_entry` in `__init__.py` now raises `ConfigEntryNotReady` if
  the initial device discovery fails, so Home Assistant retries setup
  automatically (e.g. if the AC happens to be mid-reconnect at HA startup)
  instead of the entry failing to load for the session.
