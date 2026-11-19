"""Build AI-readable Markdown for vulkanizacia.ge (llms.txt convention).

For every HTML page it writes a clean Markdown copy next to it (`index.html` -> `index.html.md`,
`index-en.html` -> `index-en.html.md`), adds `<link rel="alternate" type="text/markdown">` to the
HTML head, and regenerates `llms-full.txt` (all pages in one file).

Run from the repo root after editing any page:  python3 tools/build_md.py
"""
import re
import subprocess
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://vulkanizacia.ge"

# Facts block prepended to every page, per language (kept short and factual for answer engines).
FACTS = {
    "ka": ("## ძირითადი ინფორმაცია\n"
           "- კომპანია: Vulkanizacia.ge — მოძრავი ვულკანიზაცია და საბურავები თბილისში\n"
           "- ტელეფონი: +995 591 90 90 13 (WhatsApp / Viber)\n"
           "- ელ-ფოსტა: info@vulkanizacia.ge\n"
           "- სამუშაო საათები: 24/7, დასვენების და სადღესასწაულო დღეების ჩათვლით\n"
           "- მისვლის დრო: თბილისში ჩვეულებრივ 20–30 წუთი\n"
           "- მომსახურება: საბურავის შეკეთება და შეცვლა ადგილზე, ახალი და მეორადი საბურავები ზომების მიხედვით, ბალანსირება, დისკის დადუღება და გასწორება\n"
           "- საბურავები: https://vulkanizacia.ge/saburavebi/\n"
           "- ევაკუატორი: https://towing.ge (+995 514 90 80 90)\n"),
    "en": ("## Key facts\n"
           "- Business: Vulkanizacia.ge — mobile tyre service and tyre sales in Tbilisi, Georgia\n"
           "- Phone: +995 591 90 90 13 (WhatsApp / Viber)\n"
           "- Email: info@vulkanizacia.ge\n"
           "- Hours: 24/7, including weekends and holidays\n"
           "- Arrival time: typically 20–30 minutes within Tbilisi\n"
           "- Services: on-site tyre repair and replacement, new and used tyres by size, wheel balancing, rim welding and straightening\n"
           "- Tyres: https://vulkanizacia.ge/saburavebi/index-en.html\n"
           "- Tow truck: https://towing.ge (+995 514 90 80 90)\n"),
    "ru": ("## Основная информация\n"
           "- Компания: Vulkanizacia.ge — мобильная вулканизация и шины в Тбилиси\n"
           "- Телефон: +995 591 90 90 13 (WhatsApp / Viber)\n"
           "- Email: info@vulkanizacia.ge\n"
           "- Режим работы: 24/7, включая выходные и праздники\n"
           "- Время прибытия: по Тбилиси обычно 20–30 минут\n"
           "- Услуги: ремонт и замена шин на месте, новые и б/у шины по размерам, балансировка, сварка и правка дисков\n"
           "- Шины: https://vulkanizacia.ge/saburavebi/index-ru.html\n"
           "- Эвакуатор: https://towing.ge (+995 514 90 80 90)\n"),
}

SKIP_TAGS = {"script", "style", "nav", "noscript", "svg", "button", "picture", "img", "footer", "form", "input", "label"}
SKIP_CLASSES = {"call-button", "breadcrumb", "fixed"}
SKIP_IDS = {"top-ge-counter-container", "tyre-filter", "tyre-none"}
BLOCK = {"p", "div", "section", "header", "footer", "ul", "ol", "li", "h1", "h2", "h3", "h4", "h5", "h6",
         "details", "summary", "br", "hr", "aside", "article"}


