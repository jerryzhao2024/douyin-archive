import os, sys, json, glob, subprocess
sys.stdout.reconfigure(encoding="utf-8")
FF = r"C:\Users\John\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe"
FP = r"C:\Users\John\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffprobe.exe"

LABELS = [
    "an industrial robot arm in a factory", "industrial machinery or machine tools",
    "a portrait photo of a young woman", "a woman posing or dancing in a video",
    "an anime or cartoon character", "a screenshot of chat or text",
    "a military vehicle or weapon", "a car or vehicle",
    "a pure landscape or scenery with no people", "a man talking to the camera",
    "a flower or nature scenery",
]


def frames_of(path, n=3):
    if os.path.isdir(path):
        return sorted(glob.glob(os.path.join(path, "*.jpg")))[: n + 3]
    dur = float(subprocess.run([FP, "-v", "error", "-show_entries", "format=duration",
                                "-of", "default=nw=1:nk=1", path], capture_output=True, text=True).stdout or 0)
    out = []
    tmp = os.path.join(os.environ.get("TEMP", r"H:\tmp"), "cls_frames")
    os.makedirs(tmp, exist_ok=True)
    for i, pct in enumerate([0.1, 0.45, 0.85][:n]):
        f = os.path.join(tmp, f"f{i}.jpg")
        subprocess.run([FF, "-v", "error", "-ss", str(dur * pct), "-i", path, "-frames:v", "1",
                        "-q:v", "2", f, "-y"], capture_output=True)
        if os.path.exists(f):
            out.append(f)
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser(description="抽帧 + CLIP 判定（离线）")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--frames", type=int, default=3)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import torch
    from PIL import Image
    from transformers import CLIPProcessor, CLIPModel
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    report = []
    for p in a.paths:
        item = {"path": p, "frames": []}
        for f in frames_of(p, a.frames):
            im = Image.open(f).convert("RGB")
            inp = proc(text=LABELS, images=im, return_tensors="pt", padding=True)
            with torch.no_grad():
                lg = model(**inp).logits_per_image.softmax(dim=1)[0]
            top = sorted(zip(LABELS, lg.tolist()), key=lambda x: -x[1])[:3]
            robot = float(lg[0])
            item["frames"].append({"frame": os.path.basename(f), "robot": round(robot, 3),
                                   "top": [{"label": l, "score": round(s, 3)} for l, s in top]})
        scores = [x["robot"] for x in item["frames"]]
        item["robot_max"] = max(scores) if scores else 0
        item["verdict"] = "ROBOT" if item["robot_max"] >= 0.6 else "OTHER"
        report.append(item)
        print(f"{item['verdict']:5s} robot_max={item['robot_max']:.3f}  {os.path.basename(p)[:60]}")
        for fr in item["frames"]:
            print("    ", fr["frame"], f"robot={fr['robot']:.3f}", "|", ", ".join(f"{t['label'][:24]}={t['score']:.2f}" for t in fr["top"]))
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
