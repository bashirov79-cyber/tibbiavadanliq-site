#!/usr/bin/env python3
"""tibbiavadanliq.az formatı üçün səhifə generatoru (build_ta.py istifadə edir)."""
import html, json, os, re
from urllib.parse import quote

T = {
 'az': dict(rel='Bu bölmədən digər məhsullar', more='Bölmənin hamısı', off='Təklifə', on='Siyahıda', aria='Təklif siyahısına əlavə et',
            home='Ana səhifə', kat='Kataloq', title='{n} — klinika və müəssisələr üçün | {d}',
            wa='Salam! «{n}» barədə məlumat və qiymət almaq istəyirik. ({d})'),
 'ru': dict(rel='Другие товары раздела', more='Весь раздел', off='В запрос', on='В списке', aria='Добавить в список запроса',
            home='Главная', kat='Каталог', title='{n} — для клиник и учреждений | {d}',
            wa='Здравствуйте! Интересует «{n}»: подробности и цена. ({d})'),
}
PLUS = '<svg class="i plus" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg><svg class="i ok" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.500l4.500 4.500L19 7.500"/></svg>'
U = html.unescape
def attr(s): return html.escape(U(s), quote=True)


class Site:
    def __init__(self, root, data_path, domain, ref):
        self.root, self.dom, self.ref = root, domain, ref
        self.d = json.load(open(data_path, encoding='utf-8'))
        self.P = {int(k): v for k, v in self.d['products'].items()}
        self.S, self.I = self.d['sections'], self.d['insts']
        self.tpl = {l: self._tokenize(l) for l in ('az', 'ru')}

    # ---- köməkçilər ----
    def pre(self, lang): return '' if lang == 'az' else '../ru/'
    def path(self, slug, lang): return slug + '.html' if lang == 'az' else 'ru/' + slug + '.html'
    def grp(self, p):
        return next(g for g in self.S[p['sec']]['groups'] if g['id'] == p['grp'])
    def meta(self, p, lang):
        g = self.grp(p)
        return g['n_' + lang] if g['id'] else self.S[p['sec']]['n_' + lang]

    def row(self, p, lang, meta=None, extra=''):
        pre, t, img = self.pre(lang), T[lang], ('' if lang == 'az' else '../')
        n = p['n_' + lang]; a = attr(n); href = pre + p['slug'] + '.html'
        m = self.meta(p, lang) if meta is None else meta
        return (f'<li class="row"{extra}><a class="th" href="{href}" tabindex="-1" aria-hidden="true"><img src="{img}t/{p["id"]}.webp" alt="" width="64" height="64" loading="lazy"></a>'
                f'<div class="rt"><a class="nm" href="{href}">{n}</a><span class="meta">{m}</span></div>'
                f'<button type="button" class="add" data-add="{p["id"]}" data-name="{a}" data-url="{p["slug"]}.html" data-off="{t["off"]}" data-on="{t["on"]}" aria-pressed="false" aria-label="{t["aria"]}: {a}">{PLUS}<span class="t">{t["off"]}</span></button></li>')

    def wa(self, p, lang):
        return 'https://wa.me/994702720302?text=' + quote(T[lang]['wa'].format(n=U(p['n_' + lang]), d=self.dom), safe='/')

    def ld_product(self, p, lang):
        u = f'https://{self.dom}/' + self.path(p['slug'], lang)
        return json.dumps({"@context": "https://schema.org", "@type": "Product", "name": U(p['n_' + lang]), "sku": str(p['id']),
                           "description": p['ld_' + lang], "image": f'https://{self.dom}/img/{p["id"]}.webp',
                           "category": U(self.S[p['sec']]['n_' + lang]), "url": u}, ensure_ascii=False)

    def ld_crumbs(self, p, lang):
        b = f'https://{self.dom}/' + ('' if lang == 'az' else 'ru/'); t = T[lang]
        it = [(t['home'], b), (t['kat'], b + 'kataloq.html'), (U(self.S[p['sec']]['n_' + lang]), b + p['sec'] + '.html'), (U(p['n_' + lang]), b + p['slug'] + '.html')]
        return json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(it)]}, ensure_ascii=False)

    # ---- şablon ----
    def _tokenize(self, lang):
        p = next(x for x in self.P.values() if x['slug'] == self.ref)
        s = open(os.path.join(self.root, self.path(self.ref, lang)), encoding='utf-8').read()
        reps = [
            (r'<title>.*?</title>', '<title>@TITLE@</title>'),
            (r'(<meta property="og:title" content=")[^"]*', r'\1@TITLE@'),
            (r'(<meta name="description" content=")[^"]*', r'\1@MD@'),
            (r'(<meta property="og:description" content=")[^"]*', r'\1@MD@'),
            (r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "Product".*?</script>', '<script type="application/ld+json">@LDP@</script>'),
            (r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "BreadcrumbList".*?</script>', '<script type="application/ld+json">@LDB@</script>'),
            (r'(<ol class="crumbs">(?:<li>.*?</li>){2})<li>.*?</li><li aria-current="page">.*?</li>', r'\1@CRUMB@'),
            (r'<div class="plate">.*?</div>', '<div class="plate">@PLATE@</div>'),
            (r'<p class="pmeta">.*?</p>', '<p class="pmeta">@PMETA@</p>'),
            (r'<h1>.*?</h1>', '<h1>@N@</h1>'),
            (r'data-add="\d+" data-name="[^"]*"', 'data-add="@ID@" data-name="@AN@"'),
            (r'(aria-label="[^":]*: )[^"]*(">)(?=<svg class="i plus")', r'\1@AN@\2'),
            (r'(<a class="btn wa" href=")[^"]*(?=" target="_blank" rel="noopener"><svg[^>]*><path[^>]*/><path[^>]*/></svg>[^<]*</a><a class="btn ghost")', r'\1@WA@'),
            (r'<div class="fits"><span>([^<]*)</span><div>.*?</div></div>', r'<div class="fits"><span>\1</span><div>@FITS@</div></div>'),
            (r'(<section class="desc"><h2>[^<]*</h2>).*?</section>', r'\1@DESC@</section>'),
            (r'(<a class="more" href=")[^"]*', r'\1@SECURL@'),
            (r'<ul class="rows">.*?</ul>', '<ul class="rows">@ROWS@</ul>'),
        ]
        for rx, rep in reps:
            s, k = re.subn(rx, rep, s, count=1, flags=re.S)
            assert k == 1, (lang, rx)
        s = s.replace('/img/%d.webp' % p['id'], '/img/@ID@.webp')
        s = s.replace(self.ref + '.html', '@SLUG@.html')
        assert self.ref not in s and str(p['id']) not in s.replace('@', ''), lang
        return s

    def product_page(self, p, lang, rel_ids):
        pre, t, img = self.pre(lang), T[lang], ('' if lang == 'az' else '../')
        sec = self.S[p['sec']]; n = p['n_' + lang]; g = self.grp(p)
        crumb = f'<li><a href="{pre}{p["sec"]}.html">{sec["n_" + lang]}</a></li><li aria-current="page">{n}</li>'
        pm = (f'<a href="{pre}{p["sec"]}.html#{g["id"]}">{g["n_" + lang]}</a>' if g['id'] else f'<a href="{pre}{p["sec"]}.html">{sec["n_" + lang]}</a>')
        fits = ''.join(f'<a href="{pre}{f}.html">{self.I[f]["n_" + lang]}</a>' for f in p['fits'])
        v = {'TITLE': attr(T[lang]['title'].format(n=U(n), d=self.dom)), 'MD': p['md_' + lang],
             'LDP': self.ld_product(p, lang), 'LDB': self.ld_crumbs(p, lang), 'CRUMB': crumb,
             'PLATE': f'<img src="{img}img/{p["id"]}.webp" alt="{attr(n)}" width="{p["w"]}" height="{p["h"]}">',
             'PMETA': pm, 'N': n, 'ID': str(p['id']), 'AN': attr(n), 'WA': self.wa(p, lang), 'FITS': fits,
             'DESC': p['d_' + lang], 'SECURL': f'{pre}{p["sec"]}.html',
             'ROWS': ''.join(self.row(self.P[i], lang) for i in rel_ids), 'SLUG': p['slug']}
        return re.sub(r'@([A-Z]+)@', lambda m: v[m.group(1)], self.tpl[lang])
