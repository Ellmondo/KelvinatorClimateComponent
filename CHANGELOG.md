# Changelog

All notable changes to **Kelvinator Climate Component**, relative to
[DotEfekts/ElectroluxClimateComponent](https://github.com/DotEfekts/ElectroluxClimateComponent)
at the point it was forked (master, ~Oct 2025).

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
