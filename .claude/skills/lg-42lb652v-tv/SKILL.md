---
name: lg-42lb652v-tv
description: Device-specific profile for the LG 42LB652V-ZA TV — model and firmware info, import quirks, post-import behavior, USB requirements, factory-reset and recovery procedures. Read together with lg-tll-channel-editing when working on this TV's channel list.
---

# LG 42LB652V-ZA — Device Profile

## Device Information

| Field | Value |
|---|---|
| Model | LG 42LB652V-ZA (2014, webOS TV with built-in satellite receiver) |
| webOS | 1.4.0-2536 (afro-ashley) |
| Firmware | 05.05.90 |
| Serial | 503MATW7L753 |
| Reception | Türksat 42° (Turkey) |
| Region | **Turkey** — the list, layout and scan parameters are tailored to Turkish channels; TLL files carry `BroadcastCountrySetting = TUR`. The TV's country setting must be Turkey for imports to work |

## Observed Behavior (proven on this unit)

1. **A TLL import that violates the format rules loops for 40–60 minutes and
   wipes the channel list** ("no signal / not programmed"). Confirmed across
   five failed attempts.
2. **An import merging into a corrupted or stale database can hang even when
   the file is perfect.** Fix: factory reset → clean scan → fresh export →
   edit on that base → import. (Externally corroborated by ChanSort issue #199,
   where the user's import only worked after a factory reset.)
3. **Export always works flawlessly** — only import is fragile.
4. **TP frequency drift between scans:** the same transponder is reported with
   ±1–10 MHz offsets (e.g. 12302 ↔ 12303, 12458 ↔ 12448, 12091 ↔ 12492),
   which is why name-based matching is mandatory as a fallback.

## Post-Import Behavior (verified across two successful imports)

- **The channel order (prNum layout) survives import intact** — the TV does
  not renumber.
- **A clean import takes ~10 seconds** (476–482 records).
- After importing, the TV **re-validates services**: it may rewrite records
  (`tsid`/`onid` zeroed, frequency copy swapped back to the TV's preferred
  one) and **append services** to the tail of the list (observed: DMAX SD,
  TLC SD, TEST 1/2, a regional channel and ~14 radios reappearing as visible).
  This recurs — a cleanup import may be partially undone. Turning off the
  TV's *Automatic Channel Update* setting (if present) likely prevents it.
- **vchName repairs for Turkish-character names get blanked again by the TV**
  (~10 channels): on every import the TV rewrites its own SDT conversion.
  There is no known permanent fix; channel order and playback are unaffected.

## USB Requirements (tested on this unit)

- **MBR partition table + single partition + FAT32** — GPT or multi-partition
  sticks are not read
- Caution: sticks previously prepared as **Rufus** boot media keep a GPT table
  and a `RUFUS_BOOT` partition — reformat to MBR+FAT32 before use
  (Rufus: Partition scheme=MBR, File system=Large FAT32, Non bootable)
- The file must be named exactly `GlobalClone00001.TLL`, in the stick's root,
  as the only file

## TV Menu Paths (webOS 1.4)

| Action | Path |
|---|---|
| Channel list copy / import-export | Settings → Channels → Copy Channel List |
| Satellite scan | Settings → Channels → Auto Tuning → Satellite → Türksat 42° |
| Factory reset | Settings → General → System → Reset to Initial Settings |
| Software info / update | Settings → General → About This TV |

## Recovery Procedures

### Channels lost (failed import)
1. Unplug the USB, power-cycle the TV
2. Re-scan via **12380 / V / 27500** network (NIT) search — finds all current
   Türksat transponders
3. Export a fresh list from the TV — this becomes the new editing base

### Import still hanging (with a verified file)
1. Factory reset: Settings → General → System → Reset to Initial Settings
   (cost: Wi-Fi, app logins, etc. are reset)
2. During first setup choose country = **Turkey**
3. Skip the initial channel scan if possible
4. Insert the USB and import the edited list into the clean database

### Diagnostic test (file vs. TV unclear)
Import the TV's **own unmodified export** renamed to `GlobalClone00001.TLL`:
- If that also hangs → the problem is on the TV side (factory reset)
- If it imports → the problem is in the edited file (bisect: renumber-only →
  +hiding → +name repairs)

## Accepted Channel Layout (this project)

- Visible: main nationals first — ATV, Show, Star, Kanal D, NOW, TV8, TV8.5
- Then TRT Belgesel; movies/series block (TV2, CNBC-e, Beyaz, DMAX, TLC,
  Show Max, TNT INT, A2); music block (TRT Müzik, Dream Türk, PowerTürk,
  NR1, TMB); TRT2; news; sports; TRT main channels; kids; other nationals
- SD duplicates, test/data services and all radios hidden (owner does not
  listen to radio); HD is preferred over SD for the same channel
