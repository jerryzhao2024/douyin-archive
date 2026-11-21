# douyin-archive

抖音素材下载 + 抽帧判定 + 归档 + 逐字稿，一套跑完。给 Codex / Claude Code 用的本地技能。

## 它解决什么问题

抖音素材长期堆积时，真正的成本不在下载，而在：这条是机器人还是普通内容？该放机器人库还是当月文件夹？访谈要不要顺手出逐字稿？这个技能把这四步固定成一条流水线。

## 目录规则

| 内容 | 落点 |
|---|---|
| 画面出现机器人（任一帧/任一图） | `E:\机器人工作视频` |
| 美女 / 二次元 / AI 动画 / 原创动画 / 穿搭 | `H:\Videos\视频\YYYY-MM` 根目录 |
| 访谈、播客、人物对谈 | `H:\Videos\视频\YYYY-MM\其他\访谈` |
| 其余 | `H:\Videos\视频\YYYY-MM\其他` |

路径写在 `scripts/archive_move.py` 顶部，换机器时改这三行即可。

## 快速开始

```bash
# 1. 下载（支持分享短链 / /video/{id} / 纯 id，可传多条）
python scripts/douyin_fetch.py "https://v.douyin.com/xxxx/" --out "H:/tmp/dl_20261121"

# 2. 抽帧 + CLIP 判定
python scripts/classify_frames.py "H:/tmp/dl_20261121/某条.mp4" --frames 3

# 3. 归档
python scripts/archive_move.py --src "H:/tmp/dl_20261121" --month 2026-11 --default root --dry-run

# 4. 访谈类出逐字稿
python scripts/asr_batch.py "H:/Videos/视频/2026-11/其他/访谈" --lang zh
```

## 依赖

- Python 3.13
- `playwright`（用系统 Edge，无需单独装 Chromium）、`requests`
- `transformers` + `torch`（CLIP 模型需提前缓存；运行时设 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`）
- `faster-whisper`（GPU 可选，CPU 用 int8）
- `ffmpeg` / `ffprobe`
- 抖音下载工具目录（脚本复用了它的 `sanitize / extract_urls / save_note`），路径在 `douyin_fetch.py` 顶部

## 已知的坑（都写进 SKILL.md 了）

- 上次崩溃残留的 msedge 会占住 `_browser_profile`，必然 `exitCode=21` —— 脚本启动时会先清一遍
- 短链直接开页面经常抓不到 detail 接口，必须先跟 302 换成 `/video/{id}`
- 0 字节且无扩展名的文件，其实是图文笔记
- `sanitize` 截断到 120 字符会把 aweme id 切掉，不能靠“文件名含 id”去重
- 同一 profile 不能并行跑两个浏览器实例
- 长视频开头常是真人，抽帧要覆盖到 85%

## License

自用工具，未附许可证。
