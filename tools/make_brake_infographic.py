"""Brake graphics for the brake service page and article (no brands, site colours).

    python3 tools/make_brake_infographic.py hero        > brakes.svg            (1280x960, no text)
    python3 tools/make_brake_infographic.py wear [ka|en|ru] > brake-pad-wear.svg (840x520)
Render to PNG with headless Chrome, then encode jpg/webp/avif (see build notes in the commit).
"""
import math
import sys

YELLOW, WHITE, BG, RED, GREEN = "#facc15", "#f4f4f5", "#0b0b0c", "#f87171", "#4ade80"


def hero():
    W, H, cx, cy = 1280, 960, 560, 500
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         '<defs>'
         '<radialGradient id="bg" cx="45%" cy="45%" r="75%"><stop offset="0" stop-color="#27272a"/><stop offset="1" stop-color="#09090b"/></radialGradient>'
         '<radialGradient id="disc" cx="40%" cy="35%" r="80%"><stop offset="0" stop-color="#d4d4d8"/><stop offset=".55" stop-color="#71717a"/><stop offset="1" stop-color="#3f3f46"/></radialGradient>'
         '<radialGradient id="hat" cx="40%" cy="35%" r="80%"><stop offset="0" stop-color="#52525b"/><stop offset="1" stop-color="#18181b"/></radialGradient>'
         '<linearGradient id="cal" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fde047"/><stop offset="1" stop-color="#ca8a04"/></linearGradient>'
         '<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="18" stdDeviation="22" flood-color="#000" flood-opacity=".6"/></filter>'
         '</defs>',
         f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
         f'<circle cx="{cx}" cy="{cy}" r="360" fill="url(#disc)" filter="url(#sh)"/>']
    # machined rings
    for r, op in ((350, .25), (300, .12), (250, .12), (205, .2)):
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#18181b" stroke-opacity="{op}" stroke-width="2"/>')
    # drilled holes in staggered spirals
    for i in range(36):
        a = math.radians(i * 10)
        for k, r in enumerate((240, 285, 325)):
            aa = a + math.radians(k * 3.3)
            o.append(f'<circle cx="{cx + r * math.cos(aa):.1f}" cy="{cy + r * math.sin(aa):.1f}" r="7" fill="#27272a"/>')
    # hat + lug holes + centre bore
    o.append(f'<circle cx="{cx}" cy="{cy}" r="180" fill="url(#hat)" stroke="#a1a1aa" stroke-opacity=".35" stroke-width="3"/>')
    for i in range(5):
        a = math.radians(-90 + i * 72)
        o.append(f'<circle cx="{cx + 105 * math.cos(a):.1f}" cy="{cy + 105 * math.sin(a):.1f}" r="17" fill="#09090b" stroke="#71717a" stroke-width="3"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="48" fill="#09090b" stroke="#71717a" stroke-width="4"/>')

    # caliper over the right edge of the disc (arc band), with a pad visible inside
    def arc_band(r1, r2, a1, a2):
        p = lambda r, a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
        (x1, y1), (x2, y2), (x3, y3), (x4, y4) = p(r2, a1), p(r2, a2), p(r1, a2), p(r1, a1)
        return (f'M{x1:.1f},{y1:.1f} A{r2},{r2} 0 0 1 {x2:.1f},{y2:.1f} L{x3:.1f},{y3:.1f} '
                f'A{r1},{r1} 0 0 0 {x4:.1f},{y4:.1f} Z')
    o.append(f'<path d="{arc_band(205, 405, -42, 42)}" fill="url(#cal)" filter="url(#sh)"/>')
    o.append(f'<path d="{arc_band(232, 378, -30, 30)}" fill="none" stroke="#a16207" stroke-width="4" stroke-opacity=".7"/>')
    o.append(f'<path d="{arc_band(214, 224, -34, 34)}" fill="#3f3f46"/>')   # pad edge peeking out
    for a in (-20, 0, 20):                                                   # bolts
        x, y = cx + 390 * math.cos(math.radians(a)), cy + 390 * math.sin(math.radians(a))
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="11" fill="#713f12"/>')
    o.append(f'<circle cx="{cx + 300}" cy="{cy}" r="34" fill="none" stroke="#fef08a" stroke-opacity=".5" stroke-width="6"/>')
    o.append('</svg>')
    return "\n".join(o)


