# Pre-flight Verification Checklist

Run every check unconditionally before an edited TLL file is handed to the TV.
If any check fails, the file is not delivered.

## Checklist

- [ ] Record count and identity set are identical to the base
- [ ] ITEM order is ascending by prNum; no glued `</ITEM><ITEM>` anywhere
- [ ] CRLF count equals the base's CRLF count (**numeric equality**)
- [ ] No prNum collisions in the whole file; visible TV channels contiguous 1..M
- [ ] Radio numbers unchanged; all radios `isInvisable=1`
- [ ] No nameless/TEST/radio records among visible channels
- [ ] Changed fields are only: `prNum`, `isInvisable`, name-repaired fields
- [ ] No BOM, no lone LF, strict XML parse passes

## Test Code (Python)

```python
import re, xml.etree.ElementTree as ET
from collections import Counter

new  = open('output/channel-list-edited.tll','rb').read()
base = open('reference/tv-export-2026-08-31.tll','rb').read()

# 1) format
assert new[:3] != b'\xef\xbb\xbf', 'BOM present!'
assert new.count(b'\n') == new.count(b'\r\n'), 'lone LF present!'
assert new.count(b'</ITEM><ITEM>') == 0, 'glued ITEM blocks!'
assert new.count(b'\r\n') == base.count(b'\r\n'), 'CRLF count differs from base!'
ET.fromstring(new.decode('utf-8'))  # strict parse

def bl(t): return [b for b in re.split(r'(<ITEM>.*?</ITEM>)', t.decode('utf-8'), flags=re.S) if b.startswith('<ITEM>')]
def f(b, tag):
    m = re.search(r'<%s>([^<]*)</%s>' % (tag, tag), b); return m.group(1)

nb, bb = bl(new), bl(base)
assert len(nb) == len(bb), 'record count changed!'

# 2) ordering and uniqueness
prns = [int(f(b,'prNum')) for b in nb]
assert all(prns[i] <= prns[i+1] for i in range(len(prns)-1)), 'ITEM order broken!'
assert not [n for n,c in Counter(prns).items() if c > 1], 'prNum collision!'

# 3) visible / hidden / radio layout
vis = [b for b in nb if f(b,'isInvisable')=='0']
tva = [b for b in nb if int(f(b,'prNum')) < 16384]
rad = [b for b in nb if int(f(b,'prNum')) >= 16384]
assert [int(f(b,'prNum')) for b in vis] == list(range(1, len(vis)+1)), 'visible not contiguous!'
assert [int(f(b,'prNum')) for b in tva if f(b,'isInvisable')=='1'] == list(range(len(vis)+1, len(tva)+1)), 'hidden TV range broken!'
assert {int(f(b,'prNum')) for b in rad} == {int(f(b,'prNum')) for b in bb if int(f(b,'prNum'))>=16384}, 'radio numbers changed!'
assert not [b for b in vis if (f(b,'vchName') or '').strip()=='' or 'TEST' in (f(b,'vchName') or '').upper() or f(b,'serviceType') in ('2','10')], 'nameless/TEST/radio in visible list!'

# 4) comparison against base: identity set + changed fields
ident = lambda b: (f(b,'frequency'), f(b,'transport_id'), f(b,'service_id'), f(b,'original_network_id'))
assert Counter(map(ident, nb)) == Counter(map(ident, bb)), 'identity set differs!'
emap = {}
for b in bb: emap.setdefault(ident(b), []).append(b)
dt = Counter()
for b in nb:
    o = emap[ident(b)].pop(0)
    assert len(o.split('\r\n')) == len(b.split('\r\n')), 'block line count changed!'
    for x, y in zip(o.split('\r\n'), b.split('\r\n')):
        if x != y: dt[re.sub(r'<(\w+)>.*', r'\1', x)] += 1
ALLOWED = {'prNum', 'isInvisable', 'vchName', 'lengthOfVchName',
           'notConvertedLengthOfVchName', 'hexVchName'}
assert set(dt) <= ALLOWED, f'unauthorized field changes: {set(dt) - ALLOWED}'
print('ALL CHECKS PASSED | changed fields:', dict(dt))
```

## Symptom → Cause Table

| Symptom (on the TV) | Likely cause |
|---|---|
| Import loops 40–60 min, list ends up empty | Deleted records / stale base / glued ITEM blocks / broken format |
| Import hangs indefinitely (even with a clean file) | TV database corrupted or stale — factory reset required |
| TV does not see the USB stick | GPT table / multiple partitions / exFAT-NTFS — use MBR + single FAT32 |
| "Different country" error / import refused | TV country setting ≠ file country setting |
| Channels present but not tuning | Stale frequency records — re-scan required |
