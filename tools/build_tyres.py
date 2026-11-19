"""Build the tyre catalogue for vulkanizacia.ge from tools/tyres.json.

Generates:
  /saburavebi/                 hub (ka)      + index-en.html / index-ru.html
  /saburavebi/<size>/          one Georgian page per size, e.g. /saburavebi/205-55-r16/
and keeps in sync (idempotent, safe to re-run):
  - "საბურავები / Tyres / Шины" link in the top nav of every page
  - "tyres by size" strip on the three homepages
  - sitemap.xml and llms.txt blocks between <!-- tyres:start --> / <!-- tyres:end --> markers

Run from the repo root after editing tools/tyres.json:   python3 tools/build_tyres.py
Then rebuild CSS if needed: ./node_modules/.bin/tailwindcss -i src/input.css -o assets/styles.css --minify
"""
import json
import re
import shutil
import subprocess
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://vulkanizacia.ge"
TEL, TEL_FMT, WA = "+995591909013", "+995 591 90 90 13", "995591909013"
HUB = "/saburavebi/"
TEMPLATE_SLUG = "balansireba"   # nav + footer are copied from this service page
LANG_FILE = {"ka": "index.html", "en": "index-en.html", "ru": "index-ru.html"}
TODAY_FILE = ROOT / "tools" / "tyres.json"


# ------------------------------------------------------------------ sizes
def parse(label):
    m = re.fullmatch(r"(\d{3})/(\d{2}) R(\d{2})", label.strip())
    assert m, f"bad size: {label!r} (expected e.g. '205/55 R16')"
    w, p, r = map(int, m.groups())
    sidewall = round(w * p / 100)
    return dict(label=f"{w}/{p} R{r}", w=w, p=p, r=r, slug=f"{w}-{p}-r{r}",
                sidewall=sidewall, rim_mm=round(r * 25.4), diameter=round(r * 25.4 + 2 * w * p / 100))


_DATA = json.loads(TODAY_FILE.read_text(encoding="utf-8"))
SIZES = [parse(s) for s in _DATA["sizes"]]
SIZES.sort(key=lambda s: (s["r"], s["w"], s["p"]))
RIMS = sorted({s["r"] for s in SIZES})
_BY_LABEL = {s["label"]: s for s in SIZES}
POPULAR = [_BY_LABEL[parse(x)["label"]] for x in _DATA.get("popular", [])]
RIM_RANGE = f"R{RIMS[0]}-დან R{RIMS[-1]}-მდე"


def rim_url(r):
    return f"{HUB}r{r}/"


def kind(s):
    """Short, hedged note about where a size is typically used."""
    if s["p"] <= 40 or (s["p"] <= 45 and s["r"] >= 19):
        return ("low", f"{s['label']} დაბალპროფილიანი საბურავია — ხშირად გამოიყენება სპორტულ და პრემიუმ ავტომობილებზე. "
                       "დაბალი გვერდის გამო ორმოებსა და ბორდიურზე დარტყმისას უფრო ადვილად ზიანდება, ამიტომ მისი შეცვლა ხშირად მოულოდნელად და სასწრაფოდ გჭირდებათ — "
                       "მოგიტანთ და ადგილზე დაგიყენებთ.")
    if s["w"] >= 255 or (s["p"] >= 60 and s["r"] >= 17):
        return ("suv", f"{s['label']} ზომა ხშირად გამოიყენება ჯიპებსა და კროსოვერებზე. დიდი ბორბლის შეცვლა ადგილზე განსაკუთრებით მოსახერხებელია — "
                       "აღარ გჭირდებათ ავტომობილის სახელოსნომდე ტარება.")
    if s["r"] <= 15:
        return ("small", f"{s['label']} ზომა ხშირად გამოიყენება კომპაქტურ და საშუალო კლასის ავტომობილებზე — ერთ-ერთი ყველაზე მოთხოვნადი ზომაა ქალაქში.")
    return ("mid", f"{s['label']} ზომა ხშირად გამოიყენება სედანებსა და კროსოვერებზე — ერთ-ერთი პოპულარული ზომაა თბილისში.")


# When a customer needs a tyre replaced (hub + category pages; size pages show the first 5)
WHEN_REPLACE = [
    "საბურავი გასკდა ან გვერდითი კედელი დაზიანდა — ასეთი დაზიანების შეკეთება შეუძლებელია",
    "ნახვრეტი ძალიან დიდია ან საბურავის გვერდზეა",
    "ორმოში ჩავარდნის ან ბორდიურზე დარტყმის შემდეგ საბურავზე გამობერვა გაჩნდა",
    "პროტექტორი გაცვდა — ზაფხულის საბურავზე 3 მმ-ზე, ზამთრისაზე 4 მმ-ზე ნაკლებია",
    "საბურავზე ბზარები გაჩნდა ან 6 წელზე ძველია და რეზინი გამაგრდა",
    "ზამთრის ან ზაფხულის სეზონი დადგა",
    "საბურავი არათანაბრად ცვდება ან ვიბრაცია ბალანსირების შემდეგაც არ ქრება",
    "ერთი საბურავი დაზიანდა და იმავე ღერძზე წყვილის შერჩევა გჭირდებათ",
]


def size_url(s):
    return f"{HUB}{s['slug']}/"


def similar(s, limit=4):
    out = [o for o in SIZES if o is not s and o["r"] == s["r"] and abs(o["diameter"] - s["diameter"]) / s["diameter"] <= 0.03]
    return sorted(out, key=lambda o: abs(o["diameter"] - s["diameter"]))[:limit]


def wa_link(text):
    from urllib.parse import quote
    return f"https://wa.me/{WA}?text={quote(text)}"


# ------------------------------------------------------------------ shared chrome
def chrome(lang, urls):
    """nav + footer + floating buttons from the template page, with the language switcher pointed at `urls`."""
    src = (ROOT / "services" / TEMPLATE_SLUG / LANG_FILE[lang]).read_text(encoding="utf-8")
    nav = src[src.index("<!-- Nav -->"):src.index("<!-- Breadcrumb -->")]
    foot = src[src.index("<!-- Footer -->"):src.index("</body>")]
    base = f"{SITE}/services/{TEMPLATE_SLUG}/"

    def fix(t):
        t = t.replace(base + "index-en.html", SITE + urls["en"]).replace(base + "index-ru.html", SITE + urls["ru"])
        return t.replace(base, SITE + urls["ka"])
    return fix(nav), fix(foot)


def ld(obj):
    return ('<!-- google -->\n<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False)
            + "\n</script>\n<!-- /google -->\n")


PROVIDER = {"@type": "AutoRepair", "name": "Vulkanizacia.ge", "telephone": TEL, "email": "info@vulkanizacia.ge",
            "url": SITE, "image": f"{SITE}/assets/cover.jpg",
            "address": {"@type": "PostalAddress", "addressLocality": "Tbilisi", "addressRegion": "Tbilisi", "addressCountry": "GE"},
            "sameAs": ["https://towing.ge"]}


def page(lang, *, url, title, desc, keywords, alternates, image, schema, crumbs, body, nav_urls):
    nav, foot = chrome(lang, nav_urls)
    alt = "".join(f'<link rel="alternate" hreflang="{h}" href="{SITE}{u}">' for h, u in alternates)
    crumb_html = '<li class="text-zinc-600">/</li>'.join(
        (f'<li><a href="{u}" class="hover:text-brand">{n}</a></li>' if u else f'<li class="text-zinc-200">{n}</li>') for n, u in crumbs)
    crumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + (u or url)} for i, (n, u) in enumerate(crumbs)]}
    return f"""<!DOCTYPE html>
<html lang="{lang}" class="scroll-smooth">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{escape(desc)}">
<meta name="keywords" content="{escape(keywords)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE}{url}">
{alt}
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(desc)}">
<meta property="og:image" content="{SITE}/assets/{image}.jpg">
<meta property="og:url" content="{SITE}{url}">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#18181b">
<title>{escape(title)}</title>
<link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Georgian:wght@400;500;700;800&display=swap" rel="stylesheet">
<link href="/assets/styles.css" rel="stylesheet">
{''.join(ld(x) for x in schema)}{ld(crumb_ld)}</head>
<body class="bg-zinc-950 text-zinc-100 font-sans antialiased">

{nav}<!-- Breadcrumb -->
<nav aria-label="breadcrumb" class="mx-auto max-w-6xl px-4 pt-6">
  <ol class="flex flex-wrap items-center gap-2 text-sm text-zinc-400">
    {crumb_html}
  </ol>
</nav>

{body}
{foot}</body>
</html>
"""


# ------------------------------------------------------------------ UI pieces
CHECK = ('<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.7" stroke="currentColor" aria-hidden="true">'
         '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg>')
PLUS = ('<svg class="h-5 w-5 shrink-0 text-brand transition group-open:rotate-45" fill="none" viewBox="0 0 24 24" stroke-width="1.7" stroke="currentColor" aria-hidden="true">'
        '<path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>')
PHONE = ('<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.7" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" '
         'd="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z"/></svg>')


