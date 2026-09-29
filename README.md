# LG Channel List Editor

Tooling and documentation for editing the satellite channel list of an
**LG 42LB652V-ZA** (webOS 1.4) TV via its USB export/import mechanism
(`GlobalClone00001.TLL`), with a strict, TV-verified rule set.

The goal: keep the owner's preferred channel order across Türksat frequency
changes — main nationals first, then movies/series, music, news, sports — with
SD duplicates, test services and radios hidden.

> **Region notice:** this setup is tailored specifically to **Turkish channels
> and the Turkey broadcast region**. The reference list and the channel layout
> target **Türksat 42°** services, and the TLL files carry
> `BroadcastCountrySetting = TUR` in `ModelInfo`. The TV's own country/region
> setting must be **Turkey** — importing this list on a unit configured for
> another region will be rejected or misbehave. Channel names, the accepted
> layout and the scan parameters (12380/V/27500 network search) are all
> Turkey-specific.

## Repository Layout

```
.
├── README.md                        # this file
├── .gitignore
├── reference/
│   └── tv-export-2026-08-31.tll     # the TV's most recent export (editing base)
├── scripts/
│   └── build_channel_list.py        # builds an edited list from the reference
├── output/                          # build output (gitignored)
└── .claude/skills/
    ├── lg-tll-channel-editing/      # main skill: editing workflow + rules
    │   ├── SKILL.md
    │   └── references/
    │       ├── file-format.md       # TLL structure, field dictionary
    │       └── verification.md      # pre-flight checklist + test code
    └── lg-42lb652v-tv/              # device profile: quirks, recovery
        └── SKILL.md
```

## Quick Start

1. **Export** the current list on the TV:
   *Settings → Channels → Copy Channel List → Export to USB*
2. Save it as `reference/tv-export-<date>.tll` and point `BASE` in
   `scripts/build_channel_list.py` at it.
3. Edit `PLAN` in the script to the desired channel order.
4. Build and verify:

   ```bash
   python scripts/build_channel_list.py
   ```

   Then run the verification checklist in
   `.claude/skills/lg-tll-channel-editing/references/verification.md`.
5. **Import**: copy the output to the root of an **MBR + single FAT32** USB
   stick, renamed to exactly `GlobalClone00001.TLL`, then on the TV:
   *Settings → Channels → Copy Channel List → Import from USB*.

A healthy import completes in ~10 seconds. Anything beyond ~15 minutes is a
failure — see the device profile skill for recovery procedures.

## Skills

| Skill | Read when | Covers |
|---|---|---|
| `.claude/skills/lg-tll-channel-editing/SKILL.md` | **before every edit** | 10-step workflow: base handling, channel matching, renumbering, hiding, name repair, file assembly, prohibitions |
| ↳ `references/file-format.md` | structure/field questions | TLL layout, 28-field dictionary, service types, numbering model, format requirements |
| ↳ `references/verification.md` | **before every delivery** | 8-point checklist, runnable Python test, symptom→cause table |
| `.claude/skills/lg-42lb652v-tv/SKILL.md` | when working with this TV | device info, observed import quirks, post-import behavior, USB requirements, menu paths, factory reset & recovery |

In Claude Code sessions the skills are auto-listed and can be invoked as
`/lg-tll-channel-editing` and `/lg-42lb652v-tv`.

## Key Rules (the short version)

1. **Never delete records** — hide with `isInvisable=1` instead.
2. **Always build on the TV's latest export** — record identities change on
   every scan; stale bases are rejected.
3. ITEM blocks stay **ascending by prNum**, joined with `\r\n` separators —
   and the CRLF count must match the base file numerically.
4. **Radio `prNum` values are never touched** (they carry the 0x4000 flag).
5. Only `prNum`, `isInvisable` and name-repair fields are ever edited;
   everything else is preserved byte-for-byte.
6. USB media must be **MBR + single FAT32 partition**; the file must be named
   `GlobalClone00001.TLL` in the stick's root.
7. If a valid import still hangs, the TV database is stale — **factory reset,
   clean scan, fresh export**, then edit and import.

## Background

- August 2026 Türksat frequency changes broke the stored list; the TV was
  factory-reset and re-scanned via the 12380/V/27500 network search.
- Early edit attempts failed: the TV looped 40–60 minutes on import and wiped
  the list. Root causes identified and fixed along the way: deleted records,
  stale bases, unordered ITEM blocks, a broken radio numbering convention,
  missing `\r\n` separators, a GPT/Rufus USB layout, and a corrupted database
  requiring a factory reset.
- The final verified layout (176 visible channels) imported in ~10 seconds and
  survived the TV's post-import re-validation with the order intact.

## References

- [ChanSort](https://github.com/PredatH0r/ChanSort) — reference open-source LG
  TLL editor
  ([GcXmlSerializer.cs](https://github.com/PredatH0r/ChanSort/blob/master/source/ChanSort.Loader.LG/GlobalClone/GcXmlSerializer.cs))
- [ChanSort issue #199](https://github.com/PredatH0r/ChanSort/issues/199) — webOS import failure fixed by factory reset
- [LG — Reset to Initial Settings](https://www.lg.com/tr/destek/product-support/troubleshoot/help-library/cs-CT52000196-20153388678512/)
- [Reddit — USB FAT32/MBR requirement](https://www.reddit.com/r/webos/comments/t5y6xo/exporting_channel_list_does_not_work_c9/)
