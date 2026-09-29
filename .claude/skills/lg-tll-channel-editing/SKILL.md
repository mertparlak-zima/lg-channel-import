---
name: lg-tll-channel-editing
description: Editing LG TV GlobalClone TLL channel list files — sorting, hiding, renumbering and renaming satellite channels, then reloading the list to the TV over USB. Read before any channel-list or TLL editing task ("edit channel list", "sort channels", "reorder TLL").
---

# LG TLL Channel List Editing

This skill covers editing `GlobalClone00001.TLL` channel list files exported by LG
TVs over USB, **in a form the TV will accept**. Every rule below was proven by
trial and error; violating any of them previously caused the TV to hang on import
for 40–60 minutes and wipe its channel list.

## Sub-references

- `references/file-format.md` — TLL file structure, field dictionary, numbering model, format requirements
- `references/verification.md` — pre-flight verification checklist with runnable test code
- `lg-42lb652v-tv` — device-specific profile (model, firmware, observed quirks, recovery)

## Workflow

### 1. Obtain a fresh export (the base)
Edits are **always built on the TV's most recent export**. After a re-scan or a
factory reset the record identities change, and a file built on a stale base is
rejected. Have the user export from the TV and drop the file into `reference/`.

### 2. Analyze the base
- Record count, ITEM order (must be ascending by prNum), prNum collisions
- TV-type vs radio split (radio = prNum ≥ 16384, i.e. carries the 0x4000 flag)
- Count of `isInvisable=1` records and blank (`vchName`) records
- SatelliteDB size and TP count (for later comparison)

### 3. Define the target order
List the desired visible channels in order (previous layout, user request, or
favorites). Target: visible TV channels numbered **contiguously starting at 1**.

### 4. Map channels
In priority order:
1. **Identity match:** `(frequency, transport_id, service_id, original_network_id)`
2. **Name match:** normalized (case-insensitive, `HD` suffix and punctuation ignored)
3. Unmatched channels are **dropped** (a service absent from the TV database
   cannot be watched anyway) and reported

Note: consecutive scans report the same transponder at ±1–10 MHz offsets
(e.g. 12302 ↔ 12303, 12458 ↔ 12448), so identity misses usually resolve via the
name fallback — it finds a neighboring-frequency copy of the same channel.

### 5. Renumber and hide
- Visible TV records: `prNum = 1..M`, `isInvisable = 0`
- Remaining TV records (hidden): `prNum = M+1..N` (preserves the TV's contiguous
  1..N convention), `isInvisable = 1`
- **Radios: never touch `prNum`** (the 0x4000 flag is meaningful to the TV);
  only set `isInvisable = 1`
- Hiding uses **only** `isInvisable=1` — leave `isSkipped`/`isNumUnSel`/`isDeleted`
  alone (the TV's own hidden records carry only this flag)

### 6. Repair names (when needed)
Scans can blank `vchName` for names with Turkish characters (real name survives
in `hexVchName`). Repair visible blank records using the ChanSort convention:
- `vchName` = ASCII name
- `lengthOfVchName` = `notConvertedLengthOfVchName` = `len(name)`
- `hexVchName` = `15` + `name.encode('utf-8').hex().upper()` (0x15 = DVB UTF-8 marker)

### 7. Assemble the file — mind the separators
When reordering ITEM blocks, the **`\r\n` separator between blocks is mandatory**:

```python
out = prefix + '\r\n'.join(r.block for r in ordered) + suffix
assert out.count('\r\n') == base_crlf   # numeric equality is MANDATORY
```

Glued `</ITEM><ITEM>` breaks the TV's line-based parser — this exact mistake once
produced a 40-minute import loop.

### 8. Editing technique
Do NOT use an XML serializer (attribute order / whitespace get rewritten). Edit
values in place with line-oriented regex:

```python
def setf(block, tag, val):
    nb = re.sub(r'<%s>[^<]*</%s>' % (tag, tag), '<%s>%s</%s>' % (tag, val, tag), block)
    assert nb != block or f(block, tag) == val
    return nb
```

Editable fields **only**: `prNum`, `isInvisable`, and the name-repair fields
(`vchName`, `lengthOfVchName`, `notConvertedLengthOfVchName`, `hexVchName`).
Never touch `physicalNum`, `special_data`, `sourceIndex`, SatelliteDB, or attributes.

### 9. Verify
Run the complete checklist in `references/verification.md` unconditionally.
If any check fails, the file does not go to the TV.

### 10. Deliver
- Save the output as a separate file (e.g. `output/channel-list-edited.tll`)
- The user copies it to the **root of a USB stick** (MBR + single FAT32 partition)
  renamed to exactly **`GlobalClone00001.TLL`**
- TV menu: **Settings → Channels → Copy Channel List → Import from USB**
- An import running longer than ~15 minutes counts as failed

## Critical Prohibitions (summary)

1. ❌ Physically deleting records — hide instead (`isInvisable=1`)
2. ❌ Building on a stale base — always use the latest export
3. ❌ Changing radio prNum or breaking the 0x4000 flag
4. ❌ Losing `\r\n` separators (`</ITEM><ITEM>` gluing)
5. ❌ Regenerating the file with an XML serializer
6. ❌ Using `isDeleted`/`isSkipped` to hide
7. ❌ Skipping verification — even the CRLF count must match the base numerically
