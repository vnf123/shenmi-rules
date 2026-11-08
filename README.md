# 神秘复苏 · 人间如狱 — 规则书 V3.0（纯文本直读镜像）

《神秘复苏》自由大世界 AI 文字模拟游戏规则书 V3.0，以 **纯 `text/plain` / UTF-8** 形式托管，供 AI 模型直接抓取原文，无 HTML、无脚本、无渲染层。

## 直读入口

| 用途 | 地址 |
|---|---|
| 全文（911,558 bytes / 890 KB，单文件） | https://raw.githubusercontent.com/vnf123/shenmi-rules/main/rules-v3.0.txt |
| 机器可读清单（分片 / 行号 / 字节 / sha256） | https://raw.githubusercontent.com/vnf123/shenmi-rules/main/manifest.json |
| 分片索引（Markdown 表格） | https://raw.githubusercontent.com/vnf123/shenmi-rules/main/INDEX.md |
| 分片目录 | https://raw.githubusercontent.com/vnf123/shenmi-rules/main/parts/part-00.txt … part-13.txt |

## 抓取建议

1. `GET manifest.json` → 读取 `parts[]` 列表。
2. 逐个 `GET parts[].raw_url`，每片约 60–70 KB、以章标题起始，可独立理解。
3. 需要全文时直接取 `rules-v3.0.txt`；抓取端有截断阈值时按分片走。

## 文件结构

```
rules-v3.0.txt      原始全文（UTF-8 / 911,558 bytes / 16,751 行，与源文件逐字节一致）
parts/part-NN.txt   14 个分片，按章边界 + 70KB 上界切分
manifest.json       分片元数据：章节范围、行号、字节数、sha256、raw 地址
INDEX.md            人类可读的分片索引
build.py            可复现的分片构建脚本
```

## 完整性

- 编码：UTF-8（无 BOM），换行沿用原文（LF 为主，含少量 CRLF），未做任何归一化
- 分片按顺序拼接与原文逐字节一致的校验：**PASS**（`manifest.json` 中 `lossless_reassembly_verified: true`）
- 单片 sha256 见 `manifest.json`，可用于抓取后校验

## 版权

规则书文本版权归原作者（DY 我有玉玉症）所有，本仓库仅为便于 AI 读取的纯文本镜像，未对正文做任何改写、删节或增补。
