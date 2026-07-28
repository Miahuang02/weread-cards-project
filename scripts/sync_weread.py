#!/usr/bin/env python3
"""
sync_weread.py
通过微信读书 Skill API 拉取划线，生成 highlights.json
每条划线 = 一条记录，包含 book/chapter/text/created_at

API 文档: https://github.com/Tencent/WeChatReading
统一入口: POST https://i.weread.qq.com/api/agent/gateway
鉴权: Authorization: Bearer wrk-xxxxxxxx
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

GATEWAY = "https://i.weread.qq.com/api/agent/gateway"
SKILL_VERSION = "1.0.4"

OUTPUT_FILE = Path(__file__).parent.parent / "data" / "highlights.json"


def get_api_key():
    key = os.environ.get("WEREAD_API_KEY")
    if not key:
        print("错误：未设置 WEREAD_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)
    return key


def call_api(api_key, api_name, **params):
    """调用微信读书 Skill API 统一网关"""
    body = {"api_name": api_name, "skill_version": SKILL_VERSION}
    body.update(params)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(GATEWAY, json=body, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("errcode", 0) != 0:
        msg = data.get("errmsg", "未知错误")
        print(f"API错误 [{api_name}]: {msg}", file=sys.stderr)
        return None
    return data


def fetch_notebooks(api_key):
    """获取所有有笔记的书籍（支持翻页）"""
    books = []
    last_sort = None
    page = 1
    while True:
        params = {"count": 100}
        if last_sort is not None:
            params["lastSort"] = last_sort
        data = call_api(api_key, "/user/notebooks", **params)
        if not data:
            break
        page_books = data.get("books", [])
        books.extend(page_books)
        print(f"  笔记本第{page}页: {len(page_books)} 本")
        if data.get("hasMore") == 1 and page_books:
            last_sort = page_books[-1].get("sort")
            page += 1
            time.sleep(0.3)
        else:
            break
    print(f"共 {len(books)} 本有笔记的书")
    return books


def fetch_bookmarks(api_key, book_id, book_title=""):
    """获取某本书的划线内容"""
    data = call_api(api_key, "/book/bookmarklist", bookId=book_id)
    if not data:
        return []
    bookmarks = data.get("updated", [])
    chapters = {c["chapterUid"]: c.get("title", "未知章节")
                for c in data.get("chapters", [])}
    if book_title:
        print(f"  《{book_title}》: {len(bookmarks)} 条划线")
    return bookmarks, chapters


def parse_bookmarks(bookmarks, chapters, book_title):
    """把原始划线转成统一格式"""
    results = []
    # 清洗书名：去掉可能的 UUID 前缀
    if book_title and "_" in book_title:
        book_title = book_title.split("_", 1)[1]
    for bm in bookmarks:
        text = bm.get("markText", "").strip()
        chapter_uid = bm.get("chapterUid")
        chapter = chapters.get(chapter_uid, "未知章节")
        created = bm.get("createTime", "")
        if created and isinstance(created, (int, float)):
            try:
                created = datetime.fromtimestamp(created).isoformat()
            except Exception:
                created = str(created)
        if text:
            results.append({
                "book": book_title,
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

    # 1. 获取所有有笔记的书
    print("=== 获取笔记书籍列表 ===")
    notebooks = fetch_notebooks(api_key)
    if not notebooks:
        print("没有找到有笔记的书籍")
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text("[]", encoding="utf-8")
        return

    # 2. 逐本拉取划线
    print("\n=== 拉取划线内容 ===")
    all_highlights = []
    for nb in notebooks:
        book_id = nb.get("bookId")
        book_title = nb.get("book", {}).get("title", "未知书名")
        if not book_id:
            continue
        try:
            bookmarks, chapters = fetch_bookmarks(api_key, book_id, book_title)
            highlights = parse_bookmarks(bookmarks, chapters, book_title)
            all_highlights.extend(highlights)
            time.sleep(0.3)  # 避免请求过快
        except Exception as e:
            print(f"  《{book_title}》拉取失败: {e}", file=sys.stderr)

    # 3. 合并去重
    existing = load_existing()
    merged = merge_highlights(existing, all_highlights)

    # 4. 写入文件
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成 ===")
    print(f"共 {len(merged)} 条划线（本次拉取 {len(all_highlights)}，去重后写入 {len(merged)}）")
    print(f"输出: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