def btn_call():
    return (f'<a href="tel:{TEL}" class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl bg-brand px-5 py-3 font-bold text-zinc-950 hover:bg-amber-400">'
            f'{PHONE} {TEL_FMT}</a>')


def btn_wa(text, label="WhatsApp"):
    return (f'<a href="{wa_link(text)}" target="_blank" rel="noopener" class="inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl bg-[#25D366] px-5 py-3 font-bold text-white hover:opacity-90">{label}</a>')


def chip(s, active=False):
    cls = "bg-brand text-zinc-950 font-bold" if active else "bg-zinc-900 text-zinc-200 ring-1 ring-zinc-800 hover:ring-brand/60 hover:text-brand"
    return f'<a href="{size_url(s)}" class="rounded-full px-3 py-1.5 text-sm transition {cls}">{s["label"]}</a>'


def ul(items):
    return ('<ul class="mt-5 space-y-3">' + "".join(
        f'<li class="flex items-start gap-3"><span class="mt-0.5 text-brand">{CHECK}</span><span class="text-zinc-300">{x}</span></li>' for x in items) + "</ul>")


def faq_html(faq):
    return '<div class="mt-5 space-y-3">' + "".join(
        f'<details class="group rounded-xl bg-zinc-900 ring-1 ring-zinc-800 open:ring-brand/50"><summary class="flex cursor-pointer items-center justify-between gap-4 p-5 font-semibold list-none"><span>{escape(q)}</span>{PLUS}</summary><p class="px-5 pb-5 -mt-1 text-zinc-400">{escape(a)}</p></details>'
        for q, a in faq) + "</div>"


def faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}


def steps(items):
    return '<ol class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">' + "".join(
        f'<li class="rounded-2xl bg-zinc-900 p-5 ring-1 ring-zinc-800"><span class="grid h-9 w-9 place-items-center rounded-full bg-brand font-bold text-zinc-950">{i}</span>'
        f'<h3 class="mt-3 text-lg font-bold font-head">{t}</h3><p class="mt-1.5 text-sm text-zinc-400">{x}</p></li>'
        for i, (t, x) in enumerate(items, 1)) + "</ol>"


# ------------------------------------------------------------------ hub copy
HUB_T = {
    "ka": dict(
        title="საბურავები თბილისში — ახალი და მეორადი, მიწოდებით და მონტაჟით",
        desc="საბურავები თბილისში ზომების მიხედვით — ახალი და მეორადი, ზაფხულის, ზამთრის და ყველა სეზონის. მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ, 24/7.",
        keywords="საბურავები, საბურავები თბილისში, საბურავების მაღაზია, ზამთრის საბურავები, მეორადი საბურავები, საბურავების ყიდვა, საბურავები ზომით",
        crumbs=["მთავარი", "საბურავები"], home="/index.html",
        h1="საბურავები თბილისში",
        lead="ახალი და მეორადი საბურავები — ზაფხულის, ზამთრის და ყველა სეზონის. შეარჩიეთ ზომა — მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ. 24/7.",
        picker="იპოვეთ საბურავი ზომით", filter_ph="მაგ. 205/55 R16 ან 235/35", all="ყველა",
        notfound="ეს ზომა სიაში არ არის — მოგვწერეთ და მოგიძებნით:",
        when_h="როდის გჭირდებათ საბურავის შეცვლა", when_p="საბურავის შეცვლა ხშირად მოულოდნელად გჭირდებათ. ყველაზე გავრცელებული შემთხვევებია:", when=WHEN_REPLACE,
        rims_h="საბურავები დისკის ზომის მიხედვით",
        hint="ზომა წერია საბურავის გვერდზე, მაგალითად 205/55 R16.", hint_link="როგორ წავიკითხოთ ზომა →",
        wa_size="გამარჯობა, მაინტერესებს საბურავი {}", wa_generic="გამარჯობა, მაინტერესებს საბურავები",
        popular="პოპულარული ზომები", how="როგორ მუშაობს",
        steps=[("შეარჩიეთ ზომა", "დაგვირეკეთ ან მოგვწერეთ WhatsApp-ზე საბურავის ზომა — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს."),
               ("მოგიტანთ", "საბურავებს მოგიტანთ სახლთან, სამსახურთან ან გზაზე — თბილისის ნებისმიერ უბანში."),
               ("გამოგიცვლით", "ადგილზე ჩავცვამთ საბურავებს დისკებზე და დავაყენებთ ავტომობილზე."),
               ("დავაბალანსებთ", "ბორბლებს დავაბალანსებთ და შევამოწმებთ წნევას — გზაზე უსაფრთხოდ დაბრუნდებით.")],
        types_h="რა საბურავები გვაქვს",
        types=[("ახალი საბურავები", "ახალი საბურავები სხვადასხვა მწარმოებლისგან — ზაფხულის, ზამთრის და ყველა სეზონის.", "/saburavebi/axali-saburavebi/"),
               ("მეორადი საბურავები", "კარგ მდგომარეობაში მყოფი მეორადი საბურავები ხელმისაწვდომ ფასად.", "/saburavebi/meoradi-saburavebi/"),
               ("ზამთრის საბურავები", "თოვლსა და ცივ ამინდზე გათვლილი საბურავები — დაგიყენებთ ადგილზე.", "/saburavebi/zamtris-saburavebi/"),
               ("ზაფხულის და ყველა სეზონის", "საბურავები ქალაქში სამოძრაოდ და გრძელი გზებისთვის.", "/saburavebi/zapkhulis-saburavebi/")],
        more="ვრცლად →",
        sos_h="საბურავი გაგისკდათ გზაში?",
        sos_p="თუ საბურავის შეკეთება შეუძლებელია, ახალს ან მეორადს თქვენს ზომაში მოგიტანთ და ადგილზე დაგიყენებთ — სათადარიგოს გარეშეც.",
        sos_link=("მოძრავი ვულკანიზაცია →", "/services/modzravi-vulkanizacia/"),
        faq_h="ხშირად დასმული კითხვები",
        faq=[("სად ვნახო ჩემი საბურავის ზომა?", "ზომა წერია საბურავის გვერდზე, მაგალითად 205/55 R16. ასევე მითითებულია მძღოლის კარის ჩარჩოზე ან ავტომობილის სახელმძღვანელოში."),
             ("რა ღირს საბურავი?", "ფასი დამოკიდებულია ზომაზე, სეზონზე, მწარმოებელზე და იმაზე, ახალია თუ მეორადი. დაგვირეკეთ ან მოგვწერეთ ზომა WhatsApp-ზე — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს."),
             ("მონტაჟსა და ბალანსირებასაც აკეთებთ?", "დიახ — გთავაზობთ სრულ მომსახურებას: მიწოდებას, მონტაჟს და ბალანსირებას. ფასს წინასწარ შეგითანხმებთ."),
             ("მეორადი საბურავი უსაფრთხოა?", "მეორად საბურავებს ვარჩევთ კარგ მდგომარეობაში — საკმარისი პროტექტორით და დაზიანების გარეშე. დაყენებამდე შეგიძლიათ თავად დაათვალიეროთ."),
             ("ჩემი ზომა სიაში არ არის?", "დაგვიკავშირდით — სიაში მხოლოდ ყველაზე პოპულარული ზომებია. სხვა ზომის საბურავის მოძიებაშიც დაგეხმარებით.")],
        service="საბურავების მიწოდება და მონტაჟი",
        strip_h="საბურავები ზომების მიხედვით", strip_p="ახალი და მეორადი საბურავები — მიწოდებით, მონტაჟით და ბალანსირებით ადგილზე.", strip_all="ყველა ზომა და ინფორმაცია →",
        nav="საბურავები"),
    "en": dict(
        title="Tyres in Tbilisi — new and used, delivered and fitted",
        desc="Tyres in Tbilisi by size — new and used, summer, winter and all-season. We deliver, fit and balance them on the spot, 24/7.",
        keywords="tyres Tbilisi, buy tyres Tbilisi, winter tyres Tbilisi, used tyres Tbilisi, tyre shop Tbilisi",
        crumbs=["Home", "Tyres"], home="/index-en.html",
        h1="Tyres in Tbilisi",
        lead="New and used tyres — summer, winter and all-season. Choose your size and we deliver, fit and balance the tyres on site. 24/7.",
        picker="Find tyres by size", filter_ph="e.g. 205/55 R16 or 235/35", all="All",
        notfound="This size isn't listed — message us and we'll find it:",
        when_h="When you need a new tyre", when_p="A tyre replacement is often needed unexpectedly. The most common cases:",
        when=["The tyre burst or the sidewall is damaged — this kind of damage can't be repaired", "The puncture is too large or on the sidewall",
              "A bulge appeared after hitting a pothole or a kerb", "The tread is worn — below 3 mm on summer tyres, 4 mm on winter tyres",
              "The tyre has cracks, or it is over 6 years old and the rubber has hardened", "The winter or summer season has arrived",
              "The tyre wears unevenly or vibration remains after balancing", "One tyre is damaged and you need a matching one for the same axle"],
        rims_h="Tyres by rim size",
        hint="The size is printed on the tyre sidewall, e.g. 205/55 R16.", hint_link="How to read a tyre size →",
        wa_size="Hello, I'm interested in tyres {}", wa_generic="Hello, I'm interested in tyres",
        popular="Popular sizes", how="How it works",
        steps=[("Choose your size", "Call or message us on WhatsApp with your tyre size — we'll tell you the available options and the price."),
               ("We deliver", "We bring the tyres to your home, office or roadside — anywhere in Tbilisi."),
               ("We fit them", "We mount the tyres on your rims and fit the wheels on the spot."),
               ("We balance them", "We balance the wheels and check the pressure, so you are back on the road safely.")],
        types_h="Tyres we offer",
        types=[("New tyres", "New tyres from different manufacturers — summer, winter and all-season.", None),
               ("Used tyres", "Used tyres in good condition at affordable prices.", None),
               ("Winter tyres", "Tyres made for snow and cold weather — fitted at your location.", "/services/sezonuri-saburavebis-shecvla/index-en.html"),
               ("Summer and all-season", "Tyres for city driving in Tbilisi and long trips.", None)],
        more="Learn more →",
        sos_h="Tyre burst on the road?",
        sos_p="If the tyre can't be repaired, we bring a new or used tyre in your size and fit it on the spot — even without a spare.",
        sos_link=("Mobile tyre service →", "/services/modzravi-vulkanizacia/index-en.html"),
        faq_h="Frequently asked questions",
        faq=[("Where do I find my tyre size?", "It is printed on the tyre sidewall, for example 205/55 R16. It is also on the sticker in the driver's door frame or in the car manual."),
             ("How much does a tyre cost?", "It depends on the size, season, manufacturer and whether it is new or used. Call us or send your size on WhatsApp — we'll tell you the available options and the price."),
             ("Do you also fit and balance the tyres?", "Yes — we offer the full service: delivery, fitting and balancing. We agree the price with you in advance."),
             ("Are used tyres safe?", "We choose used tyres in good condition — with enough tread and no damage. You can inspect them yourself before fitting."),
             ("My size isn't on the list?", "Contact us — the list shows only the most popular sizes. We can help you find tyres in other sizes too.")],
        service="Tyre delivery and fitting",
        strip_h="Tyres by size", strip_p="New and used tyres — delivered, fitted and balanced on site.", strip_all="All sizes and details →",
        nav="Tyres"),
    "ru": dict(
        title="Шины в Тбилиси — новые и б/у, доставка и шиномонтаж",
        desc="Шины в Тбилиси по размерам — новые и б/у, летние, зимние и всесезонные. Привезём, установим и отбалансируем на месте, 24/7.",
        keywords="шины Тбилиси, купить шины Тбилиси, зимние шины Тбилиси, б/у шины Тбилиси, шиномонтаж Тбилиси",
        crumbs=["Главная", "Шины"], home="/index-ru.html",
        h1="Шины в Тбилиси",
        lead="Новые и б/у шины — летние, зимние и всесезонные. Выберите размер — привезём, установим и отбалансируем на месте. 24/7.",
        picker="Подбор шин по размеру", filter_ph="например 205/55 R16 или 235/35", all="Все",
        notfound="Этого размера нет в списке — напишите нам, и мы найдём:",
        when_h="Когда нужна замена шины", when_p="Замена шины часто нужна неожиданно. Самые частые случаи:",
        when=["Шина лопнула или повреждена боковина — такое повреждение не ремонтируется", "Прокол слишком большой или на боковине",
              "После ямы или удара о бордюр на шине появилась грыжа", "Протектор изношен — менее 3 мм у летних шин и 4 мм у зимних",
              "На шине появились трещины, или ей больше 6 лет и резина затвердела", "Наступил зимний или летний сезон",
              "Шина изнашивается неравномерно или вибрация не проходит после балансировки", "Повреждена одна шина, и нужна пара на ту же ось"],
        rims_h="Шины по размеру диска",
        hint="Размер указан на боковине шины, например 205/55 R16.", hint_link="Как прочитать размер шины →",
        wa_size="Здравствуйте, интересуют шины {}", wa_generic="Здравствуйте, интересуют шины",
        popular="Популярные размеры", how="Как это работает",
        steps=[("Выберите размер", "Позвоните или напишите размер в WhatsApp — расскажем о вариантах в наличии и цене."),
               ("Привезём", "Доставим шины к дому, офису или на дорогу — в любой район Тбилиси."),
               ("Установим", "Смонтируем шины на диски и установим колёса на месте."),
               ("Отбалансируем", "Отбалансируем колёса и проверим давление — и вы безопасно продолжите путь.")],
        types_h="Какие шины у нас есть",
        types=[("Новые шины", "Новые шины разных производителей — летние, зимние и всесезонные.", None),
               ("Шины б/у", "Б/у шины в хорошем состоянии по доступной цене.", None),
               ("Зимние шины", "Шины для снега и холодной погоды — установим по вашему адресу.", "/services/sezonuri-saburavebis-shecvla/index-ru.html"),
               ("Летние и всесезонные", "Шины для городской езды по Тбилиси и дальних поездок.", None)],
        more="Подробнее →",
        sos_h="Лопнула шина в дороге?",
        sos_p="Если шину нельзя отремонтировать, привезём новую или б/у шину вашего размера и установим на месте — даже без запаски.",
        sos_link=("Мобильная вулканизация →", "/services/modzravi-vulkanizacia/index-ru.html"),
        faq_h="Частые вопросы",
        faq=[("Где посмотреть размер шины?", "Он указан на боковине шины, например 205/55 R16, а также на наклейке в проёме водительской двери или в руководстве автомобиля."),
             ("Сколько стоит шина?", "Цена зависит от размера, сезона, производителя и от того, новая шина или б/у. Позвоните или напишите размер в WhatsApp — расскажем о вариантах и цене."),
             ("Вы устанавливаете и балансируете шины?", "Да — мы предлагаем полный сервис: доставку, монтаж и балансировку. Цену согласуем заранее."),
             ("Безопасны ли шины б/у?", "Мы отбираем б/у шины в хорошем состоянии — с достаточным протектором и без повреждений. Перед установкой вы можете осмотреть их сами."),
             ("Вашего размера нет в списке?", "Свяжитесь с нами — в списке только самые популярные размеры. Поможем найти шины и других размеров.")],
        service="Доставка и монтаж шин",
        strip_h="Шины по размерам", strip_p="Новые и б/у шины — с доставкой, монтажом и балансировкой на месте.", strip_all="Все размеры и подробности →",
        nav="Шины"),
}
HUB_URLS = {lang: HUB + ("" if f == "index.html" else f) for lang, f in LANG_FILE.items()}


