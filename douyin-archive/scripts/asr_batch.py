import os, re, subprocess, sys, glob, io, time
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", write_through=True)

SITE = Path(r"C:\Users\John\AppData\Local\Programs\Python\Python313\Lib\site-packages")
extra = [str(SITE / p) for p in [r"nvidia\cublas\bin", r"nvidia\cudnn\bin", r"nvidia\cuda_nvrtc\bin"] if (SITE / p).exists()]
if extra:
    os.environ["PATH"] = ";".join(extra) + ";" + os.environ.get("PATH", "")

FF = r"C:\Users\John\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
FP = r"C:\Users\John\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffprobe.exe"


def ts(sec):
    ms = int(round(sec * 1000))
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    import argparse
    ap = argparse.ArgumentParser(description="目录内视频批量转写（faster-whisper）")
    ap.add_argument("src", help="视频目录")
    ap.add_argument("--lang", default="zh", help="zh / en / auto")
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    a = ap.parse_args()
    SRC = Path(a.src)
    OUT = SRC / "逐字稿"
    TMP = Path(os.environ.get("TEMP", r"H:\tmp")) / "asr_tmp"
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)

    from faster_whisper import WhisperModel
    import ctranslate2
    dev = a.device
    if dev == "auto":
        dev = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
    ct = "float16" if dev == "cuda" else "int8"
    model = WhisperModel(a.model, device=dev, compute_type=ct)
    print(f"model ready ({dev}/{ct})", flush=True)

    vids = sorted([p for p in SRC.iterdir() if p.is_file() and p.suffix.lower() in (".mp4", ".mov", ".mkv")])
    for v in vids:
        md = OUT / (v.stem + ".md")
        if md.exists() and md.stat().st_size > 500:
            print("skip", v.stem[:44], flush=True)
            continue
        dur = float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(v)], capture_output=True, text=True).stdout or 0)
        wav = TMP / (v.stem[:50] + ".wav")
        if not wav.exists():
            subprocess.run([FF, "-v", "error", "-i", str(v), "-ac", "1", "-ar", "16000", "-vn", str(wav), "-y"], capture_output=True)
        lang = None if a.lang == "auto" else a.lang
        segs = []
        it, info = model.transcribe(str(wav), language=lang, vad_filter=True)
        for s in it:
            t = s.text.strip()
            if t:
                segs.append((s.start, s.end, t))
        body = "\n".join(t for _, _, t in segs)
        head = [f"# {v.stem}", "", f"- 时长：{int(dur//60)}分{int(dur%60)}秒",
                f"- 转写：faster-whisper {a.model}（{dev}/{ct}）", "- 说明：本地 ASR，可能有错别字", "", "## 逐字稿", ""]
        md.write_text("\n".join(head) + body, encoding="utf-8")
        (OUT / (v.stem + ".srt")).write_text(
            "\n".join(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n" for i, (s, e, t) in enumerate(segs, 1)), encoding="utf-8")
        print(f"DONE {v.stem[:40]} | {dur/60:.1f}min | chars={len(body)}", flush=True)
        try:
            wav.unlink()
        except OSError:
            pass


if __name__ == "__main__":
    main()
