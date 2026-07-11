# -*- coding: utf-8 -*-
"""
Merged alle 3 Fach-JSONs -> seed_data.json -> bettet Seed in Karteikarten.html ein
und zählt SEED_V automatisch hoch.

Ausführen nach:
  - create_erklaerungen.py  (explain-Felder generieren)
  - create_bv.py / create_gt.py / create_vm.py  (Karten aktualisieren)
"""
import json, os, re

BASE = r'C:\Users\JaZip\Desktop\Claude Projekte\Karteikarten'
HTML  = os.path.join(BASE, 'index.html')

def load_decks(fn):
    d = json.load(open(os.path.join(BASE, fn), encoding='utf-8'))
    return d['decks'] if isinstance(d, dict) and 'decks' in d else d

bv = load_decks('Bauverfahren_Karteikarten.json')
gt = load_decks('Geotechnik_Karteikarten.json')
vm = load_decks('Vermessung_Karteikarten.json')

for d in bv: d['fach'] = 'Bauverfahren'
for d in gt: d['fach'] = 'Geotechnik'
for d in vm: d['fach'] = 'Vermessung'

all_decks = bv + gt + vm

seed = {'decks': all_decks, 'log': {}, 'settings': {'theme': 'dark', 'newPerDay': 20, 'fach': 'Alle'}}
seedpath = os.path.join(BASE, 'seed_data.json')
seed_json = json.dumps(seed, ensure_ascii=False, separators=(',', ':'))
# Escape </script> inside JSON to avoid breaking HTML parser
seed_json_safe = seed_json.replace('</', '<\\/')

json.dump(seed, open(seedpath, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---- Embed in HTML ----
with open(HTML, encoding='utf-8') as f:
    html = f.read()

# Read current SEED_V and increment
m = re.search(r'const SEED_V=(\d+);', html)
if not m:
    raise RuntimeError("SEED_V nicht in HTML gefunden")
old_v = int(m.group(1))
new_v = old_v + 1

# Replace seedData block (entire line)
# WICHTIG: Ersetzung per Funktion, sonst interpretiert re.sub Backslash-Escapes
# (\r, \n, \g, \1 ...) im Ersetzungsstring und zerstoert das JSON.
replacement = f'<script type="application/json" id="seedData">{seed_json_safe}</script>'
html = re.sub(
    r'<script type="application/json" id="seedData">.*?</script>',
    lambda _m: replacement,
    html, flags=re.DOTALL
)

# Bump SEED_V
html = html.replace(f'const SEED_V={old_v};', f'const SEED_V={new_v};')

with open(HTML, 'w', encoding='utf-8') as f:
    f.write(html)

# ---- Stats ----
nfig     = sum(1 for d in all_decks for c in d['cards'] if c.get('fig'))
nexpl    = sum(1 for d in all_decks for c in d['cards'] if c.get('explain'))
faecher  = {}
for d in all_decks:
    faecher.setdefault(d['fach'], [0, 0])
    faecher[d['fach']][0] += 1
    faecher[d['fach']][1] += len(d['cards'])

print('Faecher:')
for f, (nd, nc) in faecher.items():
    print(f'  {f}: {nd} Stapel, {nc} Karten')
total_cards = sum(len(d['cards']) for d in all_decks)
print(f'Gesamt: {len(all_decks)} Stapel, {total_cards} Karten')
print(f'  {nfig} mit SVG-Grafik, {nexpl} mit Erklärung ({nexpl*100//total_cards}%)')
print(f'SEED_V: {old_v} -> {new_v}')
print(f'seed_data.json: {os.path.getsize(seedpath):,} Bytes')
print(f'index.html: {os.path.getsize(HTML):,} Bytes')
print('HTML aktualisiert.')