UI = {"ka": dict(rim="დისკი", all_of="ყველა R{} →", shown="ნაჩვენებია {} ზომა"),
      "en": dict(rim="rim", all_of="All R{} →", shown="Showing {} sizes"),
      "ru": dict(rim="диск", all_of="Все R{} →", shown="Показано размеров: {}")}


def n_sizes(lang, n):
    if lang == "ka":
        return f"{n} ზომა"
    if lang == "en":
        return f"{n} size" + ("" if n == 1 else "s")
    tail = "размер" if n % 10 == 1 and n % 100 != 11 else ("размера" if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14 else "размеров")
    return f"{n} {tail}"


def filter_html(t):
    """Size filter: free-text box ("235/35", "R20", "2353520") + rim buttons; filters the grid below."""
    btn = "shrink-0 rounded-full px-4 py-2 text-sm font-semibold ring-1 ring-zinc-700 transition hover:ring-brand"
    rims = "".join(f'<button type="button" data-rim="{r}" class="{btn}">R{r}</button>' for r in RIMS)
    return f"""<div id="tyre-filter" class="mt-6 rounded-2xl bg-zinc-900 p-5 ring-1 ring-zinc-800">
    <label for="tyre-q" class="font-semibold">{t['picker']}</label>
    <input id="tyre-q" type="search" inputmode="numeric" autocomplete="off" placeholder="{t['filter_ph']}" class="mt-3 w-full rounded-xl bg-zinc-950 px-4 py-3 text-lg text-zinc-100 ring-1 ring-zinc-700 placeholder:text-zinc-600 focus:outline-none focus:ring-brand">
    <div class="-mx-5 mt-3 flex gap-2 overflow-x-auto px-5 pb-1 sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0"><button type="button" data-rim="" class="{btn} bg-brand text-zinc-950">{t['all']}</button>{rims}</div>
    <p id="tyre-count" class="mt-3 text-sm font-semibold text-zinc-300" aria-live="polite">{UI[t['lang']]['shown'].format(len(SIZES))}</p>
    <p class="mt-3 text-sm text-zinc-400">{t['hint']} <a href="/blog/saburavis-zoma-rogor-wavikitkhot/" class="text-brand hover:text-amber-400">{t['hint_link']}</a></p>
  </div>"""


