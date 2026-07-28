#!/usr/bin/env python3
"""
generate_pdf.py
读取 highlights.json，生成适合打印的 HTML，再用 weasyprint 转为 A4 PDF。
每页 6 张卡片（2列 × 3行），带裁剪虚线。
"""
import json
from pathlib import Path
from weasyprint import HTML, CSS

DATA_FILE = Path(__file__).parent.parent / "data" / "highlights.json"
OUTPUT_HTML = Path(__file__).parent.parent / "print.html"
OUTPUT_PDF = Path(__file__).parent.parent / "highlights.pdf"

# A4 210×297mm，页边距 8mm，可用 194×281mm
# 2列3行，间隙 3mm：
# 卡片宽 = (194 - 3) / 2 = 95.5mm
# 卡片高 = (281 - 6) / 3 = 91.67mm
CARD_W = 95.5
CARD_H = 91.67
GAP = 3
MARGIN = 8

CSS_STYLE = f"""
@page {{
    size: A4;
    margin: {MARGIN}mm;
}}
* {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}}
body {{
    font-family: "Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Micro Hei", "Microsoft YaHei", sans-serif;
    color: #222;
}}
.page {{
    width: {CARD_W * 2 + GAP}mm;
    height: {CARD_H * 3 + GAP * 2}mm;
    position: relative;
    display: grid;
    grid-template-columns: {CARD_W}mm {CARD_W}mm;
    grid-template-rows: {CARD_H}mm {CARD_H}mm {CARD_H}mm;
    gap: {GAP}mm;
}}
.card {{
    width: {CARD_W}mm;
    height: {CARD_H}mm;
    border: 0.3pt solid #999;
    padding: 5mm;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    font-size: 11pt;
    line-height: 1.6;
    overflow: hidden;
    word-break: break-word;
}}
.crop-line-v {{
    position: absolute;
    top: -{MARGIN - 2}mm;
    bottom: -{MARGIN - 2}mm;
    width: 0;
    border-left: 0.5pt dashed #bbb;
}}
.crop-line-h {{
    position: absolute;
    left: -{MARGIN - 2}mm;
    right: -{MARGIN - 2}mm;
    height: 0;
    border-top: 0.5pt dashed #bbb;
}}
"""


def escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate(highlights):
    cards = [h["text"] for h in highlights if h.get("text")]
    per_page = 6
    max_pages = 150  # 上限 150 页 = 900 条卡片，避免渲染过慢
    total_pages = (len(cards) + per_page - 1) // per_page
    if total_pages > max_pages:
        print(f"划线过多（{len(cards)}条/{total_pages}页），截断为前{max_pages}页（{max_pages*per_page}条）")
        cards = cards[:max_pages * per_page]
    pages_html = []

    # 裁剪线位置
    v_pos = CARD_W + GAP / 2  # 列中线
    h_pos1 = CARD_H + GAP / 2
    h_pos2 = CARD_H * 2 + GAP * 1.5

    for i in range(0, len(cards), per_page):
        page_cards = cards[i:i + per_page]
        while len(page_cards) < per_page:
            page_cards.append("")

        cards_html = "\n".join(
            f'<div class="card">{escape_html(text)}</div>'
            for text in page_cards
        )

        lines_html = f"""
            <div class="crop-line-v" style="left:{v_pos}mm;"></div>
            <div class="crop-line-h" style="top:{h_pos1}mm;"></div>
            <div class="crop-line-h" style="top:{h_pos2}mm;"></div>
        """

        pages_html.append(
            f'<div class="page">{lines_html}{cards_html}</div>'
        )

    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>微信读书划线卡片</title>
<style>{CSS_STYLE}</style>
</head>
<body>
{''.join(pages_html)}
</body>
</html>"""
    return full_html


def main():
    if not DATA_FILE.exists():
        print("未找到 highlights.json，跳过PDF生成")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        highlights = json.load(f)

    if not highlights:
        print("无划线数据，跳过PDF生成")
        return

    html = generate(highlights)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    HTML(string=html).write_pdf(str(OUTPUT_PDF))
    print(f"已生成PDF: {OUTPUT_PDF}（{len(highlights)}条划线）")


if __name__ == "__main__":
    main()
