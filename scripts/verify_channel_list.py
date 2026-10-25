#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_channel_list.py — run the 8-point pre-flight verification checklist
against output/channel-list-edited.tll and reference/tv-export-2026-08-31.tll.
"""
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_PATH = ROOT / 'output' / 'channel-list-edited.tll'
BASE_PATH = ROOT / 'reference' / 'tv-export-2026-08-31.tll'


def bl(t):
    return [
        b
        for b in re.split(r'(<ITEM>.*?</ITEM>)', t.decode('utf-8'), flags=re.S)
        if b.startswith('<ITEM>')
    ]


def f(b, tag):
    m = re.search(r'<%s>([^<]*)</%s>' % (tag, tag), b)
    return m.group(1)


def main():
    new = NEW_PATH.read_bytes()
    base = BASE_PATH.read_bytes()

    # 1) format
    assert new[:3] != b'\xef\xbb\xbf', 'BOM present!'
    assert new.count(b'\n') == new.count(b'\r\n'), 'lone LF present!'
    assert new.count(b'</ITEM><ITEM>') == 0, 'glued ITEM blocks!'
    assert new.count(b'\r\n') == base.count(b'\r\n'), 'CRLF count differs from base!'
    ET.fromstring(new.decode('utf-8'))  # strict parse

    nb, bb = bl(new), bl(base)
    assert len(nb) == len(bb), 'record count changed!'

    # 2) ordering and uniqueness
    prns = [int(f(b, 'prNum')) for b in nb]
    assert all(prns[i] <= prns[i + 1] for i in range(len(prns) - 1)), 'ITEM order broken!'
    assert not [n for n, c in Counter(prns).items() if c > 1], 'prNum collision!'

    # 3) visible / hidden / radio layout
    vis = [b for b in nb if f(b, 'isInvisable') == '0']
    tva = [b for b in nb if int(f(b, 'prNum')) < 16384]
    rad = [b for b in nb if int(f(b, 'prNum')) >= 16384]
    assert [int(f(b, 'prNum')) for b in vis] == list(range(1, len(vis) + 1)), 'visible not contiguous!'
    assert [int(f(b, 'prNum')) for b in tva if f(b, 'isInvisable') == '1'] == list(
        range(len(vis) + 1, len(tva) + 1)
    ), 'hidden TV range broken!'
    assert {int(f(b, 'prNum')) for b in rad} == {
        int(f(b, 'prNum')) for b in bb if int(f(b, 'prNum')) >= 16384
    }, 'radio numbers changed!'
    assert all(f(b, 'isInvisable') == '1' for b in rad), 'all radios must be hidden!'

    # 4) comparison against base: identity set + changed fields
    ident = lambda b: (
        f(b, 'frequency'),
        f(b, 'transport_id'),
        f(b, 'service_id'),
        f(b, 'original_network_id'),
    )
    assert Counter(map(ident, nb)) == Counter(map(ident, bb)), 'identity set differs!'
    emap = {}
    for b in bb:
        emap.setdefault(ident(b), []).append(b)
    dt = Counter()
    for b in nb:
        o = emap[ident(b)].pop(0)
        assert len(o.split('\r\n')) == len(b.split('\r\n')), 'block line count changed!'
        for x, y in zip(o.split('\r\n'), b.split('\r\n')):
            if x != y:
                dt[re.sub(r'<(\w+)>.*', r'\1', x)] += 1
    allowed = {
        'prNum',
        'isInvisable',
        'vchName',
        'lengthOfVchName',
        'notConvertedLengthOfVchName',
        'hexVchName',
    }
    assert set(dt) <= allowed, f'unauthorized field changes: {set(dt) - allowed}'
    print('ALL CHECKS PASSED | changed fields:', dict(dt))


if __name__ == '__main__':
    main()