def filter_js(t):
    return f"""<script>
  (function () {{
    var q = document.getElementById('tyre-q'), box = document.getElementById('tyre-filter'), rim = '';
    var chips = document.querySelectorAll('#tyre-grid [data-size]'), rows = document.querySelectorAll('#tyre-grid [data-row]');
    var none = document.getElementById('tyre-none'), waText = {json.dumps(t['wa_size'])};
    function digits(s) {{ return (s || '').replace(/[^0-9]/g, ''); }}
    function run() {{
      var v = q.value, m = v.match(/r\\s*(\\d{{2}})/i), rq = m ? m[1] : '', d = digits(m ? v.replace(m[0], '') : v), shown = 0;
      chips.forEach(function (c) {{
        var ok = (!rim || c.dataset.rim === rim) && (!rq || c.dataset.rim === rq) && (!d || c.dataset.size.indexOf(d) === 0);
        c.hidden = !ok; if (ok) shown++;
      }});
      rows.forEach(function (r) {{ r.hidden = !r.querySelector('[data-size]:not([hidden])'); }});
      none.hidden = shown > 0;
      document.getElementById('tyre-count').textContent = {json.dumps(UI[t['lang']]['shown'])}.replace('{{}}', shown);
      if (!shown) none.querySelector('a').href = 'https://wa.me/{WA}?text=' + encodeURIComponent(waText.replace('{{}}', q.value || ('R' + rim)));
    }}
    q.addEventListener('input', run);
    box.querySelectorAll('[data-rim]').forEach(function (b) {{
      b.addEventListener('click', function () {{
        rim = b.dataset.rim;
        box.querySelectorAll('[data-rim]').forEach(function (x) {{ x.classList.toggle('bg-brand', x === b); x.classList.toggle('text-zinc-950', x === b); }});
        run();
      }});
    }});
  }})();
</script>"""


def size_grid(t):
    ui = UI[t["lang"]]
    tile = ("flex min-h-12 items-center justify-center rounded-xl bg-zinc-950 px-2 py-3 text-center font-semibold tabular-nums "
            "ring-1 ring-zinc-800 transition hover:text-brand hover:ring-brand active:scale-95")
    out = []
    for r in RIMS:
        rs = [s for s in SIZES if s["r"] == r]
        tiles = "".join(f'<a data-size="{s["w"]}{s["p"]}{s["r"]}" data-rim="{s["r"]}" href="{size_url(s)}" class="{tile}">{s["label"]}</a>' for s in rs)
        out.append(f'''<section data-row class="rounded-2xl bg-zinc-900/70 p-4 ring-1 ring-zinc-800 sm:p-5">
    <div class="flex items-baseline justify-between gap-3">
      <h3 class="text-xl font-bold font-head"><a href="{rim_url(r)}" class="hover:text-brand">R{r}</a> <span class="text-sm font-normal text-zinc-400">· {r}″ {ui['rim']} · {n_sizes(t['lang'], len(rs))}</span></h3>
      <a href="{rim_url(r)}" class="shrink-0 text-sm font-semibold text-brand hover:text-amber-400">{ui['all_of'].format(r)}</a>
    </div>
    <div class="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">{tiles}</div>
  </section>''')
    none = (f'<p id="tyre-none" hidden class="rounded-xl bg-zinc-900 p-4 text-zinc-300 ring-1 ring-zinc-800">{t["notfound"]} '
            f'<a href="https://wa.me/{WA}" target="_blank" rel="noopener" class="font-semibold text-[#25D366] hover:opacity-90">WhatsApp →</a></p>')
    return '<div id="tyre-grid" class="mt-6 space-y-4">' + "".join(out) + none + "</div>"


