#!/usr/bin/env python3
"""tibbiavadanliq.az formatlı saytdan məlumat çıxarır → <qovluq>.data.json"""
import json, os, re, sys

ROOT = sys.argv[1]
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def one(rx, s, flags=re.S):
    m = re.search(rx, s, flags); return m.group(1) if m else None
ROW_ID = r'<li class="row"[^>]*><a class="th" href="[^"]+" tabindex="-1" aria-hidden="true"><img src="(?:\.\./)?t/(\d+)\.webp"'

pages = sorted(f for f in os.listdir(ROOT) if f.endswith('.html'))
products, sections, insts = {}, {}, {}
for f in pages:
    s = rd(f)
    if '<div class="wrap prod">' in s:
        p = {'slug': f[:-5]}
        p['id'] = int(one(r'<div class="plate"><img src="img/(\d+)\.webp"', s))
        p['w'], p['h'] = map(int, re.search(r'<div class="plate"><img src="img/\d+\.webp" alt="[^"]*" width="(\d+)" height="(\d+)"', s).groups())
        p['sec'] = one(r'<li><a href="kataloq\.html">[^<]*</a></li><li><a href="([^"]+)\.html">', s)
        p['grp'] = one(r'<p class="pmeta"><a href="[^"#]+#([^"]+)">', s)
        p['fits'] = re.findall(r'<a href="([^"]+)\.html">', one(r'<div class="fits"><span>[^<]*</span><div>(.*?)</div></div>', s) or '')
        for lang, src in (('az', s), ('ru', rd('ru/' + f))):
            p['n_' + lang] = one(r'<h1>(.*?)</h1>', src)
            p['md_' + lang] = one(r'<meta name="description" content="([^"]*)">', src)
            p['d_' + lang] = one(r'<section class="desc"><h2>[^<]*</h2>(.*?)</section>', src)
            p['ld_' + lang] = json.loads(one(r'<script type="application/ld\+json">(\{"@context": "https://schema.org", "@type": "Product".*?)</script>', src))['description']
        products[p['id']] = p
    elif '<section class="phead">' in s and '<section class="group"' in s or '<div class="wrap listing">' in s:
        kind = 'inst' if '<p class="kicker">' in s else 'sec'
        o = {'slug': f[:-5]}
        for lang, src in (('az', s), ('ru', rd('ru/' + f))):
            o['n_' + lang] = one(r'<h1>(.*?)</h1>', src)
            groups = []
            for gid, gname, body in re.findall(r'<section class="group" id="([^"]+)"><h2>(.*?)<span>\d+</span>.*?<ul class="rows">(.*?)</ul></section>', src, re.S):
                groups.append({'id': gid, 'n_' + lang: gname, 'items': [int(x) for x in re.findall(ROW_ID, body)]})
            if not groups:
                body = one(r'<div class="wrap listing">(?:<div class="chips anchors">.*?</div>)?<ul class="rows">(.*?)</ul>', src)
                groups = [{'id': None, 'n_' + lang: None, 'items': [int(x) for x in re.findall(ROW_ID, body)]}]
            if lang == 'az': o['groups'] = groups
            else:
                for g, gr in zip(o['groups'], groups):
                    assert g['id'] == gr['id'] and g['items'] == gr['items'], (f, g['id'])
                    g['n_ru'] = gr['n_ru']
        (insts if kind == 'inst' else sections)[o['slug']] = o

k = rd('kataloq.html')
cat_rows = re.findall(r'<li class="row" data-s="([^"]*)" data-h="[^"]*"><a class="th" href="[^"]+" tabindex="-1" aria-hidden="true"><img src="t/(\d+)\.webp"', k)
chips = re.findall(r'<a href="([^"]+)\.html" data-f="([^"]*)" aria-pressed', k)
order = [c[0] for c in chips if c[0] != 'kataloq']
data = {'sections_order': order, 'scode': {a: b for a, b in chips if a != 'kataloq'},
        'kataloq_order': [int(i) for _, i in cat_rows], 'sections': sections, 'insts': insts,
        'insts_order': re.findall(r'<a class="sol" href="([^"]+)\.html">', rd('index.html')), 'products': products}
json.dump(data, open(ROOT.rstrip('/') + '.data.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
allids = [i for x in sections.values() for g in x['groups'] for i in g['items']]
print(len(products), 'məhsul;', len(sections), 'bölmə;', len(insts), 'müəssisə;', 'kataloq sətri:', len(cat_rows), '; bölmə siyahılarında:', len(allids), len(set(allids)))
