#!/usr/bin/env python3
"""
generate_html.py
读取 highlights.json，生成手机卡片网页 index.html
功能：左右滑动翻卡片、搜索、按书筛选、下载PDF入口
"""
import json
from pathlib import Path
from html import escape

DATA_FILE = Path(__file__).parent.parent / "data" / "highlights.json"
OUTPUT_FILE = Path(__file__).parent.parent / "index.html"


def load_highlights():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_html(highlights):
    # 按书分组统计
    books = {}
    for h in highlights:
        name = h.get("book", "未知")
        if name not in books:
            books[name] = 0
        books[name] += 1

    # 生成卡片数据（JSON 嵌入页面，前端渲染）
    cards_json = json.dumps(highlights, ensure_ascii=False)

    books_options = "".join(
        f'<option value="{escape(name)}">{escape(name)} ({count})</option>'
        for name, count in sorted(books.items())
    )

    html = HTML_TEMPLATE.replace("__BOOKS_OPTIONS__", books_options)
    html = html.replace("__CARDS_JSON__", cards_json)
    return html


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>微信读书划线卡片</title>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --bg: #f5f5f7;
  --card-bg: #ffffff;
  --text: #1d1d1f;
  --text-secondary: #86868b;
  --accent: #0071e3;
  --border: #d2d2d7;
}
body {
  font-family: -apple-system, "PingFang SC", "Helvetica Neue", "Noto Sans CJK SC", sans-serif;
  background: var(--bg);
  color: var(--text);
  -webkit-tap-highlight-color: transparent;
}
.header {
  position: sticky; top:0; z-index:10;
  background: rgba(245,245,247,0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  padding: 12px 16px 8px;
}
.header h1 { font-size:18px; font-weight:600; margin-bottom:8px; }
.controls { display:flex; gap:8px; align-items:center; }
.controls input[type=text] {
  flex:1; padding:8px 12px; font-size:15px;
  border:1px solid var(--border); border-radius:10px;
  background:var(--card-bg); outline:none;
}
.controls input[type=text]:focus { border-color:var(--accent); }
.controls select {
  padding:8px 12px; font-size:14px; max-width:40%;
  border:1px solid var(--border); border-radius:10px;
  background:var(--card-bg); color:var(--text);
}
.card-container {
  display:flex; flex-direction:column; gap:12px;
  padding:16px; padding-bottom:80px;
}
.card {
  background:var(--card-bg);
  border-radius:16px;
  padding:24px 20px;
  box-shadow:0 1px 3px rgba(0,0,0,0.08);
  transition: transform 0.2s;
}
.card:active { transform:scale(0.98); }
.card .book-tag {
  font-size:12px; color:var(--accent);
  margin-bottom:12px; font-weight:500;
}
.card .text {
  font-size:17px; line-height:1.7;
  color:var(--text); font-weight:400;
}
.card .chapter {
  font-size:12px; color:var(--text-secondary);
  margin-top:16px;
}
.empty {
  text-align:center; padding:60px 20px;
  color:var(--text-secondary); font-size:15px;
}
.footer {
  position:fixed; bottom:0; left:0; right:0;
  background:rgba(245,245,247,0.9);
  backdrop-filter:blur(20px);
  border-top:1px solid var(--border);
  padding:12px 16px;
  display:flex; justify-content:space-between; align-items:center;
  font-size:13px; color:var(--text-secondary);
}
.footer a {
  color:var(--accent); text-decoration:none;
  font-weight:500;
}
</style>
</head>
<body>
<div class="header">
  <h1>📚 划线卡片</h1>
  <div class="controls">
    <input type="text" id="search" placeholder="搜索划线内容...">
    <select id="bookFilter">
      <option value="">全部书籍</option>
      __BOOKS_OPTIONS__
    </select>
  </div>
</div>
<div class="card-container" id="cards">
  <div class="empty">加载中...</div>
</div>
<div class="footer">
  <span id="count"></span>
  <a href="highlights.pdf" target="_blank">下载PDF</a>
</div>
<script>
const ALL_CARDS = __CARDS_JSON__;
const container = document.getElementById('cards');
const searchBox = document.getElementById('search');
const bookFilter = document.getElementById('bookFilter');
const countEl = document.getElementById('count');

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s || '';
  return d.innerHTML;
}

function render() {
  let filtered = ALL_CARDS;
  const q = searchBox.value.trim();
  const bk = bookFilter.value;
  if (bk) filtered = filtered.filter(c => c.book === bk);
  if (q) filtered = filtered.filter(c =>
    c.text.includes(q) || (c.book && c.book.includes(q))
  );

  container.innerHTML = '';
  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty">没有匹配的划线</div>';
    countEl.textContent = '0 条';
    return;
  }
  filtered.forEach(c => {
    const div = document.createElement('div');
    div.className = 'card';
    let html = '<div class="book-tag">' + esc(c.book) + '</div>';
    html += '<div class="text">' + esc(c.text) + '</div>';
    if (c.chapter) html += '<div class="chapter">' + esc(c.chapter) + '</div>';
    div.innerHTML = html;
    container.appendChild(div);
  });
  countEl.textContent = filtered.length + ' 条划线';
}
searchBox.addEventListener('input', render);
bookFilter.addEventListener('change', render);
render();
</script>
</body>
</html>"""


def main():
    highlights = load_highlights()
    html = generate_html(highlights)
    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"已生成卡片网页: {OUTPUT_FILE}")
    print(f"共 {len(highlights)} 条划线")


if __name__ == "__main__":
    main()