def build_hub(lang):
    t = dict(HUB_T[lang], lang=lang)
    url = HUB_URLS[lang]
    types = "".join(
        f'<div class="rounded-2xl bg-zinc-900 p-5 ring-1 ring-zinc-800"><h3 class="text-lg font-bold font-head">{n}</h3><p class="mt-1.5 text-sm text-zinc-400">{d}</p>'
        + (f'<a href="{link}" class="mt-3 inline-flex text-sm font-semibold text-brand hover:text-amber-400">{t["more"]}</a>' if link else "") + "</div>"
        for n, d, link in t["types"])
    body = f"""<!-- Hero -->
<section class="mx-auto max-w-6xl px-4 pt-6">
  <div class="grid items-stretch gap-8 rounded-3xl bg-gradient-to-br from-zinc-900 to-zinc-900/40 p-6 ring-1 ring-zinc-800 sm:p-10 lg:grid-cols-2">
    <div class="flex flex-col">
      <h1 class="text-3xl font-bold font-head break-words sm:text-5xl">{t['h1']}</h1>
      <p class="mt-4 leading-relaxed text-zinc-300">{t['lead']}</p>
      <div class="mt-6 flex flex-wrap gap-3">{btn_call()}{btn_wa(t['wa_generic'])}</div>
    </div>
    <div class="relative h-60 overflow-hidden rounded-2xl ring-1 ring-zinc-800 sm:h-72 lg:h-auto lg:min-h-80"><picture><source srcset="/assets/van-rear.avif" type="image/avif"><source srcset="/assets/van-rear.webp" type="image/webp"><img fetchpriority="high" src="/assets/van-rear.jpg" alt="{escape(t['h1'])}" class="absolute inset-0 h-full w-full object-cover"></picture></div>
  </div>
  {filter_html(t)}
</section>

<section class="mx-auto max-w-6xl px-4 py-12">
  <h2 class="text-2xl font-bold font-head sm:text-3xl">{t['popular']}</h2>
  {size_grid(t)}
</section>

<section class="mx-auto max-w-6xl px-4 py-6">
  <div class="grid gap-8 rounded-3xl bg-zinc-900 p-6 ring-1 ring-zinc-800 sm:p-10 lg:grid-cols-2">
    <div><h2 class="text-2xl font-bold font-head sm:text-3xl">{t['when_h']}</h2><p class="mt-3 text-zinc-300">{t['when_p']}</p>
      <div class="mt-6 flex flex-wrap gap-3">{btn_call()}{btn_wa(t['wa_generic'])}</div></div>
    <div>{ul(t['when'])}</div>
  </div>
</section>

<section class="mx-auto max-w-6xl px-4 py-6">
  <h2 class="text-2xl font-bold font-head sm:text-3xl">{t['how']}</h2>
  {steps(t['steps'])}
</section>

<section class="mx-auto max-w-6xl px-4 py-12">
  <h2 class="text-2xl font-bold font-head sm:text-3xl">{t['types_h']}</h2>
  <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{types}</div>
  <div class="mt-8 flex flex-col gap-4 rounded-3xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30 sm:flex-row sm:items-center sm:justify-between">
    <div><h2 class="text-xl font-bold font-head">{t['sos_h']}</h2><p class="mt-2 max-w-2xl text-zinc-300">{t['sos_p']}</p>
      <a href="{t['sos_link'][1]}" class="mt-3 inline-flex text-sm font-semibold text-brand hover:text-amber-400">{t['sos_link'][0]}</a></div>
    <div class="flex shrink-0 flex-col gap-3">{btn_call()}</div>
  </div>
</section>

<section class="mx-auto max-w-6xl px-4 pb-6">
  <h2 class="text-2xl font-bold font-head sm:text-3xl">{t['rims_h']}</h2>
  <div class="mt-6 grid grid-cols-4 gap-3 sm:grid-cols-8">{''.join(f'<a href="{rim_url(r)}" class="flex flex-col items-center justify-center rounded-2xl bg-zinc-900 px-2 py-4 ring-1 ring-zinc-800 transition hover:ring-brand active:scale-95"><span class="text-2xl font-extrabold font-head">R{r}</span><span class="mt-1 text-xs text-zinc-400">{n_sizes(lang, sum(1 for x in SIZES if x["r"] == r))}</span></a>' for r in RIMS)}</div>
</section>

<section class="mx-auto max-w-3xl px-4 py-12">
  <h2 class="text-2xl font-bold font-head sm:text-3xl">{t['faq_h']}</h2>
  {faq_html(t['faq'])}
</section>
{filter_js(t)}
"""
    service = {"@context": "https://schema.org", "@type": "Service", "serviceType": t["service"], "name": t["h1"],
               "description": t["desc"], "areaServed": {"@type": "City", "name": "Tbilisi"}, "provider": PROVIDER,
               "hasOfferCatalog": {"@type": "OfferCatalog", "name": t["popular"], "itemListElement": [
                   {"@type": "Offer", "itemOffered": {"@type": "Service", "name": f"{HUB_T['ka']['h1'].split()[0]} {s['label']}", "url": SITE + size_url(s)}} for s in SIZES]}}
    alternates = [("ka", HUB_URLS["ka"]), ("en", HUB_URLS["en"]), ("ru", HUB_URLS["ru"]), ("x-default", HUB_URLS["ka"])]
    html = page(lang, url=url, title=t["title"], desc=t["desc"], keywords=t["keywords"], alternates=alternates, image="van-rear",
                schema=[service, faq_ld(t["faq"])], crumbs=[(t["crumbs"][0], t["home"]), (t["crumbs"][1], None)],
                body=body, nav_urls=HUB_URLS)
    out = ROOT / "saburavebi" / LANG_FILE[lang]
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ size pages (Georgian)
def build_size(s):
    L = s["label"]
    url = size_url(s)
    sim = similar(s)
    sim_labels = ", ".join(o["label"] for o in sim)
    faq = [(f"რა ღირს საბურავი {L}?", "ფასი დამოკიდებულია იმაზე, ახალია თუ მეორადი, ასევე სეზონსა და მწარმოებელზე. დაგვირეკეთ ან მოგვწერეთ WhatsApp-ზე — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს."),
           (f"შეგიძლიათ {L} საბურავის მოტანა და ადგილზე დაყენება?", "დიახ — საბურავს მოგიტანთ თბილისის ნებისმიერ უბანში, ადგილზე დაგიყენებთ და დავაბალანსებთ. ვმუშაობთ 24/7."),
           (f"{L}-ის ნაცვლად სხვა ზომის დაყენება შეიძლება?",
            "დასაშვები ალტერნატივა დამოკიდებულია ავტომობილის მწარმოებლის მითითებაზე."
            + (f" მსგავსი დიამეტრის ზომებია: {sim_labels}." if sim else "")
            + " შეცვლამდე შეამოწმეთ ავტომობილის სახელმძღვანელო.")]
    wa = HUB_T["ka"]["wa_size"].format(L)
    rows = [("სიგანე", f"{s['w']} მმ"), ("პროფილი", f"{s['p']}% — გვერდის სიმაღლე ≈ {s['sidewall']} მმ"),
            ("დისკის დიამეტრი", f"{s['r']}″ ({s['rim_mm']} მმ)"), ("საბურავის სრული დიამეტრი", f"≈ {s['diameter']} მმ")]
    table = "".join(f'<tr class="border-b border-zinc-800 last:border-0"><th class="py-3 pr-4 text-left font-medium text-zinc-400">{a}</th><td class="py-3 font-semibold">{b}</td></tr>' for a, b in rows)
    same_rim = [o for o in SIZES if o["r"] == s["r"] and o is not s]
    sim_block = (f"""
    <h2 class="mt-10 text-2xl font-bold font-head">მსგავსი ზომები</h2>
    <p class="mt-4 leading-relaxed text-zinc-300">ეს ზომები იმავე R{s['r']} დისკზე ჯდება და მათი სრული დიამეტრი {L}-ის მსგავსია (±3%-ის ფარგლებში). სხვა ზომის დაყენებამდე შეამოწმეთ, რას უშვებს თქვენი ავტომობილის მწარმოებელი.</p>
    <div class="mt-4 flex flex-wrap gap-2">{''.join(chip(o) for o in sim)}</div>""" if sim else "")
    body = f"""<!-- Hero card -->
<section class="mx-auto max-w-6xl px-4 pt-6">
  <div class="grid items-stretch gap-8 rounded-3xl bg-gradient-to-br from-zinc-900 to-zinc-900/40 p-6 ring-1 ring-zinc-800 sm:p-10 lg:grid-cols-2">
    <div class="flex flex-col">
      <p class="text-sm font-semibold uppercase tracking-wider text-brand">საბურავები</p>
      <h1 class="mt-2 text-3xl font-bold font-head break-words sm:text-5xl">საბურავები {L}</h1>
      <p class="mt-4 leading-relaxed text-zinc-300">ახალი და მეორადი საბურავები {L} ზომაში — ზაფხულის, ზამთრის და ყველა სეზონის. მოგიტანთ, დაგიყენებთ და დავაბალანსებთ ადგილზე.</p>
      <div class="mt-5 flex flex-wrap gap-2 text-sm"><span class="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/15">ახალი</span><span class="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/15">მეორადი</span><span class="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/15">ზამთრის</span><span class="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/15">ზაფხულის / ყველა სეზონის</span></div>
      <div class="mt-6 flex flex-wrap gap-3">{btn_call()}{btn_wa(wa)}</div>
    </div>
    <div class="relative h-60 overflow-hidden rounded-2xl ring-1 ring-zinc-800 sm:h-72 lg:h-auto lg:min-h-80"><picture><source srcset="/assets/cover.avif" type="image/avif"><source srcset="/assets/cover.webp" type="image/webp"><img loading="lazy" src="/assets/cover.jpg" alt="საბურავები {L}" class="absolute inset-0 h-full w-full object-cover"></picture></div>
  </div>
</section>

<!-- Content -->
<section class="mx-auto grid max-w-6xl gap-10 px-4 py-12 lg:grid-cols-3">
  <div class="lg:col-span-2">
    <p class="text-lg leading-relaxed text-zinc-300">{kind(s)[1]}</p>

    <h2 class="mt-10 text-2xl font-bold font-head">ზომა {L} — მონაცემები</h2>
    <table class="mt-5 w-full text-sm"><tbody>{table}</tbody></table>
    <p class="mt-3 text-sm text-zinc-500">მონაცემები გამოთვლილია ზომის მიხედვით; კონკრეტული მოდელის ზუსტი ზომა შეიძლება ოდნავ განსხვავდებოდეს.</p>

    <h2 class="mt-10 text-2xl font-bold font-head">რას მოიცავს მომსახურება</h2>
    {ul([f"საბურავის მიწოდება {L} ზომაში თქვენს ლოკაციაზე", "საბურავის ჩაცმა დისკზე და ბორბლის დაყენება",
         '<a href="/services/balansireba/" class="text-brand hover:text-amber-400">ბორბლების ბალანსირება</a>', "წნევის შემოწმება"])}

    <h2 class="mt-10 text-2xl font-bold font-head">როდის გჭირდებათ საბურავის შეცვლა</h2>
    {ul(WHEN_REPLACE[:5])}
    <p class="mt-4 text-zinc-300">ნებისმიერ ამ შემთხვევაში დაგვირეკეთ — {L} საბურავს მოგიტანთ და ადგილზე გამოგიცვლით. <a href="/blog/rodis-unda-sheicvalos-saburavi/" class="text-brand hover:text-amber-400">დაწვრილებით: როდის უნდა შეიცვალოს საბურავი →</a></p>
{sim_block}

    <h2 class="mt-10 text-2xl font-bold font-head">ასევე შეიძლება დაგჭირდეთ</h2>
    {ul(['<a href="/services/sezonuri-saburavebis-shecvla/" class="text-brand hover:text-amber-400">საბურავების სეზონური შეცვლა ადგილზე</a>',
         '<a href="/blog/saburavis-zoma-rogor-wavikitkhot/" class="text-brand hover:text-amber-400">როგორ წავიკითხოთ საბურავის ზომა</a>',
         '<a href="/blog/rodis-unda-sheicvalos-saburavi/" class="text-brand hover:text-amber-400">როდის უნდა შეიცვალოს საბურავი</a>'])}

    <h2 class="mt-10 text-2xl font-bold font-head">ხშირად დასმული კითხვები</h2>
    {faq_html(faq)}
  </div>

  <aside class="lg:col-span-1">
    <div class="sticky top-24 space-y-6">
      <div class="rounded-2xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30">
        <h2 class="text-xl font-bold font-head">გჭირდებათ {L}?</h2>
        <p class="mt-2 text-sm text-zinc-300">დაგვირეკეთ ან მოგვწერეთ — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს.</p>
        <div class="mt-4 grid gap-2">{btn_call()}{btn_wa(wa)}</div>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">სხვა ზომები R{s['r']}</h2>
        <div class="mt-4 flex flex-wrap gap-2">{''.join(chip(o) for o in same_rim) or '<span class="text-sm text-zinc-400">—</span>'}</div>
        <a href="{rim_url(s['r'])}" class="mt-4 block text-sm font-semibold text-brand hover:text-amber-400">R{s['r']} საბურავები →</a>
        <a href="{HUB}" class="mt-2 block text-sm font-semibold text-brand hover:text-amber-400">ყველა ზომა →</a>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">საბურავები ტიპის მიხედვით</h2>
        <ul class="mt-4 space-y-2.5 text-sm">{''.join(f'<li><a href="{u}" class="text-zinc-300 hover:text-brand">{n}</a></li>' for n, u in CATEGORY_LINKS)}</ul>
      </div>
    </div>
  </aside>
</section>
"""
    service = {"@context": "https://schema.org", "@type": "Service", "serviceType": "საბურავების მიწოდება და მონტაჟი",
               "name": f"საბურავები {L} — მიწოდება და მონტაჟი",
               "description": f"საბურავები {L} თბილისში — ახალი და მეორადი, ზაფხულის და ზამთრის; მიწოდება, მონტაჟი და ბალანსირება ადგილზე, 24/7.",
               "areaServed": {"@type": "City", "name": "Tbilisi"}, "provider": PROVIDER}
    title = f"საბურავები {L} თბილისში — მიწოდება და მონტაჟი ადგილზე"
    desc = f"საბურავები {L} — ახალი და მეორადი, ზაფხულის და ზამთრის. მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ, თბილისში 24/7. ფასი და მარაგი: ☎ {TEL_FMT}"
    keywords = f"საბურავები {L}, {L}, {s['w']} {s['p']} {s['r']}, {L} ფასი, {L} ზამთრის, {L} მეორადი, R{s['r']} საბურავები"
    html = page("ka", url=url, title=title, desc=desc, keywords=keywords, alternates=[], image="cover",
                schema=[service, faq_ld(faq)], crumbs=[("მთავარი", "/index.html"), ("საბურავები", HUB), (f"R{s['r']}", rim_url(s["r"])), (L, None)],
                body=body, nav_urls={"ka": url, "en": HUB_URLS["en"], "ru": HUB_URLS["ru"]})
    out = ROOT / "saburavebi" / s["slug"] / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ category + rim pages (Georgian)