TEXT = {
    "ka": dict(title="როდის უნდა შეიცვალოს ხუნდები", new="ახალი ხუნდი", new_v="ხახუნის ფენა ≈ 10–12 მმ",
               worn="გაცვეთილი ხუნდი", worn_v="≤ 3 მმ — შესაცვლელია", plate="ლითონის ფირფიტა", fric="ხახუნის ფენა",
               foot="vulkanizacia.ge · ხუნდების შეცვლა გამოძახებით", font="Noto Sans Georgian, Sylfaen, DejaVu Sans, sans-serif"),
    "en": dict(title="When to replace brake pads", new="New pad", new_v="friction material ≈ 10–12 mm",
               worn="Worn pad", worn_v="≤ 3 mm — replace", plate="backing plate", fric="friction material",
               foot="vulkanizacia.ge · mobile brake service", font="Inter, Helvetica, Arial, sans-serif"),
    "ru": dict(title="Когда менять тормозные колодки", new="Новая колодка", new_v="фрикционный слой ≈ 10–12 мм",
               worn="Изношенная колодка", worn_v="≤ 3 мм — пора менять", plate="металлическая основа", fric="фрикционный слой",
               foot="vulkanizacia.ge · замена колодок с выездом", font="Inter, Helvetica, Arial, sans-serif"),
}


def wear(lang):
    T = TEXT[lang]
    W, H = 840, 520
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{T["font"]}">',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         f'<text x="{W / 2}" y="62" text-anchor="middle" fill="{WHITE}" font-size="32" font-weight="800">{T["title"]}</text>']

    def pad(x, fric_h, colour, label, value, vcol):
        base_y, plate_h, w = 380, 34, 250
        o.append(f'<rect x="{x}" y="{base_y}" width="{w}" height="{plate_h}" rx="6" fill="#71717a"/>')
        o.append(f'<rect x="{x + 12}" y="{base_y - fric_h}" width="{w - 24}" height="{fric_h}" rx="8" fill="{colour}"/>')
        # dimension arrow
        ax = x + w + 22
        o.append(f'<line x1="{ax}" y1="{base_y - fric_h}" x2="{ax}" y2="{base_y}" stroke="{vcol}" stroke-width="3"/>')
        for yy in (base_y - fric_h, base_y):
            o.append(f'<line x1="{ax - 9}" y1="{yy}" x2="{ax + 9}" y2="{yy}" stroke="{vcol}" stroke-width="3"/>')
        o.append(f'<text x="{x + w / 2}" y="140" text-anchor="middle" fill="{WHITE}" font-size="26" font-weight="700">{label}</text>')
        o.append(f'<text x="{x + w / 2}" y="176" text-anchor="middle" fill="{vcol}" font-size="21" font-weight="700">{value}</text>')
        o.append(f'<text x="{x + w / 2}" y="{base_y + 62}" text-anchor="middle" fill="#a1a1aa" font-size="17">{T["plate"]}</text>')

    pad(95, 150, "#52525b", T["new"], T["new_v"], GREEN)
    pad(475, 40, "#7f1d1d", T["worn"], T["worn_v"], RED)
    o.append(f'<text x="220" y="310" text-anchor="middle" fill="#d4d4d8" font-size="18">{T["fric"]}</text>')
    o.append(f'<text x="{W / 2}" y="{H - 28}" text-anchor="middle" fill="{YELLOW}" font-size="18" font-weight="700">{T["foot"]}</text>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    print(hero() if sys.argv[1] == "hero" else wear(sys.argv[2] if len(sys.argv) > 2 else "ka"))
