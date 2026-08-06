# Kelvinator Climate Component

Home Assistant custom integration to control Kelvinator / Electrolux air
conditioners that use the Broadlink OEM Wi-Fi module (the "smart" ones paired
through the Electrolux Home+ app) — **entirely locally**, no cloud round-trip.

Kelvinator is an Electrolux Group brand, and Kelvinator-branded smart ACs use
the same Electrolux Home+ app and the same Broadlink-based protocol as
Electrolux-branded units — this integration works with either.

> **This is a fork of [DotEfekts/ElectroluxClimateComponent](https://github.com/DotEfekts/ElectroluxClimateComponent)**,
> originally written by [Chelsea Pritchard (DotEfekts)](https://github.com/DotEfekts).
> All credit for reverse-engineering the protocol and building the original
> integration goes to her. This fork:
>
> - is renamed to match the Kelvinator branding on the actual hardware it's
>   running against (three Kelvinator split systems), and
> - fixes a handful of stability/correctness issues found in review — see
>   [CHANGELOG.md](CHANGELOG.md) for exactly what changed and why.
>
> If you're looking for the original, unmodified project, go to
> [DotEfekts/ElectroluxClimateComponent](https://github.com/DotEfekts/ElectroluxClimateComponent)
> instead.

---

## What it does

Exposes each AC as a `climate` entity (power, mode, target temperature, fan
speed, swing) plus a `switch` entity for the front-panel LED, by talking
directly to the unit over your LAN using the same Broadlink protocol the
Electrolux Home+ app uses — nothing leaves your network.

## Supported devices

Any Kelvinator or Electrolux-branded AC with a Broadlink OEM Wi-Fi module
(`devtype 0x4f9b`). DHCP auto-discovery is pre-configured for units reporting
one of these MAC OUI prefixes:

`34:EA:34` · `24:DF:A7` · `A0:43:B0` · `B4:43:0D` · `C8:F7:42` · `E8:16:56` · `E8:70:72` · `EC:0B:AE`

If your unit isn't auto-discovered, add it manually during setup with its IP
address — auto-discovery is a convenience, not a requirement.

## What's different in this fork

The original project works, but was written as a fast first pass (its own
author called it "extremely rough" when first sharing it). This fork keeps
100% of the original functionality and fixes five issues found in review —
full details in [CHANGELOG.md](CHANGELOG.md):

| # | Fix | Why it matters |
|---|---|---|
| 1 | Device discovery no longer blocks Home Assistant's event loop | Startup used to briefly stall unrelated parts of HA; now runs in a background thread, once, instead of twice |
| 2 | Polling handles the AC's own brief reconnects gracefully | The units disassociate/reassociate from Wi-Fi for ~1–2s every few minutes as normal behaviour — this used to throw a full traceback into the log every time a poll landed in that window; now it's a quiet, correct "unavailable" |
| 3 | Fixed a `KeyError` crash path in the switch entity | Matches a guard the climate entity already had |
| 4 | General cleanup | Removed a dead import and a stray debug `print()`, switched to a proper module logger, fixed a copy-paste label bug in the config flow |
| 5 | Config entry migration uses the supported HA API | Was setting `config_entry.version`/`.title` directly, which isn't guaranteed to work on current HA core |

## Installation

### Via HACS (recommended)

1. HACS → **⋮** menu → **Custom repositories**
2. Repository: `https://github.com/Elliottmonaghan/KelvinatorClimateComponent`, Category: **Integration**
3. Install **Kelvinator Climate**, then restart Home Assistant

### Manual

Copy `custom_components/electrolux_climate` into your Home Assistant `config/custom_components/` directory and restart.

> The internal component folder and entity domain are still `electrolux_climate`
> — only the display name and repo are rebranded. See
> [**A note on the rename**](#a-note-on-the-rename) below for why.

## Configuration

Settings → Devices & Services → **Add Integration** → search **Kelvinator Climate**.

- If your AC's MAC matches one of the prefixes above, it may already show up under **Discovered** — just confirm it.
- Otherwise choose **Add manually** and enter the AC's local IP address.
- Set the minimum/maximum temperature the entity should allow (defaults: 17–30°C).

## A note on the rename

Only the **display name** (what you see in the HA integrations list and the
HACS store) and the **repository** were renamed to Kelvinator branding. The
internal domain (`electrolux_climate`), the `custom_components` folder name,
and all entity IDs are unchanged from upstream.

That's deliberate: renaming the domain is a breaking change — it would
generate brand-new entity IDs and require every automation, dashboard card,
and script referencing the old ones to be updated by hand. Since the
underlying protocol and hardware really are the same across both brandings,
there was no upside to forcing that migration just for a label. If you'd
rather have a fully renamed `kelvinator_climate` domain, that's a bigger,
separate change — open an issue if you want it.

## Known limitations

- One AC per config entry — add each unit separately.
- The underlying protocol (`electrolux.py`) supports sleep mode, self-clean, and on/off timers, but only power/mode/temperature/fan/swing and the LED switch are currently exposed as entities. Contributions welcome.
- Local-only: there's no fallback to the Electrolux cloud API if the unit drops off your LAN.

## Credits

- Original protocol reverse-engineering and integration: [DotEfekts](https://github.com/DotEfekts) — see the [Home Assistant Community thread](https://community.home-assistant.io/t/hacking-electrolux-smart-ac/137696) where this started.
- Broadlink protocol handling built on [python-broadlink](https://github.com/mjg59/python-broadlink).

## License

Apache License 2.0 — see [LICENSE](LICENSE), unchanged from the upstream project. Files modified from upstream are noted in [CHANGELOG.md](CHANGELOG.md), per the license's requirements around derivative works.