CATEGORY_LINKS = [("ახალი საბურავები", "/saburavebi/axali-saburavebi/"), ("მეორადი საბურავები", "/saburavebi/meoradi-saburavebi/"),
                  ("ზამთრის საბურავები", "/saburavebi/zamtris-saburavebi/"), ("ზაფხულის და ყველა სეზონის", "/saburavebi/zapkhulis-saburavebi/")]

PRICE_A = "ფასი დამოკიდებულია ზომაზე, სეზონზე და მწარმოებელზე. მოგვწერეთ ზომა WhatsApp-ზე ან დაგვირეკეთ — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს."

CATEGORIES = [
    dict(slug="axali-saburavebi", img="cover", h1="ახალი საბურავები",
         title="ახალი საბურავები თბილისში — ზომების მიხედვით, მიწოდება და მონტაჟი ადგილზე",
         desc=f"ახალი საბურავები თბილისში — ზაფხულის, ზამთრის და ყველა სეზონის, {RIM_RANGE}. მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ, 24/7.",
         keywords="ახალი საბურავები, ახალი საბურავები თბილისში, საბურავების ყიდვა, საბურავები ფასი, ახალი საბურავები ზომით",
         intro="ახალი საბურავი მაქსიმალურ უსაფრთხოებას გაძლევთ: სრული სიღრმის პროტექტორი, მოკლე დამუხრუჭების მანძილი და ხანგრძლივი მომსახურება. გვითხარით ზომა — შევარჩევთ ვარიანტებს თქვენი ბიუჯეტისა და სეზონის მიხედვით და ადგილზე დაგიყენებთ.",
         list_h="რატომ ახალი საბურავი",
         items=["სრული სიღრმის პროტექტორი — საუკეთესო მოჭიდება სველ გზაზე", "ახალი, ელასტიკური რეზინი",
                "ხანგრძლივი მომსახურება სწორი წნევისა და ბალანსირების პირობებში", "ზაფხულის, ზამთრის და ყველა სეზონის ვარიანტები"],
         tip="რჩევა: ახალ საბურავზეც შეამოწმეთ DOT კოდი — ოთხნიშნა რიცხვი, რომელიც დამზადების კვირასა და წელს აჩვენებს.",
         faq=[("რა ზომის ახალი საბურავები გაქვთ?", f"ყველაზე პოპულარული ზომები {RIM_RANGE}. თუ თქვენი ზომა სიაში არ არის, დაგვიკავშირდით — მოძიებაში დაგეხმარებით."),
              ("ოთხივე საბურავი ერთად უნდა შევცვალო?", "საუკეთესოა ოთხივე ერთად, მინიმუმ კი — ორი, ერთ ღერძზე. ახალი საბურავები სჯობს უკანა ღერძზე დააყენოთ."),
              ("რა ღირს ახალი საბურავი?", PRICE_A)]),
    dict(slug="meoradi-saburavebi", img="van-rear", h1="მეორადი საბურავები",
         title="მეორადი საბურავები თბილისში — შემოწმებული, მონტაჟით ადგილზე",
         desc=f"მეორადი საბურავები თბილისში ხელმისაწვდომ ფასად, {RIM_RANGE} — შემოწმებული პროტექტორი და ასაკი. მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ, 24/7.",
         keywords="მეორადი საბურავები, მეორადი საბურავები თბილისში, იაფი საბურავები, მეორადი საბურავების ყიდვა, მეორადი ზამთრის საბურავები",
         intro="კარგ მდგომარეობაში მყოფი მეორადი საბურავი ახლის ღირსეული ალტერნატივაა ნაკლებ ფასად — განსაკუთრებით, როცა მხოლოდ ერთი ან ორი საბურავის შეცვლა გჭირდებათ ან დროებით გამოსავალს ეძებთ.",
         list_h="რას ვამოწმებთ მეორად საბურავზე",
         items=["პროტექტორის სიღრმეს და თანაბარ ცვეთას", "დამზადების თარიღს (DOT კოდს)",
                "გვერდით კედელს — ბზარებისა და გამობერვის გარეშე", "ჰერმეტულობას და წინა შეკეთებებს"],
         list2_h="როდის არის მეორადი საბურავი კარგი არჩევანი",
         items2=["ერთი საბურავი დაზიანდა, დანარჩენები კი ჯერ კიდევ კარგია — მეორადით წყვილს შეარჩევთ",
                 "გჭირდებათ დროებითი გამოსავალი, სანამ ახალს იყიდით", "ავტომობილს იშვიათად იყენებთ ან გაყიდვას აპირებთ",
                 "ბიუჯეტი შეზღუდულია, მაგრამ უსაფრთხოების დათმობა არ გინდათ"],
         tip="მეორად ზამთრის საბურავზე პროტექტორი სასურველია მინიმუმ 4 მმ იყოს, ზაფხულისაზე — მინიმუმ 3 მმ.",
         faq=[("მეორადი საბურავი უსაფრთხოა?", "მეორად საბურავებს ვარჩევთ კარგ მდგომარეობაში — საკმარისი პროტექტორით და დაზიანების გარეშე. დაყენებამდე შეგიძლიათ თავად დაათვალიეროთ."),
              ("შეიძლება მხოლოდ ერთი მეორადი საბურავის ყიდვა?", "დიახ. ასეთ შემთხვევაში ვცდილობთ, დანარჩენის მსგავსი პროტექტორის საბურავი შევარჩიოთ, რომ ერთ ღერძზე ბორბლები თანაბარი იყოს."),
              ("რა ღირს მეორადი საბურავი?", "ფასი დამოკიდებულია ზომაზე, პროტექტორის მდგომარეობასა და მწარმოებელზე. მოგვწერეთ ზომა — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს.")]),
    dict(slug="zamtris-saburavebi", img="cover", h1="ზამთრის საბურავები",
         title="ზამთრის საბურავები თბილისში — ყიდვა, მიწოდება და მონტაჟი ადგილზე",
         desc=f"ზამთრის საბურავები თბილისში — ახალი და მეორადი, {RIM_RANGE}. მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ — რიგში დგომის გარეშე. 24/7.",
         keywords="ზამთრის საბურავები, ზამთრის საბურავები თბილისში, ზამთრის საბურავების ყიდვა, მეორადი ზამთრის საბურავები, ზამთრის საბურავები ფასი",
         intro="როცა ტემპერატურა 7°C-ზე დაბლა ეცემა, ზამთრის საბურავი ზაფხულისაზე უკეთ იჭერს გზას — სველ, ცივ და თოვლიან ასფალტზე. შეარჩიეთ ზომა — მოგიტანთ და ადგილზე დაგიყენებთ.",
         list_h="რით გამოირჩევა ზამთრის საბურავი",
         items=["რბილი რეზინი, რომელიც სიცივეში ელასტიკურობას ინარჩუნებს", "ღრმა პროტექტორი და წვრილი ჭრილები თოვლსა და ყინულზე მოსაჭიდად",
                "უკეთესი დამუხრუჭება ცივ და სველ გზაზე", "მარკირება M+S ან მთისა და ფიფქის სიმბოლო (3PMSF)"],
         tip='დაწვრილებით: <a href="/blog/zamtris-saburavebi-rodis-shevcvalot/" class="text-brand hover:text-amber-400">ზამთრის საბურავები — როდის შევცვალოთ?</a> · <a href="/services/sezonuri-saburavebis-shecvla/" class="text-brand hover:text-amber-400">საბურავების სეზონური შეცვლა ადგილზე</a>',
         faq=[("როდის დავაყენო ზამთრის საბურავები?", "როცა საშუალო დღიური ტემპერატურა სტაბილურად დაახლოებით 7°C-ზე დაბლა ეცემა — თბილისში ეს ჩვეულებრივ ნოემბერშია. მთის გზებზე წასვლამდე სჯობს უფრო ადრე."),
              ("ზამთრის საბურავები ოთხივე ბორბალზე უნდა დავაყენო?", "დიახ — ოთხივე ბორბალზე, რომ ავტომობილი დამუხრუჭებისა და მოხვევისას სტაბილური დარჩეს."),
              ("მეორადი ზამთრის საბურავები გაქვთ?", "დიახ, გვაქვს როგორც ახალი, ისე მეორადი ზამთრის საბურავები. მეორადზე პროტექტორი სასურველია მინიმუმ 4 მმ იყოს.")]),
    dict(slug="zapkhulis-saburavebi", img="service", h1="ზაფხულის და ყველა სეზონის საბურავები",
         title="ზაფხულის და ყველა სეზონის საბურავები თბილისში — მიწოდება და მონტაჟი",
         desc=f"ზაფხულის და ყველა სეზონის საბურავები თბილისში — ახალი და მეორადი, {RIM_RANGE}. მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ, 24/7.",
         keywords="ზაფხულის საბურავები, ყველა სეზონის საბურავები, ზაფხულის საბურავები თბილისში, საბურავები ყველა სეზონისთვის",
         intro="ზაფხულის საბურავი თბილ ამინდში საუკეთესო მართვასა და დამუხრუჭებას იძლევა, ყველა სეზონის საბურავი კი თბილისის რბილი ზამთრისთვისაც ხშირად საკმარისია. გვითხარით ზომა და როგორ იყენებთ ავტომობილს — სწორ ვარიანტს შევარჩევთ.",
         list_h="როგორ ავირჩიოთ",
         items=["ზაფხულის — თუ ზამთარში ცალკე ზამთრის საბურავებს იყენებთ", "ყველა სეზონის — თუ ძირითადად ქალაქში მოძრაობთ და მთაში იშვიათად ადიხართ",
                "დაბალპროფილიანი — სპორტული მართვისთვის, მაგრამ ორმოებში უფრო ადვილად ზიანდება",
                "როცა ტემპერატურა სტაბილურად 7°C-ს გადააჭარბებს, ზამთრის საბურავები ზაფხულისაზე შეცვალეთ"],
         tip='ზომის შერჩევაში დაგეხმარებათ: <a href="/blog/saburavis-zoma-rogor-wavikitkhot/" class="text-brand hover:text-amber-400">როგორ წავიკითხოთ საბურავის ზომა</a>',
         faq=[("ყველა სეზონის საბურავი ზამთარს გაუძლებს?", "თბილისის რბილი ზამთრისთვის ხარისხიანი ყველა სეზონის საბურავი ხშირად საკმარისია, მაგრამ თოვლსა და ყინულზე და მთის გზებზე ზამთრის საბურავი გაცილებით უკეთესია."),
              ("როდის დავაბრუნო ზაფხულის საბურავები?", "როცა საშუალო დღიური ტემპერატურა სტაბილურად 7°C-ს გადააჭარბებს — თბილისში ჩვეულებრივ მარტის ბოლოს ან აპრილში."),
              ("რა ღირს ზაფხულის საბურავი?", PRICE_A)]),
]


