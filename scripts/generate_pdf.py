#!/usr/bin/env python3
"""
generate_pdf.py
读取 highlights.json，生成 A4 多卡片 PDF（2×3=6张/页，带裁剪虚线）
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

DATA_FILE = Path(__file__).parent.parent / "data" / "highlights.json"
OUTPUT_FILE = Path(__file__).parent.parent / "highlights.pdf"

DPI = 300
PAGE_W = int(210 / 25.4 * DPI)
PAGE_H = int(297 / 25.4 * DPI)
MARGIN = int(8 / 25.4 * DPI)
GAP = int(3 / 25.4 * DPI)
COLS, ROWS = 2, 3


def find_font(size):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_w):
    lines, current = [], ""
    for ch in text:
        test = current + ch
        if draw.textbbox((0,0), test, font=font)[2] > max_w and current:
            lines.append(current)
            current = ch
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def render_card(text, w, h):
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(0,0),(w-1,h-1)], outline="#999999", width=2)
    pad = int(8 / 25.4 * DPI)
    max_w, max_h = w - 2*pad, h - 2*pad
    font_size = 42
    while font_size >= 22:
        font = find_font(font_size)
        line_h = int(font_size * 1.5)
        lines = wrap_text(draw, text, font, max_w)
        if len(lines) * line_h <= max_h:
            break
        font_size -= 2
    font = find_font(font_size)
    line_h = int(font_size * 1.5)
    lines = wrap_text(draw, text, font, max_w)
    while len(lines) * line_h > max_h and lines:
        lines.pop()
    if lines:
        lines[-1] = lines[-1][:-2] + "…"
    total_h = len(lines) * line_h
    start_y = (h - total_h) // 2 + font_size // 2
    for i, line in enumerate(lines):
        tw = draw.textbbox((0,0), line, font=font)[2]
        draw.text(((w-tw)//2, start_y + i*line_h), line, fill="#222222", font=font)
    return img


def render_page(highlights):
    page = Image.new("RGB", (PAGE_W, PAGE_H), "white")
    draw = ImageDraw.Draw(page)
    cw = (PAGE_W - 2*MARGIN - (COLS-1)*GAP) // COLS
    ch = (PAGE_H - 2*MARGIN - (ROWS-1)*GAP) // ROWS
    for i, text in enumerate(highlights[:COLS*ROWS]):
        col, row = i % COLS, i // COLS
        x = MARGIN + col * (cw + GAP)
        y = MARGIN + row * (ch + GAP)
        page.paste(render_card(text, cw, ch), (x, y))
    # 裁剪虚线
    for i in range(1, COLS):
        x = MARGIN + i*cw + (i-1)*GAP + GAP//2
        for y in range(MARGIN, PAGE_H-MARGIN, 8):
            draw.line([(x,y),(x,min(y+4,PAGE_H-MARGIN))], fill="#bbb", width=2)
    for i in range(1, ROWS):
        y = MARGIN + i*ch + (i-1)*GAP + GAP//2
        for x in range(MARGIN, PAGE_W-MARGIN, 8):
            draw.line([(x,y),(min(x+4,PAGE_W-MARGIN),y)], fill="#bbb", width=2)
    return page


def main():
    if not DATA_FILE.exists():
        print("未找到 highlights.json，跳过PDF生成")
        return
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        highlights = json.load(f)
    texts = [h["text"] for h in highlights if h.get("text")]
    per_page = COLS * ROWS
    pages = [render_page(texts[i:i+per_page]) for i in range(0, len(texts), per_page)]
    if pages:
        pages[0].save(OUTPUT_FILE, save_all=True, append_images=pages[1:],
                      resolution=DPI, quality=95)
        print(f"已生成PDF: {OUTPUT_FILE}（{len(texts)}条划线，{len(pages)}页）")
    else:
        print("无划线数据，跳过PDF生成")


if __name__ == "__main__":
    main()
