# -*- coding: utf-8 -*-
"""把规则书按章节边界切成 AI 可直接逐段抓取的纯文本分片，并生成 manifest / 目录。"""
import json
import os
import re
import hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "rules-v3.0.txt")
PARTS_DIR = os.path.join(ROOT, "parts")
REPO = "vnf123/shenmi-rules"
BRANCH = "main"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"

TARGET = 70_000          # 每片目标字节数（约 2.3 万汉字，单次抓取安全）
HEAD_RE = re.compile(r"^第\s*\d+\s*章")

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()

# 1. 定位章节起点：只认正文区（跳过目录区）里的真实章标题
toc_end = 0
for i, ln in enumerate(lines):
    if ln.startswith("第 1 章 总协议") and i > 200:
        toc_end = i
        break

sections = []   # (title, start_idx)
sections.append(("前置说明与总目录", 0))
for i in range(toc_end, len(lines)):
    s = lines[i].strip()
    if HEAD_RE.match(s) and "..." not in s and len(s) < 80:
        # 章标题独占一行：下一行通常是空行或正文
        sections.append((s, i))

# 去重相邻同起点
clean = []
for t, i in sections:
    if clean and clean[-1][1] == i:
        continue
    clean.append((t, i))

# 2. 切成块：section 边界 + 目标字节数（超长 section 按行再切，保证无损）
raw_blocks = []
for n, (title, start) in enumerate(clean):
    end = clean[n + 1][1] if n + 1 < len(clean) else len(lines)
    raw_blocks.append({"title": title, "start": start, "end": end})

blocks = []
for b in raw_blocks:
    seg = lines[b["start"]:b["end"]]
    if len("".join(seg).encode("utf-8")) <= TARGET:
        blocks.append({"title": b["title"], "start_line": b["start"] + 1,
                       "end_line": b["end"],
                       "size": len("".join(seg).encode("utf-8")),
                       "text": "".join(seg)})
        continue
    acc, acc_size, sub_start = "", 0, b["start"]
    sub_no = 1
    for i in range(b["start"], b["end"]):
        acc += lines[i]
        acc_size += len(lines[i].encode("utf-8"))
        if acc_size >= TARGET or i == b["end"] - 1:
            blocks.append({"title": f"{b['title']}（续 {sub_no}）",
                           "start_line": sub_start + 1, "end_line": i + 1,
                           "size": acc_size, "text": acc})
            acc, acc_size, sub_start, sub_no = "", 0, i + 1, sub_no + 1

groups, cur, cur_size = [], [], 0
for b in blocks:
    if cur and cur_size + b["size"] > TARGET:
        groups.append(cur)
        cur, cur_size = [], 0
    cur.append(b)
    cur_size += b["size"]
if cur:
    groups.append(cur)

# 3. 写分片
for f in os.listdir(PARTS_DIR):
    os.remove(os.path.join(PARTS_DIR, f))

manifest = []
for idx, g in enumerate(groups):
    name = f"part-{idx:02d}.txt"
    path = os.path.join(PARTS_DIR, name)
    text = ""
    for b in g:
        text += b["text"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    raw = text.encode("utf-8")
    manifest.append({
        "part": name,
        "chapters": [b["title"] for b in g],
        "first_chapter": g[0]["title"],
        "last_chapter": g[-1]["title"],
        "lines": text.count("\n"),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "start_line": g[0]["start_line"],
        "end_line": g[-1]["end_line"],
        "raw_url": f"{RAW_BASE}/parts/{name}",
    })

# 4. 校验无损重组
joined = "".join(open(os.path.join(PARTS_DIR, m["part"]), encoding="utf-8").read() for m in manifest)
orig = open(SRC, encoding="utf-8").read()
lossless = joined == orig

total_bytes = sum(m["bytes"] for m in manifest)
head = {
    "title": "神秘复苏 · 人间如狱 — 自由大世界 AI 文字模拟游戏规则书",
    "version": "V3.0",
    "encoding": "utf-8",
    "format": "text/plain",
    "total_bytes": total_bytes,
    "total_lines": orig.count("\n"),
    "part_count": len(manifest),
    "full_text_raw_url": f"{RAW_BASE}/rules-v3.0.txt",
    "full_text_sha256": hashlib.sha256(orig.encode("utf-8")).hexdigest(),
    "lossless_reassembly_verified": lossless,
    "how_to_read": [
        "抓取 manifest.json 取得分片列表，再逐片 GET raw_url，逐片为 text/plain，无 HTML。",
        "单页需要全文时直取 full_text_raw_url（约 900KB，注意抓取端截断）。",
        "每个分片均以章标题起始，可独立理解，无需跨片上下文即可使用。",
    ],
    "parts": manifest,
}
with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
    json.dump(head, f, ensure_ascii=False, indent=2)

# 5. 生成人类可读的零件索引（同时是 AI 的目录页）
lines_out = [
    "# 分片索引 · 神秘复苏·人间如狱 规则书 V3.0",
    "",
    f"- 全文：`{head['full_text_raw_url']}`",
    f"- 分片数：{len(manifest)} · 总字节：{total_bytes} · 编码：UTF-8 · 纯文本",
    f"- 无损重组校验：{'PASS' if lossless else 'FAIL'}",
    "",
    "| 分片 | 章节范围 | 行 | KB | raw |",
    "|---|---|---|---|---|",
]
for m in manifest:
    rng = m["first_chapter"] if m["first_chapter"] == m["last_chapter"] else f"{m['first_chapter']} → {m['last_chapter']}"
    lines_out.append(f"| `{m['part']}` | {rng} | {m['start_line']}-{m['end_line']} | {m['bytes']/1024:.1f} | [raw]({m['raw_url']}) |")
with open(os.path.join(ROOT, "INDEX.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines_out) + "\n")

print(f"parts={len(manifest)} total_bytes={total_bytes} lossless={lossless}")
for m in manifest:
    print(f"{m['part']}  {m['bytes']:>7}  L{m['start_line']}-{m['end_line']}  {m['first_chapter'][:40]}")
