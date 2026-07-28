#!/usr/bin/env python3
"""
generate_pdf.py
读取 highlights.json，用 reportlab + CID 字体生成 A4 多卡片 PDF。
每页 6 张卡片（2列 × 3行），带裁剪虚线。
使用 STSong-Light CID 字体，确保所有设备正确显示中文。
"""
import json
import textwrap
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

DATA_FILE = Path(__file__).parent.parent / "data" / "highlights.json"
FONT_FILE = Path(__file__).parent.parent / "NotoSansSC-subset.ttf"
OUTPUT_PDF = Path(__file__).parent.parent / "highlights.pdf"

# 页面布局参数
MARGIN = 8 * mm
GAP = 3 * mm
PAGE_W, PAGE_H = A4
CARD_W = (PAGE_W - 2 * MARGIN - GAP) / 2
CARD_H = (PAGE_H - 2 * MARGIN - 2 * GAP) / 3
CARD_PADDING = 5 * mm

FONT_MAIN = "NotoSansSC"
BOOK_TAG_CHARS = 22


def clean_book_name(book):
    """去掉 book 字段前面的 UUID 等前缀，只保留书名"""
    if not book:
        return "未知书名"
    if "_" in book:
        return book.split("_", 1)[1]
    return book


def wrap_text(text, chars_per_line):
    """中文文本换行：按字符数截断"""
    if not text:
        return []
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph:
            lines.append('')
            continue
        # 中英文混合：按字符数换行
        wrapped = textwrap.wrap(paragraph, width=chars_per_line,
                                break_long_words=True,
                                replace_whitespace=False)
        if not wrapped:
            lines.append('')
        else:
            lines.extend(wrapped)
    return lines


def draw_card(c, x, y, book, text):
    """在指定位置绘制一张卡片"""
    book = clean_book_name(book)

    # 卡片边框
    c.setStrokeColor(Color(0.6, 0.6, 0.6))
    c.setLineWidth(0.4)
    c.rect(x, y, CARD_W, CARD_H, stroke=1, fill=0)

    inner_x = x + CARD_PADDING
    inner_w = CARD_W - 2 * CARD_PADDING
    inner_top = y + CARD_H - CARD_PADDING

    # 书名标签
    c.setFont(FONT_MAIN, 7.5)
    c.setFillColor(Color(0.53, 0.53, 0.53))
    book_display = book if len(book) <= BOOK_TAG_CHARS else book[:BOOK_TAG_CHARS - 1] + '…'
    c.drawString(inner_x, inner_top - 8, book_display)

    # 分隔线
    c.setStrokeColor(Color(0.85, 0.85, 0.85))
    c.setLineWidth(0.3)
    c.line(inner_x, inner_top - 11, inner_x + inner_w, inner_top - 11)

    # 划线正文
    c.setFont(FONT_MAIN, 10)
    c.setFillColor(Color(0.13, 0.13, 0.13))

    # 根据内宽重新计算每行字数
    actual_chars = max(8, int(inner_w / (10 * 0.5 * mm)))
    lines = wrap_text(text, actual_chars)

    line_height = 14
    max_lines = int((CARD_H - 2 * CARD_PADDING - 16) / line_height)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines:
            lines[-1] = lines[-1][:-1] + '…'

    text_y = inner_top - 22
    for line in lines:
        c.drawString(inner_x, text_y, line)
        text_y -= line_height


def draw_crop_lines(c):
    """绘制裁剪虚线"""
    c.setStrokeColor(Color(0.73, 0.73, 0.73))
    c.setDash(2, 2)
    c.setLineWidth(0.3)

    # 垂直裁剪线（中间）
    v_x = MARGIN + CARD_W + GAP / 2
    c.line(v_x, 0, v_x, PAGE_H)

    # 水平裁剪线（两条）
    for row in range(1, 3):
        h_y = PAGE_H - MARGIN - row * CARD_H - (row - 1) * GAP - GAP / 2
        c.line(0, h_y, PAGE_W, h_y)

    c.setDash()  # 重置虚线


def generate(highlights):
    """生成完整 PDF"""
    cards = [(h.get("book", ""), h["text"]) for h in highlights if h.get("text")]

    if not FONT_FILE.exists():
        raise FileNotFoundError(f"字体文件不存在: {FONT_FILE}")

    pdfmetrics.registerFont(TTFont(FONT_MAIN, str(FONT_FILE)))

    c = canvas.Canvas(str(OUTPUT_PDF), pagesize=A4)

    per_page = 6
    total_pages = (len(cards) + per_page - 1) // per_page
    print(f"开始生成PDF：{len(cards)}条划线，{total_pages}页...")

    for page_idx, i in enumerate(range(0, len(cards), per_page)):
        page_cards = cards[i:i + per_page]
        while len(page_cards) < per_page:
            page_cards.append(("", ""))

        draw_crop_lines(c)

        for slot, (book, text) in enumerate(page_cards):
            row = slot // 2
            col = slot % 2
            x = MARGIN + col * (CARD_W + GAP)
            y = PAGE_H - MARGIN - (row + 1) * CARD_H - row * GAP
            if text:
                draw_card(c, x, y, book, text)

        c.showPage()

        if (page_idx + 1) % 100 == 0:
            print(f"  已生成 {page_idx + 1}/{total_pages} 页...")

    c.save()
    print(f"已生成PDF: {OUTPUT_PDF}（{len(cards)}条划线，{total_pages}页）")
    return total_pages


def main():
    if not DATA_FILE.exists():
        print("未找到 highlights.json，跳过PDF生成")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        highlights = json.load(f)

    if not highlights:
        print("无划线数据，跳过PDF生成")
        return

    generate(highlights)


if __name__ == "__main__":
    main()
