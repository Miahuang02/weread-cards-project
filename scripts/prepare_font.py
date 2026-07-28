#!/usr/bin/env python3
"""
prepare_font.py
下载 Noto Sans SC 字体并子集化，只保留 highlights.json 中实际用到的字符。
输出 NotoSansSC-subset.ttf 到仓库根目录，供 generate_pdf.py 使用。
"""
import json
import os
import urllib.request
from pathlib import Path

FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/Variable/TTF/Subset/NotoSansSC-VF.ttf"
OUTPUT_FONT = Path(__file__).parent.parent / "NotoSansSC-subset.ttf"
DATA_FILE = Path(__file__).parent.parent / "data" / "highlights.json"


def download_font(cache_path: Path):
    """下载完整字体到缓存"""
    print(f"下载字体: {FONT_URL}")
    urllib.request.urlretrieve(FONT_URL, str(cache_path))
    print(f"字体已下载: {cache_path} ({cache_path.stat().st_size / 1024 / 1024:.1f}MB)")


def prepare_font():
    if not DATA_FILE.exists():
        print("未找到 highlights.json，跳过字体准备")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        cards = json.load(f)

    text = ""
    for c in cards:
        text += c.get("text", "") + c.get("book", "") + c.get("chapter", "")

    # 额外保留常用字符
    extra = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ，。！？、；：“”‘’（）《》【】—…· \n\t"
    glyphs = set(text) | set(extra)
    glyph_text = "".join(glyphs)

    print(f"共 {len(glyphs)} 个唯一字符需要保留")

    # 查找缓存字体
    cache_dir = Path(__file__).parent.parent / ".font-cache"
    cache_dir.mkdir(exist_ok=True)
    cache_font = cache_dir / "NotoSansSC-VF.ttf"

    if not cache_font.exists():
        download_font(cache_font)

    # 子集化
    from fontTools.subset import Subsetter
    from fontTools.ttLib import TTFont

    font = TTFont(str(cache_font))
    subsetter = Subsetter()
    subsetter.populate(text=glyph_text)
    subsetter.subset(font)
    font.flavor = None
    font.save(str(OUTPUT_FONT))
    print(f"子集字体已保存: {OUTPUT_FONT} ({OUTPUT_FONT.stat().st_size / 1024:.1f}KB)")


if __name__ == "__main__":
    prepare_font()