def rim_desc(r):
    if r <= 14:
        return "პატარა და კომპაქტური ავტომობილებისთვის"
    if r <= 16:
        return "ყველაზე გავრცელებული ზომები სედანებისა და კომპაქტური ავტომობილებისთვის"
    if r == 17:
        return "სედანებისთვის, კროსოვერებისა და ჯიპებისთვის"
    if r <= 19:
        return "ბიზნეს კლასის ავტომობილებისთვის, კროსოვერებისა და ჯიპებისთვის"
    return "პრემიუმ ავტომობილებისა და დიდი ჯიპებისთვის — ხშირად დაბალპროფილიანი"


def landing(url, *, h1, kicker, intro, img, wa, sections, faq, sizes, sizes_h, crumbs, title, desc, keywords, service_name):
    chips = "".join(chip(x) for x in sizes)
    body = f"""<!-- Hero card -->
<section class="mx-auto max-w-6xl px-4 pt-6">
  <div class="grid items-stretch gap-8 rounded-3xl bg-gradient-to-br from-zinc-900 to-zinc-900/40 p-6 ring-1 ring-zinc-800 sm:p-10 lg:grid-cols-2">
    <div class="flex flex-col">
      <p class="text-sm font-semibold uppercase tracking-wider text-brand">{kicker}</p>
      <h1 class="mt-2 text-3xl font-bold font-head break-words sm:text-5xl">{h1}</h1>
      <p class="mt-4 leading-relaxed text-zinc-300">{intro}</p>
      <div class="mt-6 flex flex-wrap gap-3">{btn_call()}{btn_wa(wa)}</div>
    </div>
    <div class="relative h-60 overflow-hidden rounded-2xl ring-1 ring-zinc-800 sm:h-72 lg:h-auto lg:min-h-80"><picture><source srcset="/assets/{img}.avif" type="image/avif"><source srcset="/assets/{img}.webp" type="image/webp"><img fetchpriority="high" src="/assets/{img}.jpg" alt="{escape(h1)}" class="absolute inset-0 h-full w-full object-cover"></picture></div>
  </div>
</section>

<section class="mx-auto max-w-6xl px-4 py-12">
  <h2 class="text-2xl font-bold font-head sm:text-3xl">{sizes_h}</h2>
  <div class="mt-6 flex flex-wrap gap-2">{chips}</div>
  <p class="mt-4 text-sm text-zinc-400">თქვენი ზომა არ ჩანს? <a href="{wa_link(wa)}" target="_blank" rel="noopener" class="font-semibold text-brand hover:text-amber-400">მოგვწერეთ WhatsApp-ზე →</a> · <a href="{HUB}" class="font-semibold text-brand hover:text-amber-400">ზომის ფილტრი →</a></p>
</section>

<section class="mx-auto grid max-w-6xl gap-10 px-4 pb-12 lg:grid-cols-3">
  <div class="lg:col-span-2">
{sections}
    <h2 class="mt-10 text-2xl font-bold font-head">როდის გჭირდებათ საბურავის შეცვლა</h2>
    {ul(WHEN_REPLACE)}

    <h2 class="mt-10 text-2xl font-bold font-head">როგორ მუშაობს</h2>
    {steps(HUB_T['ka']['steps'])}

    <h2 class="mt-10 text-2xl font-bold font-head">ხშირად დასმული კითხვები</h2>
    {faq_html(faq)}
  </div>
  <aside class="lg:col-span-1">
    <div class="sticky top-24 space-y-6">
      <div class="rounded-2xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30">
        <h2 class="text-xl font-bold font-head">გჭირდებათ საბურავი?</h2>
        <p class="mt-2 text-sm text-zinc-300">მოგვწერეთ ზომა — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს. ვმუშაობთ 24/7.</p>
        <div class="mt-4 grid gap-2">{btn_call()}{btn_wa(wa)}</div>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">საბურავები ტიპის მიხედვით</h2>
        <ul class="mt-4 space-y-2.5 text-sm">{''.join(f'<li><a href="{u}" class="text-zinc-300 hover:text-brand">{n}</a></li>' for n, u in CATEGORY_LINKS if u != url)}</ul>
        <h2 class="mt-6 text-lg font-bold font-head">დისკის ზომა</h2>
        <div class="mt-3 flex flex-wrap gap-2">{''.join(f'<a href="{rim_url(r)}" class="rounded-full bg-zinc-950 px-3 py-1.5 text-sm font-semibold ring-1 ring-zinc-800 hover:text-brand hover:ring-brand/60">R{r}</a>' for r in RIMS)}</div>
      </div>
    </div>
  </aside>
</section>
"""
    service = {"@context": "https://schema.org", "@type": "Service", "serviceType": "საბურავების მიწოდება და მონტაჟი", "name": service_name,
               "description": desc, "areaServed": {"@type": "City", "name": "Tbilisi"}, "provider": PROVIDER}
    html = page("ka", url=url, title=title, desc=desc, keywords=keywords, alternates=[], image=img,
                schema=[service, faq_ld(faq)], crumbs=crumbs, body=body, nav_urls={"ka": url, "en": HUB_URLS["en"], "ru": HUB_URLS["ru"]})
    out = ROOT / url.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def build_category(c):
    url = f"/saburavebi/{c['slug']}/"
    sec = f'    <h2 class="text-2xl font-bold font-head">{c["list_h"]}</h2>\n    {ul(c["items"])}\n'
    if c.get("items2"):
        sec += f'\n    <h2 class="mt-10 text-2xl font-bold font-head">{c["list2_h"]}</h2>\n    {ul(c["items2"])}\n'
    sec += f'    <p class="mt-4 text-zinc-300">{c["tip"]}</p>\n'
    landing(url, h1=c["h1"], kicker="საბურავები", intro=c["intro"], img=c["img"], wa=f"გამარჯობა, მაინტერესებს {c['h1'].lower()}",
            sections=sec, faq=c["faq"], sizes=SIZES, sizes_h="აირჩიეთ ზომა",
            crumbs=[("მთავარი", "/index.html"), ("საბურავები", HUB), (c["h1"], None)],
            title=c["title"], desc=c["desc"], keywords=c["keywords"], service_name=f"{c['h1']} თბილისში")


