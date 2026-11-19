"""Draw the "how to read a tyre size" infographic (Georgian labels, example 205/55 R16 91V) as SVG.

Render to PNG with headless Chrome, then encode to webp/avif/jpg (see the shell commands in the repo history):
    python3 tools/make_tyre_size_infographic.py > /tmp/tyre-size.svg
"""
import math

W, H = 840, 520
CX, CY = 420, 1590           # tyre centre far below the canvas -> gentle arc
R_TREAD, R_SIDE, R_TEXT, R_RIM = 1270, 1235, 1170, 1080
YELLOW, WHITE, BG = "#facc15", "#f4f4f5", "#0b0b0c"

# (token on the tyre, x on canvas, label, value, label row)
PARTS = [
    ("205/", 140, "სიგანე", "205 მმ", 0),
    ("55", 258, "პროფილი", "სიგანის 55%", 1),
    ("R", 362, "კონსტრუქცია", "რადიალური", 0),
    ("16", 448, "დისკის დიამეტრი", "16 დიუმი", 1),
    ("91", 592, "დატვირთვის ინდექსი", "615 კგ-მდე", 0),
    ("V", 694, "სიჩქარის ინდექსი", "240 კმ/სთ-მდე", 1),
]
ROW_Y = [150, 238]           # label rows (baseline of the label)


def on_arc(x, r):
    dx = x - CX
    y = CY - math.sqrt(r * r - dx * dx)
    angle = math.degrees(math.atan2(dx, math.sqrt(r * r - dx * dx)))
    return y, angle


def svg():
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'font-family="Noto Sans Georgian, Sylfaen, DejaVu Sans, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="{BG}"/>',
           '<defs><radialGradient id="g" cx="50%" cy="0%" r="90%"><stop offset="0" stop-color="#3f3f46"/><stop offset="1" stop-color="#111113"/></radialGradient></defs>',
           # tyre: tread band, sidewall, rim edge
           f'<circle cx="{CX}" cy="{CY}" r="{R_TREAD}" fill="#18181b"/>',
           f'<circle cx="{CX}" cy="{CY}" r="{R_SIDE}" fill="url(#g)"/>',
           f'<circle cx="{CX}" cy="{CY}" r="{R_RIM}" fill="#0f0f10" stroke="#52525b" stroke-width="3"/>']
    # tread blocks
    for i in range(-40, 41):
        a = math.radians(i * 0.9)
        x1, y1 = CX + R_TREAD * math.sin(a), CY - R_TREAD * math.cos(a)
        x2, y2 = CX + (R_TREAD - 30) * math.sin(a), CY - (R_TREAD - 30) * math.cos(a)
        out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#0b0b0c" stroke-width="6"/>')
    out.append(f'<text x="{W / 2}" y="62" text-anchor="middle" fill="{WHITE}" font-size="34" font-weight="800">როგორ წავიკითხოთ საბურავის ზომა</text>')
    for token, x, label, value, row in PARTS:
        ty, ang = on_arc(x, R_TEXT)
        out.append(f'<text x="{x}" y="{ty:.1f}" transform="rotate({ang:.2f} {x} {ty:.1f})" text-anchor="middle" '
                   f'fill="{YELLOW}" font-size="56" font-weight="800" font-family="Arial Black, Arial, sans-serif">{token}</text>')
        # leader: from token top straight up to the label row
        top = ty - 52
        ly = ROW_Y[row] + 34
        out.append(f'<polyline points="{x},{top:.1f} {x},{ly}" fill="none" stroke="{WHITE}" stroke-width="2" opacity=".85"/>')
        out.append(f'<circle cx="{x}" cy="{top:.1f}" r="4" fill="{WHITE}"/>')
        out.append(f'<text x="{x}" y="{ROW_Y[row]}" text-anchor="middle" fill="{YELLOW}" font-size="17" font-weight="700">{label}</text>')
        out.append(f'<text x="{x}" y="{ROW_Y[row] + 24}" text-anchor="middle" fill="{WHITE}" font-size="15">{value}</text>')
    out.append(f'<text x="{W / 2}" y="{H - 18}" text-anchor="middle" fill="#a1a1aa" font-size="15">მაგალითი: 205/55 R16 91V · vulkanizacia.ge</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    print(svg())
