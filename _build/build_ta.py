#!/usr/bin/env python3
"""tibbiavadanliq.az saytını data.json-dan yeniləyir.
İstifadə: python3 build_ta.py <sayt_qovluğu> <data.json> <domain> <istinad_slug> [changes.json]

changes.json (hamısı istəyə bağlı):
{ "upsert": [ {"id":1, "slug":"...", "sec":"ilk-yardim", "grp":"canta"|null, "w":400, "h":400,
               "fits":["tibb-menteqesi", ...],            (müəssisə səhifələri)
               "also":[["tibbi-mebel","xerek"], ...],     (əlavə bölmələrdə də göstər — istəyə bağlı)
               "n_az","n_ru","d_az","d_ru"  (HTML),  "md_az","md_ru","ld_az","ld_ru" (verilməsə yaradılır)} ],
  "remove": [ id, ... ],
  "images": { "id": "<400px webp>" },  "thumbs": { "id": "<128px webp>" } }
Heç bir dəyişiklik olmadan işə salınsa, saytı olduğu kimi yenidən yazır (yoxlama üçün)."""
import html, json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_ta import Site, T, U
GO = '<svg class="i go" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

root, data_path, domain, ref = sys.argv[1:5]
changes = json.load(open(sys.argv[5], encoding='utf-8')) if len(sys.argv) > 5 else {}
S = Site(root, data_path, domain, ref)
old_total = len(S.P)
TR = str.maketrans({'ə': 'e', 'ı': 'i', 'ş': 's', 'ç': 'c', 'ğ': 'g', 'ö': 'o', 'ü': 'u', 'Ə': 'e', 'I': 'i', 'İ': 'i', 'Ş': 's', 'Ç': 'c', 'Ğ': 'g', 'Ö': 'o', 'Ü': 'u'})
def norm(s): return U(s).translate(TR).lower()
def rnorm(s): return U(s).lower().replace('ё', 'е')
def plain(h): return U(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))).strip()
def cut(s, n):
    if len(s) <= n: return s
    return s[:n].rsplit(' ', 1)[0].rstrip(' ,.;:') + '…'
def rd(f): return open(os.path.join(root, f), encoding='utf-8').read()
def wr(f, s, o):
    if s != o: open(os.path.join(root, f), 'w', encoding='utf-8').write(s)

# ---------- 1. məlumatı dəyiş ----------
removed = set(changes.get('remove', [])); touched = set()
def unlist(pid, where):
    for o in where.values():
        for g in o['groups']:
            if pid in g['items']: g['items'].remove(pid)
for pid in removed:
    p = S.P.pop(pid, None); unlist(pid, S.S); unlist(pid, S.I)
    if p:
        for lang in ('az', 'ru'):
            f = os.path.join(root, S.path(p['slug'], lang))
            if os.path.exists(f): os.remove(f)
        for d in ('img', 't'):
            f = os.path.join(root, d, f'{pid}.webp')
            if os.path.exists(f): os.remove(f)