def build_rim(r):
    url = rim_url(r)
    sizes = [s for s in SIZES if s["r"] == r]
    rows = "".join(f'<tr class="border-b border-zinc-800 last:border-0"><td class="py-3 pr-4"><a href="{size_url(s)}" class="font-semibold text-brand hover:text-amber-400">{s["label"]}</a></td>'
                   f'<td class="py-3 pr-4 text-zinc-300">{s["w"]} მმ</td><td class="py-3 pr-4 text-zinc-300">{s["sidewall"]} მმ</td><td class="py-3 text-zinc-300">≈ {s["diameter"]} მმ</td></tr>' for s in sizes)
    sec = f"""    <h2 class="text-2xl font-bold font-head">R{r} ზომები</h2>
    <div class="mt-5 overflow-x-auto"><table class="w-full text-left text-sm"><thead><tr class="border-b border-zinc-700 text-zinc-400"><th class="py-2 pr-4 font-medium">ზომა</th><th class="py-2 pr-4 font-medium">სიგანე</th><th class="py-2 pr-4 font-medium">გვერდის სიმაღლე</th><th class="py-2 font-medium">სრული დიამეტრი</th></tr></thead><tbody>{rows}</tbody></table></div>
    <p class="mt-3 text-sm text-zinc-500">R{r} ნიშნავს {r}-დიუმიან ({round(r * 25.4)} მმ) დისკს. მონაცემები გამოთვლილია ზომის მიხედვით.</p>
"""
    faq = [(f"R{r} რას ნიშნავს?", f"R{r} ნიშნავს, რომ საბურავი {r}-დიუმიან ({round(r * 25.4)} მმ) დისკზე ჯდება; ასო R რადიალურ კონსტრუქციას აღნიშნავს."),
           (f"რა ღირს R{r} საბურავი?", PRICE_A),
           (f"R{r} საბურავს ადგილზე დამიყენებთ?", "დიახ — მოგიტანთ თბილისის ნებისმიერ უბანში, ადგილზე დაგიყენებთ და დავაბალანსებთ. ვმუშაობთ 24/7.")]
    landing(url, h1=f"R{r} საბურავები", kicker="საბურავები დისკის ზომით",
            intro=f"{r}-დიუმიანი დისკის საბურავები — {rim_desc(r)}. ახალი და მეორადი, ზაფხულის, ზამთრის და ყველა სეზონის. აირჩიეთ ზომა ან მოგვწერეთ WhatsApp-ზე.",
            img="cover", wa=f"გამარჯობა, მაინტერესებს R{r} საბურავები", sections=sec, faq=faq, sizes=sizes, sizes_h=f"R{r} საბურავების ზომები",
            crumbs=[("მთავარი", "/index.html"), ("საბურავები", HUB), (f"R{r}", None)],
            title=f"R{r} საბურავები თბილისში — ახალი და მეორადი, მონტაჟით ადგილზე",
            desc=f"R{r} ({r}-დიუმიანი) საბურავები თბილისში — {len(sizes)} ზომა, ახალი და მეორადი, ზაფხულის და ზამთრის. მოგიტანთ, დაგიყენებთ და დავაბალანსებთ ადგილზე, 24/7.",
            keywords=f"R{r} საბურავები, საბურავები R{r}, {r} დიუმიანი საბურავები, R{r} ზამთრის საბურავები, R{r} საბურავები ფასი",
            service_name=f"R{r} საბურავები თბილისში")


# ------------------------------------------------------------------ site-wide sync
def html_files():
    tracked = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    extra = [str(p.relative_to(ROOT)) for p in (ROOT / "saburavebi").glob("**/*.html")]
    return sorted(set(tracked) | set(extra))


def ensure_nav():
    for rel in html_files():
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        lang = re.search(r'<html lang="(\w+)"', s).group(1)
        # phones: the main menu is hidden, so add a compact "tyres" button next to the call button
        if 'data-mobile-tyres' not in s and '<div class="flex items-center gap-2">' in s:
            mob = (f'<a data-mobile-tyres href="{HUB_URLS[lang]}" class="rounded-lg bg-zinc-900 px-2.5 py-2 text-xs font-semibold '
                   f'ring-1 ring-zinc-700 hover:text-brand max-[379px]:px-2 md:hidden">{HUB_T[lang]["nav"]}</a>')
            s = s.replace('<div class="flex items-center gap-2">', '<div class="flex items-center gap-2">' + mob, 1)
            # make room on phones: slightly smaller logo text below the sm breakpoint
            s = s.replace('class="flex items-center gap-2 text-lg font-extrabold font-head"',
                          'class="flex items-center gap-2 text-base font-extrabold font-head max-[379px]:gap-1.5 max-[379px]:text-sm sm:text-lg"', 1)
            p.write_text(s, encoding="utf-8")
        m = re.search(r'(<div class="hidden items-center gap-6 text-sm font-medium md:flex">)(.*?)(</div>)', s, re.S)
        if not m or 'href="/saburavebi/' in m.group(2):
            continue
        link = f'<a href="{HUB_URLS[lang]}" class="hover:text-brand transition-colors">{HUB_T[lang]["nav"]}</a>'
        s = s[:m.end(1)] + link + s[m.end(1):]
        p.write_text(s, encoding="utf-8")


def sync_block(text, start, end, block, anchor_before):
    if start in text:
        return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda m: start + block + end, text, flags=re.S)
    i = text.index(anchor_before)
    return text[:i] + start + block + end + "\n" + text[i:]


def sync_homepages():
    for lang, f in LANG_FILE.items():
        t = HUB_T[lang]
        p = ROOT / f
        s = p.read_text(encoding="utf-8")
        chips = "".join(chip(x) for x in POPULAR) + "".join(
            f'<a href="{rim_url(r)}" class="rounded-full px-3 py-1.5 text-sm font-bold text-brand ring-1 ring-brand/40 transition hover:bg-brand hover:text-zinc-950">R{r}</a>' for r in RIMS)
        block = f"""
<section class="mx-auto max-w-6xl px-4 py-12">
  <div class="flex flex-wrap items-end justify-between gap-4">
    <div><h2 class="text-3xl font-bold font-head">{t['strip_h']}</h2><p class="mt-2 text-zinc-400">{t['strip_p']}</p></div>
    <a href="{HUB_URLS[lang]}" class="text-sm font-semibold text-brand hover:text-amber-400">{t['strip_all']}</a>
  </div>
  <div class="mt-6 flex flex-wrap gap-2">{chips}</div>
</section>
"""
        s = sync_block(s, "<!-- tyres:start -->", "<!-- tyres:end -->", block, "<!-- Why -->")
        p.write_text(s, encoding="utf-8")


def sync_sitemap():
    p = ROOT / "sitemap.xml"
    s = p.read_text(encoding="utf-8")
    from datetime import date
    today = date.today().isoformat()
    url = lambda loc, pr: f"  <url>\n    <loc>{SITE}{loc}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{pr}</priority>\n  </url>\n"
    block = ("\n" + url(HUB_URLS["ka"], "0.90") + url(HUB_URLS["en"], "0.70") + url(HUB_URLS["ru"], "0.70")
             + "".join(url(f"/saburavebi/{c['slug']}/", "0.85") for c in CATEGORIES)
             + "".join(url(rim_url(r), "0.80") for r in RIMS) + "".join(url(size_url(x), "0.70") for x in SIZES) + "  ")
    s = sync_block(s, "<!-- tyres:start -->", "<!-- tyres:end -->", block, "</urlset>")
    p.write_text(s, encoding="utf-8")


def sync_llms():
    p = ROOT / "llms.txt"
    s = p.read_text(encoding="utf-8")
    block = ("\n## Tyres (საბურავები) — sale, delivery and fitting\n"
             f"- Tyre catalogue by size, new and used, summer/winter/all-season; delivered, fitted and balanced on site in Tbilisi 24/7; price and stock by phone/WhatsApp {TEL_FMT}: {SITE}{HUB}\n"
             + "".join(f"- {c['h1']}: {SITE}/saburavebi/{c['slug']}/\n" for c in CATEGORIES)
             + "- By rim: " + ", ".join(f"[R{r}]({SITE}{rim_url(r)})" for r in RIMS) + "\n"
             + "- Sizes: " + ", ".join(f"[{x['label']}]({SITE}{size_url(x)})" for x in SIZES) + "\n")
    s = sync_block(s, "<!-- tyres:start -->", "<!-- tyres:end -->", block, "## Service area") if "## Service area" in s else s + "\n<!-- tyres:start -->" + block + "<!-- tyres:end -->\n"
    p.write_text(s, encoding="utf-8")


def main():
    # remove size pages that are no longer in tyres.json
    keep = {s["slug"] for s in SIZES} | {c["slug"] for c in CATEGORIES} | {f"r{r}" for r in RIMS}
    for d in (ROOT / "saburavebi").glob("*/"):
        if d.is_dir() and d.name not in keep:
            shutil.rmtree(d)
    for lang in LANG_FILE:
        build_hub(lang)
    for s in SIZES:
        build_size(s)
    for c in CATEGORIES:
        build_category(c)
    for r in RIMS:
        build_rim(r)
    ensure_nav()
    sync_homepages()
    sync_sitemap()
    sync_llms()
    print(f"built hub (ka/en/ru) + {len(CATEGORIES)} category + {len(RIMS)} rim + {len(SIZES)} size pages")


if __name__ == "__main__":
    main()
