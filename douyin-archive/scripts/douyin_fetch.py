import asyncio, json, os, re, sys, time
import requests
from pathlib import Path

TOOL = Path(r"E:\Documents\公众号自动化内容\工具\douyin-downloader-main")
sys.path.insert(0, str(TOOL))
import douyin_batch as B

UA_I = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"


def resolve(target: str) -> str:
    """短链/ID -> aweme id"""
    t = target.strip()
    if re.fullmatch(r"\d{15,25}", t):
        return t
    m = re.search(r"/video/(\d{15,25})", t)
    if m:
        return m.group(1)
    r = requests.get(t, headers={"User-Agent": UA_I}, allow_redirects=True, timeout=25)
    m = re.search(r"/video/(\d{15,25})", r.url)
    if m:
        return m.group(1)
    m = re.search(r"slides/(\d{15,25})", r.url)
    if m:
        return m.group(1)
    raise SystemExit(f"无法解析出视频 ID：{target}")


def kill_stale_edge() -> None:
    import subprocess
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | "
          "Where-Object { $_.CommandLine -like '*douyin-downloader-main*' } | "
          "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True)


def dl(url, path, ck):
    h = {"User-Agent": B.UA, "Referer": "https://www.douyin.com/", "Accept": "*/*", "Cookie": ck}
    tmp = path + ".part"
    try:
        with requests.get(url, headers=h, stream=True, timeout=(6, 20)) as r:
            r.raise_for_status()
            n = 0
            with open(tmp, "wb") as f:
                for ch in r.iter_content(262144):
                    if ch:
                        f.write(ch)
                        n += len(ch)
        if n < 100 * 1024:
            os.remove(tmp)
            return False
        os.replace(tmp, path)
        return True
    except Exception:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        return False


async def run(out_dir: str, ids: list[str]) -> list[dict]:
    from playwright.async_api import async_playwright
    os.makedirs(out_dir, exist_ok=True)
    res = []
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(B.PROFILE), channel="msedge", headless=True,
            user_agent=B.UA, locale="zh-CN", viewport={"width": 1280, "height": 860})
        ck = "; ".join(f"{c['name']}={c['value']}" for c in await ctx.cookies()
                        if any(k in (c.get("domain") or "") for k in ["douyin", "bytedance", "snssdk"]))
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        holder = {"text": None}

        async def handler(resp):
            if "/aweme/v1/web/aweme/detail/" in resp.url and resp.status == 200:
                try:
                    t = await resp.text()
                    if 1000 < len(t) < 5_000_000:
                        holder["text"] = t
                except Exception:
                    pass

        page.on("response", handler)
        for aid in ids:
            holder["text"] = None
            try:
                await page.goto(f"https://www.douyin.com/video/{aid}", wait_until="commit", timeout=30000)
            except Exception:
                pass
            for _ in range(80):
                if holder["text"]:
                    break
                await asyncio.sleep(0.25)
            txt = holder["text"]
            if not txt:
                res.append({"id": aid, "ok": False, "reason": "no detail api"})
                print(f"FAIL {aid} (no detail api)", flush=True)
                continue
            aw = json.loads(txt).get("aweme_detail") or {}
            author = (aw.get("author") or {}).get("nickname") or "unknown"
            desc = aw.get("desc") or "video"
            name = B.sanitize(f"{author}_{desc[:50]}_{aid}")
            if aw.get("images"):
                B.save_note(Path(out_dir) / name, author, desc, aid, aw, ck)
                res.append({"id": aid, "ok": True, "type": "note", "path": os.path.join(out_dir, name)})
                print(f"NOTE {name[:60]}", flush=True)
                continue
            ok = False
            for u in B.extract_urls(txt)[:5]:
                if await asyncio.to_thread(dl, u, os.path.join(out_dir, name + ".mp4"), ck):
                    ok = True
                    break
            res.append({"id": aid, "ok": ok, "type": "video", "path": os.path.join(out_dir, name + ".mp4")})
            print(("OK   " if ok else "FAIL ") + name[:60], flush=True)
        await ctx.close()
    return res


def main():
    import argparse
    ap = argparse.ArgumentParser(description="抖音单条/批量下载（视频或图文）")
    ap.add_argument("targets", nargs="+", help="分享短链或 aweme id")
    ap.add_argument("--out", required=True, help="输出目录")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    kill_stale_edge()
    time.sleep(2)
    ids = [resolve(t) for t in a.targets]
    res = asyncio.run(run(a.out, ids))
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
