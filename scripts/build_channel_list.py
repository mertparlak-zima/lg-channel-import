#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_channel_list.py — build an edited LG GlobalClone TLL channel list.

Reads the TV's latest export (BASE), applies the target channel order defined
in PLAN, hides everything else, and writes the result to OUT. The output must
be renamed to GlobalClone00001.TLL and copied to the root of an MBR/FAT32 USB
stick before importing on the TV.

Usage:
    python scripts/build_channel_list.py

Before re-running for a new layout:
    1. Update BASE to the newest reference export (see reference/)
    2. Adjust PLAN to the desired channel order
    3. Run, then verify with the checklist in
       .claude/skills/lg-tll-channel-editing/references/verification.md

Rules enforced here (proven on an LG 42LB652V / webOS 1.4):
- Records are never deleted; identity set is preserved
- ITEM blocks are written ascending by prNum, joined with \\r\\n separators
- TV-type records form a contiguous 1..N range (visible first, then hidden)
- Radio prNum values are never touched (0x4000 flag); radios are only hidden
- Hiding uses isInvisable=1 only
- CRLF count must equal the base file exactly (line count never changes)
"""
import os
import re

BASE = os.path.join('..', 'reference', 'tv-export-2026-08-31.tll')
OUT  = os.path.join('..', 'output', 'channel-list-edited.tll')

# Target channel order (channel names are matched case-insensitively,
# ignoring 'HD' suffixes and punctuation; they must match SDT names).
PLAN = [
    # main national channels
    'ATV', 'SHOW', 'STAR TV', 'KANAL D', 'NOW', 'TV8', 'TV8.5',
    # documentary
    'TRT BELGESEL',
    # movies / series / entertainment
    'TV2', 'CNBC-E', 'BEYAZ TV', 'DMAX', 'TLC', 'SHOW MAX', 'TNT INT', 'A2',
    # music
    'TRT MUZIK', 'DREAM TURK', 'POWERTURK TV', 'NR1 TURK TV', 'TMB TV',
    # culture
    'TRT2',
    # news
    'CNN TURK', 'HABERTURK', 'NTV', 'A HABER', 'HABER GLOBAL', 'ULKE TV',
    'BLOOMBERGHT', '24',
    # sports
    'TRT SPOR', 'A SPOR', 'HT SPOR', 'TRT SPOR YILDIZ', 'TRT 3-SPOR',
    # TRT main channels (rarely watched)
    'TRT1', 'TRT HABER', 'TRT TURK', 'TRT WORLD',
    # kids
    'TRT COCUK', 'minikaCOCUK', 'minikaGO',
    # other nationals / news
    'KANAL 7', 'SHOW TURK', 'FLASH HABER', 'HABITAT TV', 'TGRT HABER',
]
assert len(PLAN) == 47 and len(set(PLAN)) == 47


def key(nm):
    """Normalize a channel name for matching."""
    nm = (nm or '').upper()
    nm = re.sub(r'[^A-Z0-9]', '', nm)      # drop spaces, dots, dashes
    if nm.endswith('HD'):
        nm = nm[:-2]
    return nm


text = open(BASE, 'rb').read().decode('utf-8')
base_crlf = text.count('\r\n')
parts = re.split(r'(<ITEM>.*?</ITEM>)', text, flags=re.S)
idxs = [i for i, b in enumerate(parts) if b.startswith('<ITEM>')]
prefix, suffix = ''.join(parts[:idxs[0]]), ''.join(parts[idxs[-1] + 1:])


def f(b, tag):
    m = re.search(r'<%s>([^<]*)</%s>' % (tag, tag), b)
    return m.group(1)


def setf(b, tag, val):
    nb = re.sub(r'<%s>[^<]*</%s>' % (tag, tag), '<%s>%s</%s>' % (tag, val, tag), b)
    assert nb != b or f(b, tag) == val
    return nb


def hexname(b):
    """Decode hexVchName, skipping the DVB encoding prefix byte."""
    hexn = f(b, 'hexVchName') or ''
    try:
        dec = bytes.fromhex(hexn).decode('utf-8', 'replace') if hexn else ''
    except ValueError:
        return ''
    return dec[1:] if dec[:1] in ('\x05', '\x15', '\x1f') else dec


class R:
    pass


recs = []
for i in idxs:
    r = R()
    b = parts[i]
    r.block = b
    r.prNum = int(f(b, 'prNum'))
    r.inv = f(b, 'isInvisable') == '1'
    r.tvid = r.prNum < 16384
    nm = (f(b, 'vchName') or '').strip()
    r.name = nm if nm else hexname(b).strip()
    r.blank = nm == '' and r.name != ''
    recs.append(r)

tvs    = [r for r in recs if r.tvid]
radios = [r for r in recs if not r.tvid]
vis_tv = [r for r in tvs if not r.inv]
print('base: total %d | TV %d | visible TV %d | radio %d'
      % (len(recs), len(tvs), len(vis_tv), len(radios)))

# --- match the plan against the base ---
used, chosen, missing = set(), [], []
for nm in PLAN:
    k = key(nm)
    cands = [r for r in tvs if id(r) not in used and key(r.name) == k]
    cands.sort(key=lambda r: (r.inv, r.prNum))   # prefer visible, then lowest number
    if not cands:
        missing.append(nm)
        continue
    used.add(id(cands[0]))
    chosen.append(cands[0])
assert not missing, 'unmatched channels: %r' % missing

rest_vis = [r for r in vis_tv if id(r) not in used]
rest_vis.sort(key=lambda r: r.prNum)
print('plan: %d/%d matched | remaining visible: %d' % (len(chosen), len(PLAN), len(rest_vis)))
visible = chosen + rest_vis
assert len(visible) == len(vis_tv)

# --- renumber, hide, repair names ---
hidden_tvs = sorted([r for r in tvs if id(r) not in used and r not in rest_vis],
                    key=lambda r: r.prNum)
assert len(hidden_tvs) == len(tvs) - len(visible)
ordered, repaired = [], []
for n, r in enumerate(visible, start=1):
    r.block = setf(r.block, 'prNum', str(n))
    r.block = setf(r.block, 'isInvisable', '0')
    if r.blank:  # repair names that the scan blanked (Turkish characters)
        r.block = setf(r.block, 'vchName', r.name)
        r.block = setf(r.block, 'lengthOfVchName', str(len(r.name)))
        r.block = setf(r.block, 'notConvertedLengthOfVchName', str(len(r.name)))
        r.block = setf(r.block, 'hexVchName', '15' + r.name.encode('utf-8').hex().upper())
        repaired.append((n, r.name))
    ordered.append(r)
for n, r in enumerate(hidden_tvs, start=len(visible) + 1):
    r.block = setf(r.block, 'prNum', str(n))
    r.block = setf(r.block, 'isInvisable', '1')
    ordered.append(r)
for r in radios:
    r.block = setf(r.block, 'isInvisable', '1')
    ordered.append(r)

out = prefix + '\r\n'.join(r.block for r in ordered) + suffix   # separators are MANDATORY
assert out.count('\r\n') == base_crlf, 'CRLF count mismatch!'
assert out.count('\n') == out.count('\r\n')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, 'wb').write(out.encode('utf-8'))
print('repaired names:', repaired)
print('written: %s | visible: %d | hidden TV: %d | radio: %d'
      % (OUT, len(visible), len(hidden_tvs), len(radios)))
