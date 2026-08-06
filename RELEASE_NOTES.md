# Kelvinator Climate Component — v0.1.0 (Initial Release)

Local Home Assistant control for Kelvinator/Electrolux air conditioners with
a Broadlink OEM Wi-Fi module — no cloud round-trip.

This is the first release under the **Kelvinator Climate Component** name —
a fork of [DotEfekts/ElectroluxClimateComponent](https://github.com/DotEfekts/ElectroluxClimateComponent),
renamed to match the branding on the hardware it's actually running against
(three Kelvinator split systems), with five stability/correctness fixes
applied on top. All credit for the original protocol reverse-engineering and
integration goes to [DotEfekts](https://github.com/DotEfekts).

## Highlights

- 🏷️ **Renamed** to Kelvinator Climate — cosmetic only. The internal domain,
  `custom_components` folder, and entity IDs are unchanged from upstream, so
  this is a safe drop-in for anyone already running the original: no entity
  churn, no automation rewrites.
- 🐛 **Event loop no longer blocks on startup.** Device discovery used to run
  synchronously on Home Assistant's event loop, twice, on every startup —
  now it runs once, in the background, and the result is shared across both
  entities.
- 🐛 **No more log-spam on the AC's own brief reconnects.** These units
  disassociate and reassociate from Wi-Fi for ~1–2 seconds every few minutes
  as normal behaviour. Polling used to throw a full traceback into the log
  every time it landed in that window — it's now a clean, quiet
  "unavailable."
- 🐛 Fixed a `KeyError` crash path in the switch (LED) entity.
- 🧹 General cleanup: dead imports, a stray debug `print()`, root-logger
  usage, and a copy-paste label bug in the config flow, all fixed.
- 🧹 Config entry migration now goes through the supported Home Assistant
  API instead of direct attribute assignment.

Full details: [CHANGELOG.md](https://github.com/Elliottmonaghan/KelvinatorClimateComponent/blob/master/CHANGELOG.md)

## Installation

**Via HACS:**
1. HACS → **⋮** → **Custom repositories**
2. Add `https://github.com/Elliottmonaghan/KelvinatorClimateComponent` as an **Integration**
3. Install **Kelvinator Climate**, restart Home Assistant

**Manual:** copy `custom_components/electrolux_climate` into your `config/custom_components/` directory and restart.

Then: Settings → Devices & Services → **Add Integration** → search **Kelvinator Climate**.

## Supported devices

Any Kelvinator or Electrolux-branded AC with a Broadlink OEM Wi-Fi module
(paired via the Electrolux Home+ app). DHCP auto-discovery covers MAC OUI
prefixes `34:EA:34`, `24:DF:A7`, `A0:43:B0`, `B4:43:0D`, `C8:F7:42`,
`E8:16:56`, `E8:70:72`, `EC:0B:AE` — anything else can still be added
manually by IP.

## Known limitations

- One AC per config entry.
- Sleep mode, self-clean, and on/off timers exist in the protocol layer but
  aren't yet exposed as entities.
- Local-only — no fallback to the Electrolux cloud API.

**Full Changelog**: https://github.com/Elliottmonaghan/KelvinatorClimateComponent/commits/v0.1.0