class ToMarkdown(HTMLParser):
    def __init__(self, page_url):
        super().__init__(convert_charrefs=True)
        self.page_url = page_url
        self.out = []
        self.skip = 0          # depth inside skipped subtree
        self.stack = []        # (tag, skipped?)
        self.href = None
        self.link_text = []
        self.list_depth = 0
        self.cell = 0

    def _abs(self, href):
        if href.startswith(("http://", "https://", "mailto:", "tel:", "viber:")):
            return href
        if href.startswith("#"):
            return self.page_url + href
        base = self.page_url if self.page_url.endswith("/") else self.page_url.rsplit("/", 1)[0] + "/"
        if href.startswith("/"):
            return SITE + href
        return base + href

    def emit(self, text):
        if self.href is not None:
            self.link_text.append(text)
        else:
            self.out.append(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = set((a.get("class") or "").split())
        skipped = self.skip > 0 or tag in SKIP_TAGS or cls & SKIP_CLASSES or a.get("id") in SKIP_IDS
        if tag in ("br", "hr", "img", "source", "meta", "link", "input"):
            if not skipped and tag == "br":
                self.emit("  \n")
            return
        self.stack.append((tag, bool(skipped)))
        if skipped:
            self.skip += 1
            return
        if tag == "tr":
            self.cell = 0
            self.emit("\n- ")
        elif tag in ("td", "th"):
            self.cell += 1
            if self.cell > 1:
                self.emit(" — ")
        elif tag == "span" and "rounded-full" in cls:
            self.emit(" • ")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.emit("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "summary":
            self.emit("\n\n### ")
        elif tag in ("ul", "ol"):
            self.list_depth += 1
            self.emit("\n")
        elif tag == "li":
            self.emit("\n" + "  " * (self.list_depth - 1) + "- ")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag == "a" and a.get("href"):
            self.href = self._abs(a["href"])
            self.link_text = []
        elif tag in BLOCK:
            self.emit("\n\n")

    def handle_endtag(self, tag):
        if tag in ("br", "hr", "img", "source", "meta", "link", "input"):
            return
        while self.stack:
            t, skipped = self.stack.pop()
            if skipped:
                self.skip -= 1
            if t == tag:
                break
        else:
            return
        if skipped:
            return
        if tag in ("strong", "b"):
            self.emit("**")
        elif tag == "a" and self.href is not None:
            text = re.sub(r"\s+", " ", "".join(self.link_text)).strip()
            href, self.href = self.href, None
            if text:
                if self.out and self.out[-1].endswith(")") and self.out[-1].startswith("["):
                    self.out.append(" · ")
                self.out.append(f"[{text}]({href})")
        elif tag in ("ul", "ol"):
            self.list_depth -= 1
            self.emit("\n")
        elif tag in BLOCK:
            self.emit("\n\n")

    def handle_data(self, data):
        if self.skip:
            return
        text = re.sub(r"\s+", " ", data)
        if text.strip():
            self.emit(text)

    def markdown(self):
        md = "".join(self.out)
        md = re.sub(r"[ \t]+\n", "\n", md)
        md = re.sub(r"\n(#+|-) +", lambda m: "\n" + m.group(1) + " ", md)
        md = re.sub(r"\n{3,}", "\n\n", md)
        md = re.sub(r"\*\*\s*\*\*", "", md)
        # numbered step badges ("- 1" + bold title) -> ordered list item
        md = re.sub(r"\n- (\d+)\s*\n\s*\*\*", r"\n\1. **", md)
        # drop empty list items / headings left by skipped icons
        md = re.sub(r"\n- *\n", "\n", md)
        md = re.sub(r"\n#+ *\n", "\n", md)
        # list items must not be separated by blank lines
        md = re.sub(r"(\n- [^\n]*)\n\n(?=- )", r"\1\n", md)
        md = re.sub(r"(\n- [^\n]*)\n\n(?=- )", r"\1\n", md)
        return md.strip() + "\n"


def page_url(rel):
    if rel.endswith("index.html"):
        return f"{SITE}/{rel[:-len('index.html')]}"
    return f"{SITE}/{rel}"


def build(rel):
    src = (ROOT / rel).read_text(encoding="utf-8")
    lang = re.search(r'<html lang="(\w+)"', src).group(1)
    title = unescape(re.search(r"<title>(.*?)</title>", src, re.S).group(1).strip())
    desc = unescape(re.search(r'<meta name="description" content="([^"]*)"', src).group(1))
    body = re.search(r"<body[^>]*>(.*)</body>", src, re.S).group(1)
    # JSON-LD lives in <head>; inline FAQ JSON-LD in body is skipped as <script>
    conv = ToMarkdown(page_url(rel))
    conv.feed(body)
    content = conv.markdown()
    # the page's H1 becomes the document title (falls back to <title>)
    h1 = re.search(r"^# (.*)\n", content, re.M)
    if h1:
        heading, content = h1.group(1).strip(), (content[:h1.start()] + content[h1.end():]).strip() + "\n"
    else:
        heading = title
    url = page_url(rel)
    alts = re.findall(r'<link rel="alternate" hreflang="(\w+(?:-\w+)?)" href="([^"]+)"', src)
    lang_line = ""
    if alts:
        lang_line = "\n" + " · ".join(f"[{h}]({u})" for h, u in alts if h != "x-default") + "\n"
    md = (f"# {heading}\n\n> {desc}\n\n"
          f"Canonical: {url}\n{lang_line}\n"
          f"{FACTS[lang]}\n{content}")
    out = ROOT / (rel + ".md")
    out.write_text(md, encoding="utf-8")

    # advertise the Markdown copy from the HTML head
    md_url = f"{SITE}/{rel}.md"
    tag = f'<link rel="alternate" type="text/markdown" href="{md_url}" />'
    if tag not in src:
        src2, n = re.subn(r'(\n(\s*)<link rel="canonical"[^>]*>)', lambda m: m.group(1) + "\n" + m.group(2) + tag, src, count=1)
        assert n == 1, rel
        (ROOT / rel).write_text(src2, encoding="utf-8")
    return rel, lang, title, md


def main():
    files = subprocess.run(["git", "ls-files", "*.html"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    files += [str(p.relative_to(ROOT)) for p in ROOT.glob("**/*.html")
              if str(p.relative_to(ROOT)) not in files and "node_modules" not in p.parts]
    order = {"ka": 0, "en": 1, "ru": 2}
    pages = sorted((build(f) for f in sorted(set(files))),
                   key=lambda x: (order[x[1]], x[0] != "index.html" and not x[0].startswith("index-"), x[0]))
    full = ["# Vulkanizacia.ge — full site content (მოძრავი ვულკანიზაცია და საბურავები / Mobile tyre service and tyres / Шины и вулканизация, Tbilisi)\n",
            "> Every page of https://vulkanizacia.ge in Markdown, for AI assistants and answer engines. "
            "Index: https://vulkanizacia.ge/llms.txt\n"]
    for rel, lang, title, md in pages:
        if re.match(r"saburavebi/\d{3}-\d{2}-r\d{2}/", rel):
            continue  # 60+ near-identical size pages: keep their own .md, skip them here
        full.append(f"\n\n---\n\nSource: {SITE}/{rel}.md\n\n{md}")
    (ROOT / "llms-full.txt").write_text("".join(full), encoding="utf-8")
    for rel, lang, title, _ in pages:
        print(f"{lang}  {rel}.md  — {title}")


if __name__ == "__main__":
    main()