for u in changes.get('upsert', []):
    pid = u['id']; old = S.P.get(pid, {})
    also = u.pop('also', None)
    p = {**old, **u}
    for lang in ('az', 'ru'):
        pl = plain(p['d_' + lang])
        if 'ld_' + lang not in u and ('d_' + lang in u or not old): p['ld_' + lang] = cut(pl, 300)
        if 'md_' + lang not in u and ('d_' + lang in u or 'n_' + lang in u or not old):
            n = U(p['n_' + lang])
            p['md_' + lang] = html.escape(
                (f'{n} tibb müəssisələri üçün. ' + cut(pl, max(20, 130 - len(n))) + ' Kommersiya təklifini bir sorğu ilə alın.') if lang == 'az' else
                (f'{n} для медицинских учреждений. ' + cut(pl, max(20, 130 - len(n))) + ' Коммерческое предложение — одним запросом.'), quote=True)
    # bölmə siyahıları: əsas + əlavə
    if old and (also is not None or (old['sec'], old['grp']) != (p['sec'], p['grp'])):
        if also is None:   # yalnız əsas yer dəyişib — əlavələri saxla
            also = [[s, g['id']] for s, o in S.S.items() for g in o['groups'] if pid in g['items'] and (s, g['id']) != (old['sec'], old['grp'])]
        unlist(pid, S.S)
    for sec, gid in [[p['sec'], p['grp']]] + (also or []):
        grp = next(g for g in S.S[sec]['groups'] if g['id'] == gid)
        if pid not in grp['items']: grp['items'].append(pid); grp['items'].sort(reverse=True)
    p['fits'] = [x for x in S.d['insts_order'] if x in p.get('fits', [])]
    S.P[pid] = p; touched.add(pid)
    for key, d in (('images', 'img'), ('thumbs', 't')):
        if str(pid) in changes.get(key, {}):
            shutil.copy(changes[key][str(pid)], os.path.join(root, d, f'{pid}.webp'))
    if str(pid) in changes.get('images', {}) and str(pid) not in changes.get('thumbs', {}):
        from PIL import Image   # 128px kvadrat miniatür (ağ fonda)
        im = Image.open(os.path.join(root, 'img', f'{pid}.webp')).convert('RGBA'); im.thumbnail((128, 128), Image.LANCZOS)
        bg = Image.new('RGB', (128, 128), 'white'); bg.paste(im, ((128 - im.width) // 2, (128 - im.height) // 2), im)
        bg.save(os.path.join(root, 't', f'{pid}.webp'), 'WEBP', quality=80)
    # müəssisə səhifələri: fits × məhsulun göründüyü bölmələr
    unlist(pid, S.I)
    secs = [s for s in S.d['sections_order'] if any(pid in g['items'] for g in S.S[s]['groups'])]
    for inst in p.get('fits', []):
        o = S.I[inst]
        for s in secs:
            g = next((g for g in o['groups'] if g['id'] == s), None)
            if g is None:
                g = {'id': s, 'n_az': S.S[s]['n_az'], 'n_ru': S.S[s]['n_ru'], 'items': []}; o['groups'].append(g)
            g['items'].append(pid); g['items'].sort(reverse=True)
for o in S.I.values(): o['groups'] = [g for g in o['groups'] if g['items']]
for o in S.S.values():
    for g in o['groups']: assert g['items'] or len(o['groups']) > 1, ('boş bölmə', o['slug'])

def ids_of(o): return {i for g in o['groups'] for i in g['items']}
def cnt(slug): return len(ids_of(S.S[slug] if slug in S.S else S.I[slug]))
def gmeta(pid, sec, lang):
    for g in S.S[sec]['groups']:
        if pid in g['items']: return g['n_' + lang] if g['id'] else S.S[sec]['n_' + lang]
def listings(pid):
    prim = S.P[pid]['sec']
    return [(s, g) for s in [prim] + [x for x in S.d['sections_order'] if x != prim] for g in S.S[s]['groups'] if pid in g['items']]
def hay(pid):
    p = S.P[pid]; h = [norm(p['n_az']), rnorm(p['n_ru'])]
    for s, g in listings(pid):
        h += [norm(S.S[s]['n_az']), rnorm(S.S[s]['n_ru'])]
        if g['id']: h += [norm(g['n_az']), rnorm(g['n_ru'])]
    if p.get('kw'): h.append(p['kw'])   # əlavə axtarış sözləri (sinonimlər)
    return ' '.join(h)

# ---------- 2. məhsul səhifələri ----------
for pid, p in S.P.items():
    for lang in ('az', 'ru'):
        f = S.path(p['slug'], lang)
        old = rd(f) if os.path.exists(os.path.join(root, f)) else None
        cur = [int(x) for x in re.findall(r'data-add="(\d+)" data-name="[^"]*" data-url="[^"]*" data-off="' + T[lang]['off'], old)] if old else []
        ids = [i for i in cur if i in S.P and i != pid and any(i in g['items'] for g in S.S[p['sec']]['groups'])]
        if len(ids) < 5:
            pool = [i for g in S.S[p['sec']]['groups'] for i in g['items'] if i != pid and i not in ids]
            same = [i for i in S.grp(p)['items'] if i in pool]
            ids += sorted(same, key=lambda i: abs(i - pid))[:5 - len(ids)]
            ids += sorted((i for i in pool if i not in ids), key=lambda i: abs(i - pid))[:5 - len(ids)]
        wr(f, S.product_page(p, lang, ids[:5]), old)

# ---------- 3. siyahı səhifələri ----------
def counts_text(s, n, lang):
    if lang == 'az':
        s = re.sub(r'(<title>[^<]*— )\d+( məhsul)', rf'\g<1>{n}\2', s, count=1)
        s = re.sub(r'\d+( məhsul\.</p>)', rf'{n}\1', s, count=1)
    else:
        s = re.sub(r'(<title>[^<]*— товаров: )\d+', rf'\g<1>{n}', s, count=1)
        s = re.sub(r'(Товаров: )\d+(\.</p>)', rf'\g<1>{n}\2', s, count=1)
    return s

def index_counts(s):
    s = re.sub(r'(<li><a href="(?:\.\./ru/)?([^"]+)\.html"><span class="a">(?:(?!</a>).)*?</span><span class="n">)\d+',
               lambda m: m.group(1) + str(cnt(m.group(2))) if m.group(2) in S.S or m.group(2) in S.I else m.group(0), s)
    return re.sub(r'(<a class="sol" href="(?:\.\./ru/)?([^"]+)\.html">(?:(?!</a>).)*?<span class="n">[^<\d]*)\d+', lambda m: m.group(1) + str(cnt(m.group(2))), s)

def section_body(slug, lang, inst):
    pre = S.pre(lang); o = (S.I if inst else S.S)[slug]; out = ''
    grouped = o['groups'][0]['id'] is not None
    if grouped:
        out += '<div class="chips anchors">' + ''.join(f'<a href="#{g["id"]}">{g["n_" + lang]}<span>{len(g["items"])}</span></a>' for g in o['groups']) + '</div>'
        for g in o['groups']:
            more = f'<a class="more" href="{pre}{g["id"]}.html">{T[lang]["more"]}{GO}</a>' if inst else ''
            rows = ''.join(S.row(S.P[i], lang, gmeta(i, g['id'] if inst else slug, lang)) for i in g['items'])
            out += f'<section class="group" id="{g["id"]}"><h2>{g["n_" + lang]}<span>{len(g["items"])}</span>{more}</h2><ul class="rows">{rows}</ul></section>'
    else:
        out += '<ul class="rows">' + ''.join(S.row(S.P[i], lang, S.S[slug]['n_' + lang]) for i in o['groups'][0]['items']) + '</ul>'
    return out

kat_order = [i for s in S.d['sections_order'] for i in sorted((i for i, p in S.P.items() if p['sec'] == s), reverse=True)]
def kat_row(pid, lang):
    p = S.P[pid]; g = S.grp(p); sec = S.S[p['sec']]
    meta = sec['n_' + lang] + (' · ' + g['n_' + lang] if g['id'] else '')
    codes = ' '.join(dict.fromkeys(S.d['scode'][s] for s, _ in listings(pid)))
    return S.row(p, lang, meta, f' data-s="{codes}" data-h="{html.escape(hay(pid), quote=True)}"')

total = len(S.P)
for lang in ('az', 'ru'):
    d = '' if lang == 'az' else 'ru/'
    for f in os.listdir(os.path.join(root, d) if d else root):
        if not f.endswith('.html'): continue
        fp = d + f; s = rd(fp); o = s; slug = f[:-5]
        if '<div class="wrap prod">' in s: continue
        if slug in S.S or slug in S.I:
            s = counts_text(s, cnt(slug), lang)
            s = re.sub(r'(<div class="wrap listing">).*?(</div><section class="block">)',
                       lambda m: m.group(1) + section_body(slug, lang, slug in S.I) + m.group(2), s, count=1, flags=re.S)
        if slug == 'kataloq':
            s = re.sub(r'(<ul class="rows" id="crows">).*?(</ul>)', lambda m: m.group(1) + ''.join(kat_row(i, lang) for i in kat_order) + m.group(2), s, count=1, flags=re.S)
            s = re.sub(r'(data-f="([^"]*)" aria-pressed="(?:true|false)">[^<]*<span>)\d+',
                       lambda m: m.group(1) + str(total if not m.group(2) else cnt(next(k for k, v in S.d['scode'].items() if v == m.group(2)))), s)
        if slug == 'index' and total != old_total:
            s = re.sub(rf'(?<![\d.]){old_total}(?![\d.])', str(total), s)
        s = index_counts(s)
        wr(fp, s, o)

# ---------- 4. axtarış, sitemap, llms.txt ----------
order = sorted(S.P, reverse=True)
for lang, f in (('az', 'search.json'), ('ru', 'ru/search.json')):
    pre = '' if lang == 'az' else '../'
    ent = []
    for i in order:
        p = S.P[i]; n = U(p['n_' + lang])
        ent.append({"u": f'{p["slug"]}.html', "i": f'{pre}t/{i}.webp', "t": n, "k": U(S.meta(p, lang)),
                    "n": norm(n) if lang == 'az' else rnorm(n), "h": hay(i)})
    wr(f, json.dumps(ent, ensure_ascii=False, separators=(',', ':')), rd(f))
smp = 'sitemap.xml'; sm0 = rd(smp)
prev = re.findall(r'<loc>([^<]+)</loc>', sm0)
B = f'https://{domain}/'
dead = {B + pre + S.path(slug, 'az') for pre in ('', 'ru/') for slug in changes.get('_removed_slugs', [])}
prod_urls = {B + pre + p['slug'] + '.html' for p in S.P.values() for pre in ('', 'ru/')}
locs = [u for u in prev if u not in dead and (u in prod_urls or os.path.exists(os.path.join(root, u[len(B):] or 'index.html')) or u.endswith('/'))]
for pre in ('', 'ru/'):
    new = [B + pre + S.P[i]['slug'] + '.html' for i in order if B + pre + S.P[i]['slug'] + '.html' not in locs]
    pos = locs.index(B + 'ru/') if pre == '' and B + 'ru/' in locs else len(locs)
    locs[pos:pos] = new
wr(smp, sm0[:sm0.index('<url>')] + ''.join(f'<url><loc>{u}</loc></url>' for u in locs) + '</urlset>\n', sm0)
l = rd('llms.txt'); wr('llms.txt', re.sub(r'Məhsul sayı: \d+', f'Məhsul sayı: {total}', l), l)

# ---------- 5. məlumatı saxla ----------
S.d['products'] = {str(k): v for k, v in S.P.items()}
S.d['kataloq_order'] = kat_order
json.dump(S.d, open(data_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'OK: {total} məhsul; dəyişən: {sorted(touched)}; silinən: {sorted(removed)}')
