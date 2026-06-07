#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image_designer.py — har post uchun jozibali karta-rasm yaratadi.
Pillow (PIL) kerak:  pip install pillow

Ishlatish (test):
    python image_designer.py        # content_bank dan namuna kartalar yaratadi
"""

import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "cards")
os.makedirs(OUT_DIR, exist_ok=True)

W, H = 1080, 1080

# Tur bo'yicha gradient ranglar (yuqori, past)
THEMES = {
    "vocabulary": ((37, 99, 235), (79, 70, 229)),
    "test":       ((234, 88, 12), (190, 24, 93)),
    "grammar":    ((5, 150, 105), (4, 120, 87)),
    "topic":      ((13, 148, 136), (8, 145, 178)),
    "fact":       ((124, 58, 237), (76, 29, 149)),
    "tip":        ((217, 119, 6), (180, 83, 9)),
    "idiom":      ((219, 39, 119), (131, 24, 67)),
    "default":    ((30, 41, 59), (15, 23, 42)),
}

TYPE_LABEL = {
    "vocabulary": "VOCABULARY", "test": "QUIZ", "grammar": "GRAMMAR",
    "topic": "TOPIC", "fact": "DID YOU KNOW?", "tip": "IELTS TIP",
    "idiom": "IDIOM",
}

# Shrift yo'llari (Windows -> sandbox fallback)
FONT_CANDIDATES = {
    "bold": [
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "regular": [
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
    "emoji": [
        r"C:\Windows\Fonts\seguiemj.ttf",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    ],
}


def _font(kind, size):
    for path in FONT_CANDIDATES.get(kind, []):
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _gradient(top, bottom):
    base = Image.new("RGB", (W, H), top)
    draw = ImageDraw.Draw(base)
    for y in range(H):
        t = y / H
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return base


def _wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_card(post, out_path=None):
    typ = post.get("type", "default")
    top, bottom = THEMES.get(typ, THEMES["default"])
    img = _gradient(top, bottom)
    draw = ImageDraw.Draw(img, "RGBA")

    # Yengil dekorativ doiralar
    draw.ellipse([W - 320, -160, W + 160, 320], fill=(255, 255, 255, 18))
    draw.ellipse([-200, H - 260, 220, H + 160], fill=(255, 255, 255, 14))

    margin = 90

    # Yuqori chap: tur belgisi (pill)
    label = TYPE_LABEL.get(typ, typ.upper())
    fl = _font("bold", 34)
    lw = draw.textlength(label, font=fl)
    pad = 28
    draw.rounded_rectangle(
        [margin, margin, margin + lw + pad * 2, margin + 64],
        radius=32, fill=(255, 255, 255, 235))
    draw.text((margin + pad, margin + 13), label, font=fl, fill=bottom)

    # Yuqori o'ng: daraja doirasi
    level = post.get("level", "")
    if level:
        d = 130
        cx0 = W - margin - d
        draw.ellipse([cx0, margin, cx0 + d, margin + d], outline=(255, 255, 255, 255), width=6)
        flev = _font("bold", 52)
        tw = draw.textlength(level, font=flev)
        draw.text((cx0 + (d - tw) / 2, margin + 30), level, font=flev, fill=(255, 255, 255, 255))

    # Markaz: katta emoji (imkon bo'lsa)
    emoji = post.get("emoji", "")
    cy = 360
    if emoji:
        fe = _font("emoji", 180)
        # Faqat haqiqiy emoji shrifti yuklangan bo'lsa chizamiz (tofu/quti chiqmasligi uchun)
        if isinstance(fe, ImageFont.FreeTypeFont):
            try:
                ew = draw.textlength(emoji, font=fe)
                draw.text(((W - ew) / 2, cy), emoji, font=fe, embedded_color=True)
                cy += 230
            except Exception:
                cy += 40
        else:
            cy += 40

    # Sarlavha (katta, markazda)
    title = post.get("title", "")
    ft = _font("bold", 86)
    lines = _wrap(draw, title, ft, W - margin * 2)
    line_h = 104
    block_h = len(lines) * line_h
    ty = max(cy, (H - block_h) // 2 + 40)
    for ln in lines:
        tw = draw.textlength(ln, font=ft)
        # soya
        draw.text(((W - tw) / 2 + 3, ty + 3), ln, font=ft, fill=(0, 0, 0, 70))
        draw.text(((W - tw) / 2, ty), ln, font=ft, fill=(255, 255, 255, 255))
        ty += line_h

    # Pastki brend
    fb = _font("bold", 40)
    brand = "English free course"
    bw = draw.textlength(brand, font=fb)
    draw.text(((W - bw) / 2, H - 150), brand, font=fb, fill=(255, 255, 255, 255))
    fh = _font("regular", 32)
    handle = "@English_news_free"
    hw = draw.textlength(handle, font=fh)
    draw.text(((W - hw) / 2, H - 95), handle, font=fh, fill=(255, 255, 255, 200))

    if out_path is None:
        out_path = os.path.join(OUT_DIR, f"{post.get('id', 'card')}.png")
    img.save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    import json
    with open(os.path.join(BASE_DIR, "content_bank.json"), encoding="utf-8") as f:
        data = json.load(f)
    samples = data["posts"][:8]
    for p in samples:
        path = make_card(p)
        print("Yaratildi:", path)
    print(f"\nJami {len(samples)} namuna karta '{OUT_DIR}' papkasida.")
