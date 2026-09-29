# TLL File Structure and Format Rules

LG GlobalClone TLL files are plain-text XML (no encryption).

## Overall Structure

```
<?xml version="1.0" encoding="UTF-8"?>\r\n
\r\n
<TLLDATA>\r\n
  <ModelInfo>        <- model, CloneVersion, country settings
  <SatelliteDB>      <- satellite/TP database (NEVER TOUCH)
  <CHANNEL>\r\n
    <ATV>\r\n</ATV>\r\n   <- analog section, empty; keep this exact form
    <DTV>\r\n
      <ITEM>...</ITEM>\r\n   <- one record per channel, ascending by prNum
      ...
    </DTV>\r\n
  </CHANNEL>\r\n
</TLLDATA>\r\n
```

## Format Requirements

| Rule | Value |
|---|---|
| Encoding | UTF-8, **no BOM** |
| Line endings | **CRLF only**, no lone LF |
| ITEM separator | `</ITEM>\r\n<ITEM>` — never glued |
| Empty element | `<ATV>\r\n</ATV>` (not self-closing) |
| File ending | terminates with `\r\n` |
| Attributes | SatelliteDB carries `type="0/1"` attributes; CHANNEL/DTV has none — both states are native, do not modify |
| CRLF count | after editing, must equal the base **numerically** (line count never changes) |

## ITEM Field Dictionary

| Field | Meaning / Rule |
|---|---|
| `prNum` | Displayed channel number. TV-type: contiguous 1..N. **Radio: 16384+N (0x4000 flag) — never modify** |
| `minorNum` | ATSC sub-channel; always 0 for DVB — untouched |
| `original_network_id`, `network_id` | DVB network id — used for channel matching, untouched |
| `transport_id` | TP id — used for matching, untouched |
| `service_id` | Service id — used for matching, untouched |
| `physicalNum` | Per-frequency physical index (repeats across a TP) — **untouched** |
| `sourceIndex` | Scan source index — untouched |
| `serviceType` | DVB service type (table below) |
| `special_data` | Packed scan data; NOT stable per service — **untouched** |
| `frequency` | MHz — used for matching |
| `nitVersion`, `mapType`, `mapAttr` | LCN mapping info; `mapType=1` normal, `0x03` deleted — untouched |
| `isInvisable` | **The hide flag — the only legitimate way to hide a channel** |
| `isBlocked` | Parental lock — untouched |
| `isSkipped` | User "skip" flag — untouched |
| `isNumUnSel` | Not selectable by number — untouched |
| `isDeleted` | Deleted marker — **never use** (records are never deleted anyway) |
| `chNameByte` | 0 — untouched |
| `hexVchName` | Raw DVB name bytes (hex). Prefix `05` = ISO-8859-9, `15` = UTF-8 (used in repairs) |
| `notConvertedLengthOfVchName` | Pre-conversion length — updated during name repair |
| `vchName` | Displayed name; an empty name is a **single space `" "`** |
| `lengthOfVchName` | `len(vchName)` — updated during name repair |
| `hSettingIDHandle`, `usSatelliteHandle` | Satellite references — untouched |
| `isUserSelCHNo` | User-assigned-number marker — untouched |
| `logoIndex`, `videoStreamType` | — untouched |

## serviceType Values (observed)

| Value | Meaning |
|---|---|
| 1 | Digital TV (some SD-labeled broadcasters use it too) |
| 2 | Radio |
| 10 | Radio-like (TEST TONE, TRT World Radio, …) |
| 25 | HDTV |
| 0, 9, 11, 12, 17, 31, 129, 240 | Data/SSU/test services — hide |

## Numbering Model

```
TV-type records:    1 ......... M ................. N
                   +- visible -+----- hidden -------+
Radio records:     16385 .. 16384+K   (0x4000 flag; never touched)
```

- Visible + hidden TV records together form a **contiguous** 1..N range (TV convention)
- prNum is **unique across the whole file** (visible/hidden/radio collisions = zero)
- ITEM blocks are physically stored in **ascending prNum** order

## Name Behavior (LG quirks)

1. For names with Turkish characters a scan may blank `vchName` while the real
   name survives in `hexVchName` — visible records then need name repair
2. An empty name is written as a **single space** (`" "`), not an empty tag
3. Broadcasters change SDT names over time (`STAR TV HD` → `STAR TV`); as long
   as the service id is unchanged the broadcast is the same — do not let name
   differences break matching
4. Repair convention (ChanSort): `vchName` = ASCII name, length fields = len(name),
   `hexVchName` = `15` + uppercase UTF-8 hex
