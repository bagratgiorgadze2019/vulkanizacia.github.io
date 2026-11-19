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
LANG_HUB = {"ka": "/saburavebi/", "en": "/tyres/", "ru": "/shiny/"}
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


def rim_url(r, lang="ka"):
    return f"{LANG_HUB[lang]}r{r}/"


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


def size_url(s, lang="ka"):
    return f"{LANG_HUB[lang]}{s['slug']}/"


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
    nav = src[src.index("<!-- Nav -->"):src.index("<!-- Breadcrumb -->")].replace('\n<main id="main">', "")
    foot = src[src.index("<!-- Footer -->"):src.index("</body>")]  # <main> is added by build_md's a11y pass
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


def chip(s, active=False, lang="ka"):
    cls = "bg-brand text-zinc-950 font-bold" if active else "bg-zinc-900 text-zinc-200 ring-1 ring-zinc-800 hover:ring-brand/60 hover:text-brand"
    return f'<a href="{size_url(s, lang)}" class="rounded-full px-3 py-1.5 text-sm transition {cls}">{s["label"]}</a>'


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
        title="Tires in Tbilisi — new and used, delivered and fitted",
        desc="Tires in Tbilisi by size — new and used, summer, winter and all-season. We deliver, fit and balance them on the spot, 24/7.",
        keywords="tires Tbilisi, tyres Tbilisi, buy tires Tbilisi, winter tires Tbilisi, used tires Tbilisi, tire shop Tbilisi",
        crumbs=["Home", "Tires"], home="/index-en.html",
        h1="Tires in Tbilisi",
        lead="New and used tires — summer, winter and all-season. Choose your size and we deliver, fit and balance the tires on site. 24/7.",
        picker="Find tires by size", filter_ph="e.g. 205/55 R16 or 235/35", all="All",
        notfound="This size isn't listed — message us and we'll find it:",
        when_h="When you need a new tire", when_p="A tire replacement is often needed unexpectedly. The most common cases:",
        when=["The tire burst or the sidewall is damaged — this kind of damage can't be repaired", "The puncture is too large or on the sidewall",
              "A bulge appeared after hitting a pothole or a kerb", "The tread is worn — below 3 mm on summer tires, 4 mm on winter tires",
              "The tire has cracks, or it is over 6 years old and the rubber has hardened", "The winter or summer season has arrived",
              "The tire wears unevenly or vibration remains after balancing", "One tire is damaged and you need a matching one for the same axle"],
        rims_h="Tires by rim size",
        hint="The size is printed on the tire sidewall, e.g. 205/55 R16.", hint_link="How to read a tire size →",
        wa_size="Hello, I'm interested in tires {}", wa_generic="Hello, I'm interested in tires",
        popular="Popular sizes", how="How it works",
        steps=[("Choose your size", "Call or message us on WhatsApp with your tire size — we'll tell you the available options and the price."),
               ("We deliver", "We bring the tires to your home, office or roadside — anywhere in Tbilisi."),
               ("We fit them", "We mount the tires on your rims and fit the wheels on the spot."),
               ("We balance them", "We balance the wheels and check the pressure, so you are back on the road safely.")],
        types_h="Tires we offer",
        types=[("New tires", "New tires from different manufacturers — summer, winter and all-season.", None),
               ("Used tires", "Used tires in good condition at affordable prices.", None),
               ("Winter tires", "Tires made for snow and cold weather — fitted at your location.", "/services/sezonuri-saburavebis-shecvla/index-en.html"),
               ("Summer and all-season", "Tires for city driving in Tbilisi and long trips.", None)],
        more="Learn more →",
        sos_h="Tire burst on the road?",
        sos_p="If the tire can't be repaired, we bring a new or used tire in your size and fit it on the spot — even without a spare.",
        sos_link=("Mobile tire service →", "/services/modzravi-vulkanizacia/index-en.html"),
        faq_h="Frequently asked questions",
        faq=[("Where do I find my tire size?", "It is printed on the tire sidewall, for example 205/55 R16. It is also on the sticker in the driver's door frame or in the car manual."),
             ("How much does a tire cost?", "It depends on the size, season, manufacturer and whether it is new or used. Call us or send your size on WhatsApp — we'll tell you the available options and the price."),
             ("Do you also fit and balance the tires?", "Yes — we offer the full service: delivery, fitting and balancing. We agree the price with you in advance."),
             ("Are used tires safe?", "We choose used tires in good condition — with enough tread and no damage. You can inspect them yourself before fitting."),
             ("My size isn't on the list?", "Contact us — the list shows only the most popular sizes. We can help you find tires in other sizes too.")],
        service="Tire delivery and fitting",
        strip_h="Tires by size", strip_p="New and used tires — delivered, fitted and balanced on site.", strip_all="All sizes and details →",
        nav="Tires"),
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
HUB_URLS = dict(LANG_HUB)


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
    <p class="mt-3 text-sm text-zinc-400">{t['hint']} <a href="{blog_url("size", t["lang"])}" class="text-brand hover:text-amber-400">{t['hint_link']}</a></p>
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
    lg = t["lang"]
    tile = ("flex min-h-12 items-center justify-center rounded-xl bg-zinc-950 px-2 py-3 text-center font-semibold tabular-nums "
            "ring-1 ring-zinc-800 transition hover:text-brand hover:ring-brand active:scale-95")
    out = []
    for r in RIMS:
        rs = [s for s in SIZES if s["r"] == r]
        tiles = "".join(f'<a data-size="{s["w"]}{s["p"]}{s["r"]}" data-rim="{s["r"]}" href="{size_url(s, lg)}" class="{tile}">{s["label"]}</a>' for s in rs)
        out.append(f'''<section data-row class="rounded-2xl bg-zinc-900/70 p-4 ring-1 ring-zinc-800 sm:p-5">
    <div class="flex items-baseline justify-between gap-3">
      <h3 class="text-xl font-bold font-head"><a href="{rim_url(r, lg)}" class="hover:text-brand">R{r}</a> <span class="text-sm font-normal text-zinc-400">· {r}″ {ui['rim']} · {n_sizes(t['lang'], len(rs))}</span></h3>
      <a href="{rim_url(r, lg)}" class="shrink-0 text-sm font-semibold text-brand hover:text-amber-400">{ui['all_of'].format(r)}</a>
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
        for (n, d, _), link in zip(t["types"], [cat_url(k, lang) for k in ("new", "used", "winter", "summer")]))
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
  <div class="mt-6 grid grid-cols-4 gap-3 sm:grid-cols-8">{''.join(f'<a href="{rim_url(r, lang)}" class="flex flex-col items-center justify-center rounded-2xl bg-zinc-900 px-2 py-4 ring-1 ring-zinc-800 transition hover:ring-brand active:scale-95"><span class="text-2xl font-extrabold font-head">R{r}</span><span class="mt-1 text-xs text-zinc-400">{n_sizes(lang, sum(1 for x in SIZES if x["r"] == r))}</span></a>' for r in RIMS)}</div>
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
                   {"@type": "Offer", "itemOffered": {"@type": "Service", "name": SZ[lang]["h1"].format(L=s["label"]), "url": SITE + size_url(s, lang)}} for s in SIZES]}}
    alternates = [("ka", HUB_URLS["ka"]), ("en", HUB_URLS["en"]), ("ru", HUB_URLS["ru"]), ("x-default", HUB_URLS["ka"])]
    html = page(lang, url=url, title=t["title"], desc=t["desc"], keywords=t["keywords"], alternates=alternates, image="van-rear",
                schema=[service, faq_ld(t["faq"])], crumbs=[(t["crumbs"][0], t["home"]), (t["crumbs"][1], None)],
                body=body, nav_urls=HUB_URLS)
    out = ROOT / url.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ trilingual URLs + shared copy
LANGS = ("ka", "en", "ru")
CAT_SLUGS = {"new": {"ka": "axali-saburavebi", "en": "new-tyres", "ru": "novye-shiny"},
             "used": {"ka": "meoradi-saburavebi", "en": "used-tyres", "ru": "shiny-bu"},
             "winter": {"ka": "zamtris-saburavebi", "en": "winter-tyres", "ru": "zimnie-shiny"},
             "summer": {"ka": "zapkhulis-saburavebi", "en": "summer-all-season-tyres", "ru": "letnie-i-vsesezonnye-shiny"}}
KA_CAT_KEY = {v["ka"]: k for k, v in CAT_SLUGS.items()}
BLOG_SLUGS = {k: v for k, v in json.loads((ROOT / "tools" / "blog_slugs.json").read_text(encoding="utf-8")).items() if not k.startswith("_")}
HOME = {"ka": "/index.html", "en": "/index-en.html", "ru": "/index-ru.html"}


def cat_url(key, lang="ka"):
    return f"{LANG_HUB[lang]}{CAT_SLUGS[key][lang]}/"


def blog_url(key, lang="ka"):
    return f"/blog/{BLOG_SLUGS[key][lang]}/"


def svc_url(slug, lang="ka"):
    return f"/services/{slug}/" + ("" if lang == "ka" else LANG_FILE[lang])


def alts(urls):
    return [("ka", urls["ka"]), ("en", urls["en"]), ("ru", urls["ru"]), ("x-default", urls["ka"])]


def a(href, text):
    return f'<a href="{href}" class="text-brand hover:text-amber-400">{text}</a>'


def rim_range(lang):
    lo, hi = RIMS[0], RIMS[-1]
    return {"ka": f"R{lo}-დან R{hi}-მდე", "en": f"R{lo} to R{hi}", "ru": f"от R{lo} до R{hi}"}[lang]


PRICE = {"ka": "ფასი დამოკიდებულია ზომაზე, სეზონზე და მწარმოებელზე. მოგვწერეთ ზომა WhatsApp-ზე ან დაგვირეკეთ — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს.",
         "en": "The price depends on the size, season and manufacturer. Send us your size on WhatsApp or call — we'll tell you the available options and the price.",
         "ru": "Цена зависит от размера, сезона и производителя. Напишите размер в WhatsApp или позвоните — расскажем о вариантах в наличии и цене."}
WHEN = {"ka": WHEN_REPLACE, "en": HUB_T["en"]["when"], "ru": HUB_T["ru"]["when"]}
CATEGORY_NAMES = {"ka": {"new": "ახალი საბურავები", "used": "მეორადი საბურავები", "winter": "ზამთრის საბურავები", "summer": "ზაფხულის და ყველა სეზონის"},
                  "en": {"new": "New tyres", "used": "Used tyres", "winter": "Winter tyres", "summer": "Summer and all-season"},
                  "ru": {"new": "Новые шины", "used": "Шины б/у", "winter": "Зимние шины", "summer": "Летние и всесезонные"}}


def category_links(lang):
    return [(CATEGORY_NAMES[lang][k], cat_url(k, lang)) for k in CAT_SLUGS]


CATEGORY_LINKS = category_links("ka")


def kind_text(s, lang):
    k = kind(s)[0]
    L = s["label"]
    if lang == "ka":
        return kind(s)[1]
    T = {
        "en": {"low": f"{L} is a low-profile tire — often used on sporty and premium cars. Its low sidewall is easier to damage on potholes and kerbs, so replacing it is often sudden and urgent — we bring it and fit it on the spot.",
               "suv": f"{L} is a common size for SUVs and crossovers. Replacing a large wheel on site is especially convenient — no need to drive to a workshop.",
               "small": f"{L} is a common size for compact and mid-size cars — one of the most requested sizes in the city.",
               "mid": f"{L} is a common size for sedans and crossovers — one of the popular sizes in Tbilisi."},
        "ru": {"low": f"{L} — низкопрофильная шина, часто стоит на спортивных и премиальных автомобилях. Низкая боковина легче повреждается на ямах и бордюрах, поэтому замена часто нужна внезапно и срочно — привезём и установим на месте.",
               "suv": f"Размер {L} часто встречается на внедорожниках и кроссоверах. Замена большого колеса на месте особенно удобна — не нужно ехать в мастерскую.",
               "small": f"Размер {L} часто встречается на компактных автомобилях и машинах среднего класса — один из самых востребованных размеров в городе.",
               "mid": f"Размер {L} часто встречается на седанах и кроссоверах — один из популярных размеров в Тбилиси."},
    }
    return T[lang][k]


# ------------------------------------------------------------------ size pages
SZ = {
    "ka": dict(kicker="საბურავები", h1="საბურავები {L}",
               lead="ახალი და მეორადი საბურავები {L} ზომაში — ზაფხულის, ზამთრის და ყველა სეზონის. მოგიტანთ, დაგიყენებთ და დავაბალანსებთ ადგილზე.",
               badges=["ახალი", "მეორადი", "ზამთრის", "ზაფხულის / ყველა სეზონის"],
               data_h="ზომა {L} — მონაცემები",
               rows=[("სიგანე", "{w} მმ"), ("პროფილი", "{p}% — გვერდის სიმაღლე ≈ {sw} მმ"), ("დისკის დიამეტრი", "{r}″ ({mm} მმ)"), ("საბურავის სრული დიამეტრი", "≈ {d} მმ")],
               data_note="მონაცემები გამოთვლილია ზომის მიხედვით; კონკრეტული მოდელის ზუსტი ზომა შეიძლება ოდნავ განსხვავდებოდეს.",
               inc_h="რას მოიცავს მომსახურება",
               inc=["საბურავის მიწოდება {L} ზომაში თქვენს ლოკაციაზე", "საბურავის ჩაცმა დისკზე და ბორბლის დაყენება", "ბორბლების ბალანსირება", "წნევის შემოწმება"],
               when_h="როდის გჭირდებათ საბურავის შეცვლა", when_p="ნებისმიერ ამ შემთხვევაში დაგვირეკეთ — {L} საბურავს მოგიტანთ და ადგილზე გამოგიცვლით.",
               when_link="დაწვრილებით: როდის უნდა შეიცვალოს საბურავი →",
               sim_h="მსგავსი ზომები",
               sim_p="ეს ზომები იმავე R{r} დისკზე ჯდება და მათი სრული დიამეტრი {L}-ის მსგავსია (±3%-ის ფარგლებში). სხვა ზომის დაყენებამდე შეამოწმეთ, რას უშვებს თქვენი ავტომობილის მწარმოებელი.",
               also_h="ასევე შეიძლება დაგჭირდეთ",
               also=["საბურავების სეზონური შეცვლა ადგილზე", "როგორ წავიკითხოთ საბურავის ზომა", "როდის უნდა შეიცვალოს საბურავი"],
               faq_h="ხშირად დასმული კითხვები",
               faq=[("რა ღირს საბურავი {L}?", "ფასი დამოკიდებულია იმაზე, ახალია თუ მეორადი, ასევე სეზონსა და მწარმოებელზე. დაგვირეკეთ ან მოგვწერეთ WhatsApp-ზე — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს."),
                    ("შეგიძლიათ {L} საბურავის მოტანა და ადგილზე დაყენება?", "დიახ — საბურავს მოგიტანთ თბილისის ნებისმიერ უბანში, ადგილზე დაგიყენებთ და დავაბალანსებთ. ვმუშაობთ 24/7.")],
               faq_alt=("{L}-ის ნაცვლად სხვა ზომის დაყენება შეიძლება?", "დასაშვები ალტერნატივა დამოკიდებულია ავტომობილის მწარმოებლის მითითებაზე.",
                        " მსგავსი დიამეტრის ზომებია: {sim}.", " შეცვლამდე შეამოწმეთ ავტომობილის სახელმძღვანელო."),
               side_h="გჭირდებათ {L}?", side_p="დაგვირეკეთ ან მოგვწერეთ — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს.",
               other_h="სხვა ზომები R{r}", rim_link="R{r} საბურავები →", all_link="ყველა ზომა →", types_h="საბურავები ტიპის მიხედვით",
               svc_type="საბურავების მიწოდება და მონტაჟი", svc_name="საბურავები {L} — მიწოდება და მონტაჟი",
               svc_desc="საბურავები {L} თბილისში — ახალი და მეორადი, ზაფხულის და ზამთრის; მიწოდება, მონტაჟი და ბალანსირება ადგილზე, 24/7.",
               title="საბურავები {L} თბილისში — მიწოდება და მონტაჟი ადგილზე",
               desc="საბურავები {L} — ახალი და მეორადი, ზაფხულის და ზამთრის. მოგიტანთ, ადგილზე დაგიყენებთ და დავაბალანსებთ, თბილისში 24/7. ფასი და მარაგი: ☎ {tel}",
               keywords="საბურავები {L}, {L}, {w} {p} {r}, {L} ფასი, {L} ზამთრის, {L} მეორადი, R{r} საბურავები",
               home="მთავარი", tyres="საბურავები"),
    "en": dict(kicker="Tires", h1="{L} tires",
               lead="New and used {L} tires — summer, winter and all-season. We deliver, fit and balance them on the spot.",
               badges=["New", "Used", "Winter", "Summer / all-season"],
               data_h="{L} size — specifications",
               rows=[("Width", "{w} mm"), ("Profile", "{p}% — sidewall height ≈ {sw} mm"), ("Rim diameter", "{r}″ ({mm} mm)"), ("Overall tire diameter", "≈ {d} mm")],
               data_note="Figures are calculated from the size; the exact dimensions of a specific model may differ slightly.",
               inc_h="What the service includes",
               inc=["Delivery of {L} tires to your location", "Mounting the tire on the rim and fitting the wheel", "Wheel balancing", "Pressure check"],
               when_h="When you need a tire replacement", when_p="In any of these cases, call us — we bring a {L} tire and replace it on the spot.",
               when_link="More: when should a tire be replaced →",
               sim_h="Similar sizes",
               sim_p="These sizes fit the same R{r} rim and have a similar overall diameter to {L} (within ±3%). Check what your car manufacturer approves before fitting a different size.",
               also_h="You may also need",
               also=["Seasonal tire change on site", "How to read a tire size", "When should a tire be replaced"],
               faq_h="Frequently asked questions",
               faq=[("How much does a {L} tire cost?", "It depends on whether it is new or used, the season and the manufacturer. Call us or message us on WhatsApp — we'll tell you the available options and the price."),
                    ("Can you bring a {L} tire and fit it on site?", "Yes — we deliver to any district of Tbilisi, fit and balance the tire on the spot. We work 24/7.")],
               faq_alt=("Can I fit a different size instead of {L}?", "Approved alternatives depend on your car manufacturer.",
                        " Sizes with a similar diameter: {sim}.", " Check your car manual before changing size."),
               side_h="Need {L} tires?", side_p="Call or message us — we'll tell you the available options and the price.",
               other_h="Other R{r} sizes", rim_link="R{r} tires →", all_link="All sizes →", types_h="Tires by type",
               svc_type="Tire delivery and fitting", svc_name="{L} tires — delivery and fitting",
               svc_desc="{L} tires in Tbilisi — new and used, summer and winter; delivery, fitting and balancing on site, 24/7.",
               title="{L} tires in Tbilisi — delivered and fitted on site",
               desc="{L} tires — new and used, summer and winter. We deliver, fit and balance them on site in Tbilisi, 24/7. Price and stock: ☎ {tel}",
               keywords="{L} tires, {L} tyres, {L}, {w} {p} {r}, {L} tire price, {L} winter tires, {L} used tires, R{r} tires Tbilisi",
               home="Home", tyres="Tires"),
    "ru": dict(kicker="Шины", h1="Шины {L}",
               lead="Новые и б/у шины {L} — летние, зимние и всесезонные. Привезём, установим и отбалансируем на месте.",
               badges=["Новые", "Б/у", "Зимние", "Летние / всесезонные"],
               data_h="Размер {L} — параметры",
               rows=[("Ширина", "{w} мм"), ("Профиль", "{p}% — высота боковины ≈ {sw} мм"), ("Диаметр диска", "{r}″ ({mm} мм)"), ("Полный диаметр шины", "≈ {d} мм")],
               data_note="Параметры рассчитаны по размеру; точные размеры конкретной модели могут немного отличаться.",
               inc_h="Что входит в услугу",
               inc=["Доставка шин {L} по вашему адресу", "Монтаж шины на диск и установка колеса", "Балансировка колёс", "Проверка давления"],
               when_h="Когда нужна замена шины", when_p="В любом из этих случаев позвоните нам — привезём шину {L} и заменим её на месте.",
               when_link="Подробнее: когда менять шины →",
               sim_h="Похожие размеры",
               sim_p="Эти размеры подходят к тому же диску R{r} и имеют похожий полный диаметр, что и {L} (в пределах ±3%). Перед установкой другого размера проверьте, что допускает производитель автомобиля.",
               also_h="Может пригодиться",
               also=["Сезонная замена шин на месте", "Как прочитать размер шины", "Когда менять шины"],
               faq_h="Частые вопросы",
               faq=[("Сколько стоит шина {L}?", "Цена зависит от того, новая шина или б/у, а также от сезона и производителя. Позвоните или напишите в WhatsApp — расскажем о вариантах и цене."),
                    ("Можете привезти шину {L} и установить на месте?", "Да — привезём в любой район Тбилиси, установим и отбалансируем на месте. Работаем 24/7.")],
               faq_alt=("Можно поставить другой размер вместо {L}?", "Допустимые варианты зависят от указаний производителя автомобиля.",
                        " Размеры с похожим диаметром: {sim}.", " Перед заменой проверьте руководство автомобиля."),
               side_h="Нужны шины {L}?", side_p="Позвоните или напишите — расскажем о вариантах и цене.",
               other_h="Другие размеры R{r}", rim_link="Шины R{r} →", all_link="Все размеры →", types_h="Шины по типу",
               svc_type="Доставка и монтаж шин", svc_name="Шины {L} — доставка и монтаж",
               svc_desc="Шины {L} в Тбилиси — новые и б/у, летние и зимние; доставка, монтаж и балансировка на месте, 24/7.",
               title="Шины {L} в Тбилиси — доставка и шиномонтаж на месте",
               desc="Шины {L} — новые и б/у, летние и зимние. Привезём, установим и отбалансируем на месте, Тбилиси 24/7. Цена и наличие: ☎ {tel}",
               keywords="шины {L}, {L}, {w} {p} {r}, {L} цена, {L} зимние, {L} б/у, шины R{r} Тбилиси",
               home="Главная", tyres="Шины"),
}


def size_urls(s):
    return {l: size_url(s, l) for l in LANGS}


def build_size(s, lang="ka"):
    T = SZ[lang]
    L = s["label"]
    f = dict(L=L, w=s["w"], p=s["p"], r=s["r"], sw=s["sidewall"], mm=s["rim_mm"], d=s["diameter"], tel=TEL_FMT)
    url = size_url(s, lang)
    sim = similar(s)
    sim_labels = ", ".join(o["label"] for o in sim)
    q, a1, a2, a3 = T["faq_alt"]
    faq = [(x.format(**f), y) for x, y in T["faq"]] + [(q.format(**f), a1 + (a2.format(sim=sim_labels) if sim else "") + a3)]
    wa = HUB_T[lang]["wa_size"].format(L)
    table = "".join(f'<tr class="border-b border-zinc-800 last:border-0"><th class="py-3 pr-4 text-left font-medium text-zinc-400">{x}</th><td class="py-3 font-semibold">{y.format(**f)}</td></tr>' for x, y in T["rows"])
    same_rim = [o for o in SIZES if o["r"] == s["r"] and o is not s]
    sim_block = (f"""
    <h2 class="mt-10 text-2xl font-bold font-head">{T['sim_h']}</h2>
    <p class="mt-4 leading-relaxed text-zinc-300">{T['sim_p'].format(**f)}</p>
    <div class="mt-4 flex flex-wrap gap-2">{''.join(chip(o, lang=lang) for o in sim)}</div>""" if sim else "")
    inc = [T["inc"][0].format(**f), T["inc"][1], a(svc_url("balansireba", lang), T["inc"][2]), T["inc"][3]]
    also = [a(svc_url("sezonuri-saburavebis-shecvla", lang), T["also"][0]), a(blog_url("size", lang), T["also"][1]), a(blog_url("when", lang), T["also"][2])]
    badges = "".join(f'<span class="rounded-full bg-white/10 px-3 py-1 ring-1 ring-white/15">{b}</span>' for b in T["badges"])
    body = f"""<!-- Hero card -->
<section class="mx-auto max-w-6xl px-4 pt-6">
  <div class="grid items-stretch gap-8 rounded-3xl bg-gradient-to-br from-zinc-900 to-zinc-900/40 p-6 ring-1 ring-zinc-800 sm:p-10 lg:grid-cols-2">
    <div class="flex flex-col">
      <p class="text-sm font-semibold uppercase tracking-wider text-brand">{T['kicker']}</p>
      <h1 class="mt-2 text-3xl font-bold font-head break-words sm:text-5xl">{T['h1'].format(**f)}</h1>
      <p class="mt-4 leading-relaxed text-zinc-300">{T['lead'].format(**f)}</p>
      <div class="mt-5 flex flex-wrap gap-2 text-sm">{badges}</div>
      <div class="mt-6 flex flex-wrap gap-3">{btn_call()}{btn_wa(wa)}</div>
    </div>
    <div class="relative h-60 overflow-hidden rounded-2xl ring-1 ring-zinc-800 sm:h-72 lg:h-auto lg:min-h-80"><picture><source srcset="/assets/cover.avif" type="image/avif"><source srcset="/assets/cover.webp" type="image/webp"><img loading="lazy" src="/assets/cover.jpg" alt="{T['h1'].format(**f)}" class="absolute inset-0 h-full w-full object-cover"></picture></div>
  </div>
</section>

<!-- Content -->
<section class="mx-auto grid max-w-6xl gap-10 px-4 py-12 lg:grid-cols-3">
  <div class="lg:col-span-2">
    <p class="text-lg leading-relaxed text-zinc-300">{kind_text(s, lang)}</p>

    <h2 class="mt-10 text-2xl font-bold font-head">{T['data_h'].format(**f)}</h2>
    <table class="mt-5 w-full text-sm"><tbody>{table}</tbody></table>
    <p class="mt-3 text-sm text-zinc-400">{T['data_note']}</p>

    <h2 class="mt-10 text-2xl font-bold font-head">{T['inc_h']}</h2>
    {ul(inc)}

    <h2 class="mt-10 text-2xl font-bold font-head">{T['when_h']}</h2>
    {ul(WHEN[lang][:5])}
    <p class="mt-4 text-zinc-300">{T['when_p'].format(**f)} {a(blog_url("when", lang), T['when_link'])}</p>
{sim_block}

    <h2 class="mt-10 text-2xl font-bold font-head">{T['also_h']}</h2>
    {ul(also)}

    <h2 class="mt-10 text-2xl font-bold font-head">{T['faq_h']}</h2>
    {faq_html(faq)}
  </div>

  <aside class="lg:col-span-1">
    <div class="sticky top-24 space-y-6">
      <div class="rounded-2xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30">
        <h2 class="text-xl font-bold font-head">{T['side_h'].format(**f)}</h2>
        <p class="mt-2 text-sm text-zinc-300">{T['side_p']}</p>
        <div class="mt-4 grid gap-2">{btn_call()}{btn_wa(wa)}</div>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">{T['other_h'].format(**f)}</h2>
        <div class="mt-4 flex flex-wrap gap-2">{''.join(chip(o, lang=lang) for o in same_rim) or '<span class="text-sm text-zinc-400">—</span>'}</div>
        <a href="{rim_url(s['r'], lang)}" class="mt-4 block text-sm font-semibold text-brand hover:text-amber-400">{T['rim_link'].format(**f)}</a>
        <a href="{LANG_HUB[lang]}" class="mt-2 block text-sm font-semibold text-brand hover:text-amber-400">{T['all_link']}</a>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">{T['types_h']}</h2>
        <ul class="mt-4 space-y-2.5 text-sm">{''.join(f'<li><a href="{u}" class="text-zinc-300 hover:text-brand">{n}</a></li>' for n, u in category_links(lang))}</ul>
      </div>
    </div>
  </aside>
</section>
"""
    service = {"@context": "https://schema.org", "@type": "Service", "serviceType": T["svc_type"], "name": T["svc_name"].format(**f),
               "description": T["svc_desc"].format(**f), "areaServed": {"@type": "City", "name": "Tbilisi"}, "provider": PROVIDER}
    urls = size_urls(s)
    html = page(lang, url=url, title=T["title"].format(**f), desc=T["desc"].format(**f), keywords=T["keywords"].format(**f),
                alternates=alts(urls), image="cover", schema=[service, faq_ld(faq)],
                crumbs=[(T["home"], HOME[lang]), (T["tyres"], LANG_HUB[lang]), (f"R{s['r']}", rim_url(s["r"], lang)), (L, None)],
                body=body, nav_urls=urls)
    out = ROOT / url.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ category + rim pages
LS = {
    "ka": dict(notvis="თქვენი ზომა არ ჩანს?", wa_link="მოგვწერეთ WhatsApp-ზე →", filter_link="ზომის ფილტრი →",
               when_h="როდის გჭირდებათ საბურავის შეცვლა", how="როგორ მუშაობს", faq_h="ხშირად დასმული კითხვები",
               side_h="გჭირდებათ საბურავი?", side_p="მოგვწერეთ ზომა — გეტყვით ხელმისაწვდომ ვარიანტებს და ფასს. ვმუშაობთ 24/7.",
               types_h="საბურავები ტიპის მიხედვით", rim_h="დისკის ზომა", svc_type="საბურავების მიწოდება და მონტაჟი",
               cat_kicker="საბურავები", cat_sizes_h="აირჩიეთ ზომა", home="მთავარი", tyres="საბურავები", city=" თბილისში"),
    "en": dict(notvis="Can't see your size?", wa_link="Message us on WhatsApp →", filter_link="Size filter →",
               when_h="When you need a tire replacement", how="How it works", faq_h="Frequently asked questions",
               side_h="Need tires?", side_p="Send us your size — we'll tell you the available options and the price. We work 24/7.",
               types_h="Tires by type", rim_h="Rim size", svc_type="Tire delivery and fitting",
               cat_kicker="Tires", cat_sizes_h="Choose your size", home="Home", tyres="Tires", city=" in Tbilisi"),
    "ru": dict(notvis="Не видите свой размер?", wa_link="Напишите в WhatsApp →", filter_link="Фильтр по размеру →",
               when_h="Когда нужна замена шины", how="Как это работает", faq_h="Частые вопросы",
               side_h="Нужны шины?", side_p="Напишите размер — расскажем о вариантах в наличии и цене. Работаем 24/7.",
               types_h="Шины по типу", rim_h="Размер диска", svc_type="Доставка и монтаж шин",
               cat_kicker="Шины", cat_sizes_h="Выберите размер", home="Главная", tyres="Шины", city=" в Тбилиси"),
}

CAT_I18N = {
    "new": {
        "en": dict(h1="New tires", img="cover", wa="Hello, I'm interested in new tires",
                   title="New tires in Tbilisi — by size, delivered and fitted on site",
                   desc="New tires in Tbilisi — summer, winter and all-season, {range}. We deliver, fit and balance them on site, 24/7.",
                   keywords="new tires Tbilisi, buy tires Tbilisi, tire prices Tbilisi, new tires by size",
                   intro="A new tire gives you maximum safety: full tread depth, a shorter braking distance and a long service life. Tell us your size — we'll offer options for your budget and season and fit them on the spot.",
                   list_h="Why new tires", items=["Full tread depth — the best grip on wet roads", "New, flexible rubber",
                                                  "A long service life with correct pressure and balancing", "Summer, winter and all-season options"],
                   tip="Tip: check the DOT code on new tires too — the four-digit number shows the week and year of manufacture.",
                   faq=[("Which sizes of new tires do you have?", "The most popular sizes, {range}. If your size isn't listed, contact us — we'll help you find it."),
                        ("Should I replace all four tires at once?", "Ideally all four, or at least two on the same axle. New tires are best fitted on the rear axle."),
                        ("How much does a new tire cost?", "{price}")]),
        "ru": dict(h1="Новые шины", img="cover", wa="Здравствуйте, интересуют новые шины",
                   title="Новые шины в Тбилиси — по размерам, доставка и шиномонтаж",
                   desc="Новые шины в Тбилиси — летние, зимние и всесезонные, {range}. Привезём, установим и отбалансируем на месте, 24/7.",
                   keywords="новые шины Тбилиси, купить шины Тбилиси, шины цена Тбилиси, новые шины по размеру",
                   intro="Новая шина даёт максимальную безопасность: полную глубину протектора, короткий тормозной путь и долгий срок службы. Назовите размер — подберём варианты под ваш бюджет и сезон и установим на месте.",
                   list_h="Почему новые шины", items=["Полная глубина протектора — лучшее сцепление на мокрой дороге", "Новая, эластичная резина",
                                                      "Долгий срок службы при правильном давлении и балансировке", "Летние, зимние и всесезонные варианты"],
                   tip="Совет: проверяйте код DOT и на новых шинах — четырёхзначное число показывает неделю и год выпуска.",
                   faq=[("Какие размеры новых шин у вас есть?", "Самые популярные размеры, {range}. Если вашего размера нет в списке, свяжитесь с нами — поможем найти."),
                        ("Нужно ли менять все четыре шины сразу?", "Лучше все четыре, минимум — две на одной оси. Новые шины лучше ставить на заднюю ось."),
                        ("Сколько стоит новая шина?", "{price}")]),
    },
    "used": {
        "en": dict(h1="Used tires", img="van-rear", wa="Hello, I'm interested in used tires",
                   title="Used tires in Tbilisi — inspected, fitted on site",
                   desc="Used tires in Tbilisi at affordable prices, {range} — tread and age checked. We deliver, fit and balance them on site, 24/7.",
                   keywords="used tires Tbilisi, second-hand tires Tbilisi, cheap tires Tbilisi, used winter tires",
                   intro="A used tire in good condition is a solid alternative to a new one at a lower price — especially when you only need to replace one or two tires or are looking for a temporary solution.",
                   list_h="What we check on used tires", items=["Tread depth and even wear", "Date of manufacture (DOT code)",
                                                                "Sidewall — no cracks or bulges", "Airtightness and previous repairs"],
                   list2_h="When a used tire is a good choice",
                   items2=["One tire is damaged and the others are still good — a used one makes a matching pair",
                           "You need a temporary solution until you buy new tires", "You rarely use the car or are about to sell it",
                           "Your budget is limited but you don't want to compromise on safety"],
                   tip="Used winter tires should have at least 4 mm of tread, summer tires at least 3 mm.",
                   faq=[("Are used tires safe?", "We choose used tires in good condition — with enough tread and no damage. You can inspect them yourself before fitting."),
                        ("Can I buy just one used tire?", "Yes. In that case we try to match the tread of your other tire so both wheels on the axle are even."),
                        ("How much does a used tire cost?", "It depends on the size, tread condition and manufacturer. Send us your size — we'll tell you the available options and the price.")]),
        "ru": dict(h1="Шины б/у", img="van-rear", wa="Здравствуйте, интересуют шины б/у",
                   title="Шины б/у в Тбилиси — проверенные, с установкой на месте",
                   desc="Шины б/у в Тбилиси по доступной цене, {range} — проверены протектор и возраст. Привезём, установим и отбалансируем на месте, 24/7.",
                   keywords="шины б/у Тбилиси, бу шины Тбилиси, дешёвые шины Тбилиси, зимние шины б/у",
                   intro="Б/у шина в хорошем состоянии — достойная альтернатива новой по меньшей цене, особенно если нужно заменить одну-две шины или нужно временное решение.",
                   list_h="Что мы проверяем в б/у шинах", items=["Глубину протектора и равномерность износа", "Дату выпуска (код DOT)",
                                                                 "Боковину — без трещин и грыж", "Герметичность и прежние ремонты"],
                   list2_h="Когда б/у шина — хороший выбор",
                   items2=["Повреждена одна шина, а остальные ещё хорошие — б/у шина составит пару", "Нужно временное решение до покупки новых шин",
                           "Вы редко ездите или собираетесь продавать машину", "Бюджет ограничен, но экономить на безопасности не хочется"],
                   tip="У б/у зимних шин протектор желательно не менее 4 мм, у летних — не менее 3 мм.",
                   faq=[("Безопасны ли шины б/у?", "Мы отбираем б/у шины в хорошем состоянии — с достаточным протектором и без повреждений. Перед установкой вы можете осмотреть их сами."),
                        ("Можно купить только одну б/у шину?", "Да. В этом случае мы стараемся подобрать протектор как у второй шины, чтобы колёса на одной оси были одинаковыми."),
                        ("Сколько стоит б/у шина?", "Цена зависит от размера, состояния протектора и производителя. Напишите размер — расскажем о вариантах и цене.")]),
    },
    "winter": {
        "en": dict(h1="Winter tires", img="cover", wa="Hello, I'm interested in winter tires",
                   title="Winter tires in Tbilisi — buy, delivered and fitted on site",
                   desc="Winter tires in Tbilisi — new and used, {range}. We deliver, fit and balance them on site — no queuing. 24/7.",
                   keywords="winter tires Tbilisi, buy winter tires Tbilisi, used winter tires, winter tire prices",
                   intro="When the temperature drops below 7°C, a winter tire grips the road better than a summer one — on wet, cold and snowy asphalt. Choose your size — we bring the tires and fit them on the spot.",
                   list_h="What makes a winter tire different", items=["Soft rubber that stays flexible in the cold", "Deep tread and fine sipes for grip on snow and ice",
                                                                       "Better braking on cold and wet roads", "M+S marking or the mountain-snowflake symbol (3PMSF)"],
                   tip="More: {blog_winter} · {seasonal}", tip_links=("Winter tires — when to change?", "Seasonal tire change on site"),
                   faq=[("When should I fit winter tires?", "When the average daily temperature stays below about 7°C — in Tbilisi that is usually November. Fit them earlier if you are heading to mountain roads."),
                        ("Do winter tires have to go on all four wheels?", "Yes — on all four, so the car stays stable when braking and cornering."),
                        ("Do you have used winter tires?", "Yes, we have both new and used winter tires. Used ones should have at least 4 mm of tread.")]),
        "ru": dict(h1="Зимние шины", img="cover", wa="Здравствуйте, интересуют зимние шины",
                   title="Зимние шины в Тбилиси — покупка, доставка и установка на месте",
                   desc="Зимние шины в Тбилиси — новые и б/у, {range}. Привезём, установим и отбалансируем на месте — без очередей. 24/7.",
                   keywords="зимние шины Тбилиси, купить зимние шины Тбилиси, зимние шины б/у, зимние шины цена",
                   intro="Когда температура опускается ниже 7°C, зимняя шина держит дорогу лучше летней — на мокром, холодном и заснеженном асфальте. Выберите размер — привезём и установим на месте.",
                   list_h="Чем отличаются зимние шины", items=["Мягкая резина, которая сохраняет эластичность на холоде", "Глубокий протектор и ламели для сцепления на снегу и льду",
                                                               "Лучшее торможение на холодной и мокрой дороге", "Маркировка M+S или символ горы со снежинкой (3PMSF)"],
                   tip="Подробнее: {blog_winter} · {seasonal}", tip_links=("Зимние шины — когда менять?", "Сезонная замена шин на месте"),
                   faq=[("Когда ставить зимние шины?", "Когда среднесуточная температура стабильно ниже примерно 7°C — в Тбилиси обычно в ноябре. Если едете в горы — раньше."),
                        ("Зимние шины нужно ставить на все четыре колеса?", "Да — на все четыре, чтобы машина оставалась устойчивой при торможении и в поворотах."),
                        ("У вас есть зимние шины б/у?", "Да, есть и новые, и б/у зимние шины. У б/у протектор желательно не менее 4 мм.")]),
    },
    "summer": {
        "en": dict(h1="Summer and all-season tires", img="service", wa="Hello, I'm interested in summer tires",
                   title="Summer and all-season tires in Tbilisi — delivered and fitted",
                   desc="Summer and all-season tires in Tbilisi — new and used, {range}. We deliver, fit and balance them on site, 24/7.",
                   keywords="summer tires Tbilisi, all-season tires Tbilisi, buy summer tires, all season tires",
                   intro="Summer tires give the best handling and braking in warm weather, and all-season tires are often enough even for Tbilisi's mild winter. Tell us your size and how you use the car — we'll pick the right option.",
                   list_h="How to choose", items=["Summer — if you use separate winter tires in winter", "All-season — if you mostly drive in the city and rarely go to the mountains",
                                                  "Low-profile — for sporty driving, but easier to damage on potholes", "When the temperature stays above 7°C, switch from winter to summer tires"],
                   tip="Help with the size: {blog_size}", tip_links=("How to read a tire size",),
                   faq=[("Will all-season tires cope with winter?", "For Tbilisi's mild winter, good all-season tires are often enough, but on snow, ice and mountain roads winter tires are much better."),
                        ("When should I switch back to summer tires?", "When the average daily temperature stays above 7°C — in Tbilisi usually in late March or April."),
                        ("How much does a summer tire cost?", "{price}")]),
        "ru": dict(h1="Летние и всесезонные шины", img="service", wa="Здравствуйте, интересуют летние шины",
                   title="Летние и всесезонные шины в Тбилиси — доставка и шиномонтаж",
                   desc="Летние и всесезонные шины в Тбилиси — новые и б/у, {range}. Привезём, установим и отбалансируем на месте, 24/7.",
                   keywords="летние шины Тбилиси, всесезонные шины Тбилиси, купить летние шины, всесезонная резина",
                   intro="Летние шины дают лучшую управляемость и торможение в тёплую погоду, а всесезонных часто хватает и для мягкой тбилисской зимы. Назовите размер и расскажите, как вы ездите, — подберём подходящий вариант.",
                   list_h="Как выбрать", items=["Летние — если зимой вы ставите отдельные зимние шины", "Всесезонные — если ездите в основном по городу и редко бываете в горах",
                                                "Низкопрофильные — для спортивной езды, но легче повреждаются на ямах", "Когда температура стабильно выше 7°C, меняйте зимние шины на летние"],
                   tip="Поможет с размером: {blog_size}", tip_links=("Как прочитать размер шины",),
                   faq=[("Справятся ли всесезонные шины с зимой?", "Для мягкой тбилисской зимы хорошие всесезонные шины часто подходят, но на снегу, льду и горных дорогах зимние шины гораздо лучше."),
                        ("Когда возвращать летние шины?", "Когда среднесуточная температура стабильно выше 7°C — в Тбилиси обычно в конце марта или в апреле."),
                        ("Сколько стоит летняя шина?", "{price}")]),
    },
}

RIM_DESC = {
    "ka": lambda r: ("პატარა და კომპაქტური ავტომობილებისთვის" if r <= 14 else
                     "ყველაზე გავრცელებული ზომები სედანებისა და კომპაქტური ავტომობილებისთვის" if r <= 16 else
                     "სედანებისთვის, კროსოვერებისა და ჯიპებისთვის" if r == 17 else
                     "ბიზნეს კლასის ავტომობილებისთვის, კროსოვერებისა და ჯიპებისთვის" if r <= 19 else
                     "პრემიუმ ავტომობილებისა და დიდი ჯიპებისთვის — ხშირად დაბალპროფილიანი"),
    "en": lambda r: ("for small and compact cars" if r <= 14 else
                     "the most common sizes for sedans and compact cars" if r <= 16 else
                     "for sedans, crossovers and SUVs" if r == 17 else
                     "for business-class cars, crossovers and SUVs" if r <= 19 else
                     "for premium cars and large SUVs — often low-profile"),
    "ru": lambda r: ("для небольших и компактных автомобилей" if r <= 14 else
                     "самые распространённые размеры для седанов и компактных автомобилей" if r <= 16 else
                     "для седанов, кроссоверов и внедорожников" if r == 17 else
                     "для автомобилей бизнес-класса, кроссоверов и внедорожников" if r <= 19 else
                     "для премиальных автомобилей и больших внедорожников — часто низкопрофильные"),
}


def landing(urls, lang, *, h1, kicker, intro, img, wa, sections, faq, sizes, sizes_h, crumbs, title, desc, keywords, service_name):
    U = LS[lang]
    url = urls[lang]
    chips = "".join(chip(x, lang=lang) for x in sizes)
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
  <p class="mt-4 text-sm text-zinc-400">{U['notvis']} <a href="{wa_link(wa)}" target="_blank" rel="noopener" class="font-semibold text-brand hover:text-amber-400">{U['wa_link']}</a> · <a href="{LANG_HUB[lang]}" class="font-semibold text-brand hover:text-amber-400">{U['filter_link']}</a></p>
</section>

<section class="mx-auto grid max-w-6xl gap-10 px-4 pb-12 lg:grid-cols-3">
  <div class="lg:col-span-2">
{sections}
    <h2 class="mt-10 text-2xl font-bold font-head">{U['when_h']}</h2>
    {ul(WHEN[lang])}

    <h2 class="mt-10 text-2xl font-bold font-head">{U['how']}</h2>
    {steps(HUB_T[lang]['steps'])}

    <h2 class="mt-10 text-2xl font-bold font-head">{U['faq_h']}</h2>
    {faq_html(faq)}
  </div>
  <aside class="lg:col-span-1">
    <div class="sticky top-24 space-y-6">
      <div class="rounded-2xl bg-gradient-to-br from-brand/15 to-zinc-900 p-6 ring-1 ring-brand/30">
        <h2 class="text-xl font-bold font-head">{U['side_h']}</h2>
        <p class="mt-2 text-sm text-zinc-300">{U['side_p']}</p>
        <div class="mt-4 grid gap-2">{btn_call()}{btn_wa(wa)}</div>
      </div>
      <div class="rounded-2xl bg-zinc-900 p-6 ring-1 ring-zinc-800">
        <h2 class="text-lg font-bold font-head">{U['types_h']}</h2>
        <ul class="mt-4 space-y-2.5 text-sm">{''.join(f'<li><a href="{u}" class="text-zinc-300 hover:text-brand">{n}</a></li>' for n, u in category_links(lang) if u != url)}</ul>
        <h2 class="mt-6 text-lg font-bold font-head">{U['rim_h']}</h2>
        <div class="mt-3 flex flex-wrap gap-2">{''.join(f'<a href="{rim_url(r, lang)}" class="rounded-full bg-zinc-950 px-3 py-1.5 text-sm font-semibold ring-1 ring-zinc-800 hover:text-brand hover:ring-brand/60">R{r}</a>' for r in RIMS)}</div>
      </div>
    </div>
  </aside>
</section>
"""
    service = {"@context": "https://schema.org", "@type": "Service", "serviceType": U["svc_type"], "name": service_name,
               "description": desc, "areaServed": {"@type": "City", "name": "Tbilisi"}, "provider": PROVIDER}
    html = page(lang, url=url, title=title, desc=desc, keywords=keywords, alternates=alts(urls), image=img,
                schema=[service, faq_ld(faq)], crumbs=crumbs, body=body, nav_urls=urls)
    out = ROOT / url.strip("/") / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def build_category(c, lang="ka"):
    key = KA_CAT_KEY[c["slug"]]
    urls = {l: cat_url(key, l) for l in LANGS}
    U = LS[lang]
    if lang == "ka":
        d = c
        tip = c["tip"]
        faq = c["faq"]
        wa = f"გამარჯობა, მაინტერესებს {c['h1'].lower()}"
    else:
        d = CAT_I18N[key][lang]
        fill = dict(range=rim_range(lang), price=PRICE[lang])
        links = d.get("tip_links", ())
        if key == "winter":
            fill.update(blog_winter=a(blog_url("winter", lang), links[0]), seasonal=a(svc_url("sezonuri-saburavebis-shecvla", lang), links[1]))
        if key == "summer":
            fill.update(blog_size=a(blog_url("size", lang), links[0]))
        tip = d["tip"].format(**fill)
        faq = [(q, x.format(**fill)) for q, x in d["faq"]]
        wa = d["wa"]
        d = dict(d, desc=d["desc"].format(**fill))
    sec = f'    <h2 class="text-2xl font-bold font-head">{d["list_h"]}</h2>\n    {ul(d["items"])}\n'
    if d.get("items2"):
        sec += f'\n    <h2 class="mt-10 text-2xl font-bold font-head">{d["list2_h"]}</h2>\n    {ul(d["items2"])}\n'
    sec += f'    <p class="mt-4 text-zinc-300">{tip}</p>\n'
    landing(urls, lang, h1=d["h1"], kicker=U["cat_kicker"], intro=d["intro"], img=d["img"], wa=wa,
            sections=sec, faq=faq, sizes=SIZES, sizes_h=U["cat_sizes_h"],
            crumbs=[(U["home"], HOME[lang]), (U["tyres"], LANG_HUB[lang]), (d["h1"], None)],
            title=d["title"], desc=d["desc"], keywords=d["keywords"], service_name=f"{d['h1']}{U['city']}")


RIM_T = {
    "ka": dict(kicker="საბურავები დისკის ზომით", h1="R{r} საბურავები", sizes_h="R{r} საბურავების ზომები", wa="გამარჯობა, მაინტერესებს R{r} საბურავები",
               intro="{r}-დიუმიანი დისკის საბურავები — {desc}. ახალი და მეორადი, ზაფხულის, ზამთრის და ყველა სეზონის. აირჩიეთ ზომა ან მოგვწერეთ WhatsApp-ზე.",
               sec_h="R{r} ზომები", heads=("ზომა", "სიგანე", "გვერდის სიმაღლე", "სრული დიამეტრი"), unit="მმ",
               note="R{r} ნიშნავს {r}-დიუმიან ({mm} მმ) დისკს. მონაცემები გამოთვლილია ზომის მიხედვით.",
               faq=[("R{r} რას ნიშნავს?", "R{r} ნიშნავს, რომ საბურავი {r}-დიუმიან ({mm} მმ) დისკზე ჯდება; ასო R რადიალურ კონსტრუქციას აღნიშნავს."),
                    ("რა ღირს R{r} საბურავი?", "{price}"),
                    ("R{r} საბურავს ადგილზე დამიყენებთ?", "დიახ — მოგიტანთ თბილისის ნებისმიერ უბანში, ადგილზე დაგიყენებთ და დავაბალანსებთ. ვმუშაობთ 24/7.")],
               title="R{r} საბურავები თბილისში — ახალი და მეორადი, მონტაჟით ადგილზე",
               desc="R{r} ({r}-დიუმიანი) საბურავები თბილისში — {n} ზომა, ახალი და მეორადი, ზაფხულის და ზამთრის. მოგიტანთ, დაგიყენებთ და დავაბალანსებთ ადგილზე, 24/7.",
               keywords="R{r} საბურავები, საბურავები R{r}, {r} დიუმიანი საბურავები, R{r} ზამთრის საბურავები, R{r} საბურავები ფასი",
               service="R{r} საბურავები თბილისში"),
    "en": dict(kicker="Tires by rim size", h1="R{r} tires", sizes_h="R{r} tire sizes", wa="Hello, I'm interested in R{r} tires",
               intro="Tires for {r}-inch rims — {desc}. New and used, summer, winter and all-season. Choose your size or message us on WhatsApp.",
               sec_h="R{r} sizes", heads=("Size", "Width", "Sidewall height", "Overall diameter"), unit="mm",
               note="R{r} means {art} {r}-inch ({mm} mm) rim. Figures are calculated from the size.",
               faq=[("What does R{r} mean?", "R{r} means the tire fits {art} {r}-inch ({mm} mm) rim; the letter R stands for radial construction."),
                    ("How much does an R{r} tire cost?", "{price}"),
                    ("Can you fit R{r} tires on site?", "Yes — we deliver to any district of Tbilisi, fit and balance the tires on the spot. We work 24/7.")],
               title="R{r} tires in Tbilisi — new and used, fitted on site",
               desc="R{r} ({r}-inch) tires in Tbilisi — {n}, new and used, summer and winter. We deliver, fit and balance them on site, 24/7.",
               keywords="R{r} tires, R{r} tyres, R{r} tires Tbilisi, {r} inch tires, R{r} winter tires, R{r} tire price",
               service="R{r} tires in Tbilisi"),
    "ru": dict(kicker="Шины по размеру диска", h1="Шины R{r}", sizes_h="Размеры шин R{r}", wa="Здравствуйте, интересуют шины R{r}",
               intro="Шины для {r}-дюймовых дисков — {desc}. Новые и б/у, летние, зимние и всесезонные. Выберите размер или напишите нам в WhatsApp.",
               sec_h="Размеры R{r}", heads=("Размер", "Ширина", "Высота боковины", "Полный диаметр"), unit="мм",
               note="R{r} означает {r}-дюймовый ({mm} мм) диск. Параметры рассчитаны по размеру.",
               faq=[("Что означает R{r}?", "R{r} означает, что шина подходит к {r}-дюймовому ({mm} мм) диску; буква R обозначает радиальную конструкцию."),
                    ("Сколько стоит шина R{r}?", "{price}"),
                    ("Установите шины R{r} на месте?", "Да — привезём в любой район Тбилиси, установим и отбалансируем на месте. Работаем 24/7.")],
               title="Шины R{r} в Тбилиси — новые и б/у, шиномонтаж на месте",
               desc="Шины R{r} ({r} дюймов) в Тбилиси — {n}, новые и б/у, летние и зимние. Привезём, установим и отбалансируем на месте, 24/7.",
               keywords="шины R{r}, шины R{r} Тбилиси, резина R{r}, зимние шины R{r}, шины R{r} цена",
               service="Шины R{r} в Тбилиси"),
}


def build_rim(r, lang="ka"):
    T = RIM_T[lang]
    U = LS[lang]
    urls = {l: rim_url(r, l) for l in LANGS}
    sizes = [s for s in SIZES if s["r"] == r]
    f = dict(r=r, mm=round(r * 25.4), desc=RIM_DESC[lang](r), price=PRICE[lang], art="an" if r in (8, 11, 18) else "a",
             n=(str(len(sizes)) if lang == "ka" else n_sizes(lang, len(sizes))))
    un = T["unit"]
    rows = "".join(f'<tr class="border-b border-zinc-800 last:border-0"><td class="py-3 pr-4"><a href="{size_url(s, lang)}" class="font-semibold text-brand hover:text-amber-400">{s["label"]}</a></td>'
                   f'<td class="py-3 pr-4 text-zinc-300">{s["w"]} {un}</td><td class="py-3 pr-4 text-zinc-300">{s["sidewall"]} {un}</td><td class="py-3 text-zinc-300">≈ {s["diameter"]} {un}</td></tr>' for s in sizes)
    th = "".join(f'<th class="py-2 {"pr-4 " if i < 3 else ""}font-medium">{h}</th>' for i, h in enumerate(T["heads"]))
    sec = f"""    <h2 class="text-2xl font-bold font-head">{T['sec_h'].format(**f)}</h2>
    <div class="mt-5 overflow-x-auto"><table class="w-full text-left text-sm"><thead><tr class="border-b border-zinc-700 text-zinc-400">{th}</tr></thead><tbody>{rows}</tbody></table></div>
    <p class="mt-3 text-sm text-zinc-400">{T['note'].format(**f)}</p>
"""
    faq = [(q.format(**f), x.format(**f)) for q, x in T["faq"]]
    landing(urls, lang, h1=T["h1"].format(**f), kicker=T["kicker"], intro=T["intro"].format(**f), img="cover", wa=T["wa"].format(**f),
            sections=sec, faq=faq, sizes=sizes, sizes_h=T["sizes_h"].format(**f),
            crumbs=[(U["home"], HOME[lang]), (U["tyres"], LANG_HUB[lang]), (f"R{r}", None)],
            title=T["title"].format(**f), desc=T["desc"].format(**f), keywords=T["keywords"].format(**f), service_name=T["service"].format(**f))


# Georgian category data (original text)
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


# ------------------------------------------------------------------ site-wide sync
def html_files():
    tracked = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    extra = [str(p.relative_to(ROOT)) for d in ("saburavebi", "tyres", "shiny") for p in (ROOT / d).glob("**/*.html")]
    return sorted(set(tracked) | set(extra))


def ensure_nav():
    for rel in html_files():
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        m_lang = re.search(r'<html lang="(\w+)"', s)
        if not m_lang:
            continue  # redirect stubs
        lang = m_lang.group(1)
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
        if not m or any(f'href="{h}' in m.group(2) for h in LANG_HUB.values()) or 'href="/saburavebi/index-' in m.group(2):
            continue
        link = f'<a href="{HUB_URLS[lang]}" class="hover:text-brand transition-colors">{HUB_T[lang]["nav"]}</a>'
        s = s[:m.end(1)] + link + s[m.end(1):]
        p.write_text(s, encoding="utf-8")


LANG_LABEL = {"ka": "ქა", "en": "EN", "ru": "RU"}
SWITCH_CLS = "hidden items-center gap-1 rounded-lg bg-zinc-900 p-1 text-xs sm:flex"
MENU_JS = ("<script>document.getElementById('navBtn').addEventListener('click',function(){"
           "document.getElementById('navMenu').classList.toggle('hidden');});</script>\n")


def page_path(rel):
    return "/" + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)


def ensure_mobile_menu():
    """Every page gets the phone menu (☰) the homepages already had: tyres first (highlighted), the page's
    own nav links, then languages. Blog pages also get the header language switcher. Idempotent."""
    for rel in html_files():
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        if "<header" not in s:
            continue
        lang = re.search(r'<html lang="(\w+)"', s).group(1)
        head_end = s.index("</header>")
        header = s[:head_end]

        # 1) header language switcher (blog pages were missing it; articles are Georgian-only -> EN/RU homepages)
        if SWITCH_CLS not in header:
            me = page_path(rel)
            links = [(me, "ქა", True), ("/index-en.html", "EN", False), ("/index-ru.html", "RU", False)]
            sw = (f'<div class="{SWITCH_CLS}">' + "".join(
                f'<a href="{u}" class="px-2 py-1 rounded hover:bg-zinc-800 {"text-brand font-semibold" if cur else "text-zinc-400"}">{t}</a>'
                for u, t, cur in links) + "</div>\n      ")
            i = header.index('<a href="tel:')
            s = s[:i] + sw + s[i:]
            head_end = s.index("</header>")
            header = s[:head_end]

        # 2) phones under 400px: hide the header call button (the floating call button is on every page)
        tel_cls = "inline-flex items-center gap-2 rounded-lg bg-brand px-3 py-2 text-sm font-bold text-zinc-950 hover:bg-amber-400"
        if f'class="{tel_cls}"' in header:
            s = s.replace(f'class="{tel_cls}"', f'class="{tel_cls} max-[399px]:hidden"', 1)
            head_end = s.index("</header>")
            header = s[:head_end]

        # 3) the ☰ button + menu panel
        if 'id="navMenu"' not in header:
            nav = re.search(r'<div class="hidden items-center gap-6 text-sm font-medium md:flex">(.*?)</div>', header, re.S).group(1)
            items = [(h, t) for h, t in re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', nav) if not h.startswith("/saburavebi/")]
            sw = re.search(r'<div class="' + re.escape(SWITCH_CLS) + r'">(.*?)</div>', header, re.S).group(1)
            langs = re.sub(r'class="px-2 py-1 rounded', 'class="px-3 py-1.5 rounded', sw)
            panel = ('\n  <div id="navMenu" class="hidden border-t border-zinc-800 px-4 py-2 md:hidden">'
                     + "".join(f'<a href="{h}" class="block px-4 py-2 hover:bg-zinc-800 rounded">{t}</a>' for h, t in items)
                     + f'\n    <div class="mt-2 flex gap-1 border-t border-zinc-800 pt-2 text-sm">{langs}</div>\n  </div>\n')
            btn = ('\n      <button id="navBtn" class="grid h-9 w-9 place-items-center rounded-lg bg-zinc-900 md:hidden" aria-label="menu">'
                   '<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke-width="1.7" stroke="currentColor" aria-hidden="true">'
                   '<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"/></svg></button>')
            tel_end = header.index("</a>", header.index('<a href="tel:')) + len("</a>")
            s = s[:tel_end] + btn + s[tel_end:]
            nav_close = s.index("</nav>", tel_end) + len("</nav>")
            s = s[:nav_close] + panel + s[nav_close:]
        if "getElementById('navBtn')" not in s:
            s = s.replace("</body>", MENU_JS + "</body>", 1)

        # 4) tyres first and highlighted in the menu (also on the homepages that already had a menu)
        if "data-menu-tyres" not in s:
            m = re.search(r'<div id="navMenu"[^>]*>', s)
            tyres = (f'<a data-menu-tyres href="{HUB_URLS[lang]}" class="block rounded px-4 py-2 font-semibold text-brand hover:bg-zinc-800">'
                     f'{HUB_T[lang]["nav"]} →</a>')
            s = s[:m.end()] + tyres + s[m.end():]
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
        chips = "".join(chip(x, lang=lang) for x in POPULAR) + "".join(
            f'<a href="{rim_url(r, lang)}" class="rounded-full px-3 py-1.5 text-sm font-bold text-brand ring-1 ring-brand/40 transition hover:bg-brand hover:text-zinc-950">R{r}</a>' for r in RIMS)
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
    block = "\n"
    for lang in LANGS:
        top = lang == "ka"
        block += (url(LANG_HUB[lang], "0.90" if top else "0.80")
                  + "".join(url(cat_url(k, lang), "0.85" if top else "0.75") for k in CAT_SLUGS)
                  + "".join(url(rim_url(r, lang), "0.80" if top else "0.70") for r in RIMS)
                  + "".join(url(size_url(x, lang), "0.70" if top else "0.60") for x in SIZES))
    block += "  "
    s = sync_block(s, "<!-- tyres:start -->", "<!-- tyres:end -->", block, "</urlset>")
    p.write_text(s, encoding="utf-8")


def sync_llms():
    p = ROOT / "llms.txt"
    s = p.read_text(encoding="utf-8")
    block = ("\n## Tyres (საბურავები) — sale, delivery and fitting\n"
             f"- Tyre catalogue by size, new and used, summer/winter/all-season; delivered, fitted and balanced on site in Tbilisi 24/7; price and stock by phone/WhatsApp {TEL_FMT}: {SITE}{HUB}\n"
             + f"- English: {SITE}/tyres/ · Russian: {SITE}/shiny/ (every size, rim and category page exists in all three languages)\n"
             + "".join(f"- {c['h1']}: {SITE}/saburavebi/{c['slug']}/\n" for c in CATEGORIES)
             + "- By rim: " + ", ".join(f"[R{r}]({SITE}{rim_url(r)})" for r in RIMS) + "\n"
             + "- Sizes: " + ", ".join(f"[{x['label']}]({SITE}{size_url(x)})" for x in SIZES) + "\n")
    s = sync_block(s, "<!-- tyres:start -->", "<!-- tyres:end -->", block, "## Service area") if "## Service area" in s else s + "\n<!-- tyres:start -->" + block + "<!-- tyres:end -->\n"
    p.write_text(s, encoding="utf-8")


OLD_URLS = {"/saburavebi/index-en.html": "/tyres/", "/saburavebi/index-ru.html": "/shiny/"}


def write_redirects():
    """The first English/Russian hubs lived at /saburavebi/index-en.html and index-ru.html (2026-11-20, a few hours).
    Keep those URLs working: tiny redirect pages + every internal link updated to the new URL."""
    for old, new in OLD_URLS.items():
        (ROOT / old.lstrip("/")).write_text(
            f'<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>Redirect</title>'
            f'<link rel="canonical" href="{SITE}{new}"><meta name="robots" content="noindex, follow">'
            f'<meta http-equiv="refresh" content="0; url={new}"></head>'
            f'<body><a href="{new}">{SITE}{new}</a></body></html>\n', encoding="utf-8")
    for rel in html_files():
        if rel.lstrip("/") in {o.lstrip("/") for o in OLD_URLS}:
            continue
        f = ROOT / rel
        t = f.read_text(encoding="utf-8")
        o = t
        for old, new in OLD_URLS.items():
            t = t.replace(f'href="{old}"', f'href="{new}"').replace(f'href="{SITE}{old}"', f'href="{SITE}{new}"')
        if t != o:
            f.write_text(t, encoding="utf-8")


def main():
    # remove size pages that are no longer in tyres.json
    for lang in LANGS:
        keep = {s["slug"] for s in SIZES} | {CAT_SLUGS[k][lang] for k in CAT_SLUGS} | {f"r{r}" for r in RIMS}
        hub_dir = ROOT / LANG_HUB[lang].strip("/")
        for d in hub_dir.glob("*/"):
            if d.is_dir() and d.name not in keep:
                shutil.rmtree(d)
        build_hub(lang)
        for s in SIZES:
            build_size(s, lang)
        for c in CATEGORIES:
            build_category(c, lang)
        for r in RIMS:
            build_rim(r, lang)
    write_redirects()
    ensure_nav()
    ensure_mobile_menu()
    sync_homepages()
    sync_sitemap()
    sync_llms()
    print(f"built ka/en/ru: hub + {len(CATEGORIES)} category + {len(RIMS)} rim + {len(SIZES)} size pages each")


if __name__ == "__main__":
    main()
