#!/usr/bin/env python3
"""
sync_weread.py
从微信读书拉取划线，生成 highlights.json
每条划线 = 一条记录，包含 book/chapter/text/created_at
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# 微信读书 Skill API 配置
SKILL_API = "https://weread.qq.com/r/weread-skills"
SKILL_ID = "wr_2024"

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "highlights.json"


def get_api_key():
    key = os.environ.get("WEREAD_API_KEY")
    if not key:
        print("错误：未设置 WEREAD_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    return key


def fetch_bookshelf(api_key):
    """获取书架书籍列表"""
    url = f"{SKILL_API}/api/bookshelf"
    headers = {"Authorization": f"Bearer {api_key}"}
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    books = data.get("books", data.get("data", {}).get("books", []))
    print(f"书架共 {len(books)} 本书")
    return books


def fetch_bookmarks(api_key, book_id, book_name=""):
    """获取某本书的划线"""
    url = f"{SKILL_API}/api/bookmark/list"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"bookId": book_id}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # 兼容不同返回结构
    bookmarks = data.get("bookmarks", data.get("data", {}).get("bookmarks", []))
    if book_name:
        print(f"  《{book_name}》: {len(bookmarks)} 条划线")
    return bookmarks


def parse_bookmarks(bookmarks, book_name):
    """把原始划线转成统一格式"""
    results = []
    for bm in bookmarks:
        # 微信读书划线字段：bookmarkText / chapterName / createTime
        text = bm.get("bookmarkText", bm.get("content", "")).strip()
        chapter = bm.get("chapterName", bm.get("chapter", "未知章节"))
        created = bm.get("createTime", "")
        if created and isinstance(created, (int, float)):
            # 微信读书 createTime 是秒级时间戳
            try:
                created = datetime.fromtimestamp(created).isoformat()
            except Exception:
                created = str(created)

        if text:
            results.append({
                "book": book_name,
                "chapter": chapter,
                "text": text,
                "created_at": created,
            })
    return results


def load_existing():
    """加载已有数据（用于增量合并 + 去重）"""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def merge_highlights(existing, new_data):
    """合并 + 去重（按 book+text 去重）"""
    seen = set()
    merged = []
    for h in existing + new_data:
        key = (h.get("book", ""), h.get("text", ""))
        if key not in seen:
            seen.add(key)
            merged.append(h)
    # 按书名 + 创建时间排序
    merged.sort(key=lambda x: (x.get("book", ""), x.get("created_at", "")))
    return merged


def main():
    api_key = get_api_key()
    books = fetch_bookshelf(api_key)

    all_highlights = []
    for book in books:
        book_id = book.get("bookId", book.get("book_id", ""))
        book_name = book.get("bookName", book.get("title", "未知书名"))
        if not book_id:
            continue
        try:
            bookmarks = fetch_bookmarks(api_key, book_id, book_name)
            highlights = parse_bookmarks(bookmarks, book_name)
            all_highlights.extend(highlights)
            time.sleep(0.5)  # 避免请求过快
        except Exception as e:
            print(f"  《{book_name}》拉取失败: {e}", file=sys.stderr)

    existing = load_existing()
    merged = merge_highlights(existing, all_highlights)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\n完成：共 {len(merged)} 条划线（新增 {len(all_highlights)}，去重后写入 {len(merged)}）")
    print(f"输出：{OUTPUT_FILE}")


if __name__ == "__main__":
    main()
