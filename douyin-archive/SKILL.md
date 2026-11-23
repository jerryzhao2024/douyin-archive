---
name: douyin-archive
description: >
  抖音素材下载与归档：给一条或一批分享链接/账号主页，下载无水印视频或图文笔记，抽帧判定后按规则归到「机器人库 / 当月根目录 / 其他 / 访谈」，需要时批量生成逐字稿。
  触发词：下载抖音、抖音归档、把这条存下来、整号下载、抖音转逐字稿、机器人素材归档、抖音视频下载。
metadata:
  short-description: 抖音下载 + 判定 + 归档 + 逐字稿
---

# 抖音素材下载与归档

四件事按需组合：**下载 → 判定 → 归档 → 转写**。所有产物落在本机固定目录，方便长期检索。

## 目录约定（硬规则）

| 内容 | 落点 |
|---|---|
| 画面出现机器人（任一帧/任一图） | `E:\机器人工作视频` |
| 出海 / 外贸 / 跨境 / 独立站 / 开发信 | `E:\出海` |
| AI 工具 / Agent / 大模型 / AI 内容生产 | `E:\AI` |
| 美女 / 二次元 / 原创动画 / 穿搭 | `H:\Videos\视频\YYYY-MM` 根目录 |
| 访谈、播客、人物对谈 | `H:\Videos\视频\YYYY-MM\其他\访谈` |
| 其余（商业、知识、军事、普通图文） | `H:\Videos\视频\YYYY-MM\其他` |

`YYYY-MM` 用当月，例如 `2026-11`。

## 前置条件

- Python 3.13：`C:\Users\John\AppData\Local\Programs\Python\Python313\python.exe`（已装 playwright / requests / faster-whisper / transformers）
- 抖音下载工具：`E:\Documents\公众号自动化内容\工具\douyin-downloader-main`（本技能复用其 `sanitize / extract_urls / save_note / PROFILE`）
- ffmpeg：`C:\Users\John\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_...\ffmpeg-8.1.2-full_build\bin`
- CLIP 模型已缓存，**必须**设 `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`，否则会卡在 HuggingFace 超时

## 一、下载

```powershell
python C:\Users\John\.codex\skills\douyin-archive\scripts\douyin_fetch.py `
  "https://v.douyin.com/xxxx/" "7701234567890123456" `
  --out "H:\tmp\dl_YYYYMMDD"
```

- 支持分享短链、`/video/{id}`、纯 id
- 自动识别图文笔记（存成文件夹：`note.md` + `01.jpg…` + `music.mp3`）
- 命名规则：`{作者}_{标题前50字}_{aweme_id}.mp4`

### 整号下载

先用 Playwright 打开主页，拦截 `/aweme/v1/web/aweme/post/` 收集全部 `aweme_id`（滚轮要作用在滚动容器上，`window.scrollTo` 无效），再把 id 列表喂给 `douyin_fetch.py`。整号参考：134 条约 25–40 分钟。

## 二、判定

```powershell
python ...\classify_frames.py "H:\tmp\dl_xxx\a.mp4" "H:\tmp\dl_xxx\某图文文件夹"
```

- 视频抽 10% / 45% / 85% 三帧；图文取前几张
- 输出每帧 top3 标签 + `robot` 分数，并给 `ROBOT / OTHER` 结论（阈值 0.6）
- **单图**若分数分散（如动漫 0.57 / 截图 0.23），改用 Grounding DINO 看检测框位置与面积：主体框大且居中才算主体，边缘小框是背景
- 长视频开头常是真人，机器人只在后段：抽帧要覆盖到 85%，否则会漏判

## 三、归档

```powershell
python ...\archive_move.py --src "H:\tmp\dl_xxx" --month 2026-11 [--default root] [--dry-run]
```

按文件名关键词先粗分（机器人 / 访谈 / 其他），确认无误后去掉 `--dry-run` 执行。判定拿不准的，把 `classify_frames.py` 判为 ROBOT 的文件名用 `--robot-verdict "a.mp4,b.mp4"` 补进去。

## 四、逐字稿（访谈/长视频）

```powershell
python ...\asr_batch.py "H:\Videos\视频\2026-11\其他\访谈" --lang zh
```

- 输出到该目录下 `逐字稿\{同名}.md` + `.srt`，已存在则跳过
- 英文内容用 `--lang en`；不确定用 `--lang auto`
- GPU 可用时自动用 CUDA float16（约 20–30 倍速）

## 常见错误

| 现象 | 原因 | 处理 |
|---|---|---|
| `TargetClosedError` / `exitCode=21` | 上次异常退出留下 msedge 占着 `_browser_profile` | 先按命令行匹配杀掉 `douyin-downloader-main` 的 msedge，再重试 |
| 下载出 0 字节且无扩展名 | 其实是图文笔记，工具先落了视频占位 | 单独重跑该链接，会正确存成文件夹 |
| 短链直接打开抓不到 detail 接口 | 跳转过程中接口没触发 | 先用 requests 跟 302 拿到 `/video/{id}`，再开详情页 |
| 文件名里找不到 aweme id | `sanitize` 截断到 120 字符把 id 切掉了 | 去重不能靠“文件名含 id”，要按标题前缀或先算期望文件名 |
| 两个浏览器实例并行崩 | 同一 profile 只能一个实例 | 复制一份 `_browser_profile` 给第二个进程，或改成串行 |
| CDN 卡住不动 | 个别节点挂死，urllib 默认 90s 超时 | 用 `requests` + `timeout=(6,20)`，并对 `url_list` 逐个 fallback |
| 整号抓不全 | 只滚了 window，没滚容器 | 对 `scrollHeight > clientHeight` 的 div 设 `scrollTop` |

## 成功判据

- 视频：文件 > 100 KB，ffprobe 能读出时长
- 图文：文件夹内有 `note.md` 和至少 1 张 jpg
- 归档：目标目录里能看到文件，源目录清空
- 逐字稿：`逐字稿\*.md` 非空且条数与视频数一致

## 不做的事

- 不破解付费/权限内容；需要登录的站点（如一堂回放）先确认本机浏览器已登录
- 不下载成人内容
