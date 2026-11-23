import argparse, json, os, shutil

ROBOT_DIR = r"E:\机器人工作视频"
SEA_DIR = r"E:\出海"
AI_DIR = r"E:\AI"
VIDEO_ROOT = r"H:\Videos\视频"

ROBOT_KEYS = ["机器人", "机械臂", "robot", "Robot", "ROBOT", "产线", "焊装", "点焊", "弧焊",
              "上下料", "码垛", "AGV", "PLC", "自动化线", "涂胶", "夹具", "示教器", "伺服",
              "发那科", "库卡", "安川", "那智", "ABB", "FANUC", "KUKA", "Yaskawa",
              "管线包", "FULLLINK", "釜菱", "冲压", "热锻", "主机厂", "焊装车间", "机器人调试",
              "机器人工程师", "机器人维修", "减速机", "工博会"]

SEA_KEYS = ["外贸", "出海", "跨境", "独立站", "海外仓", "亚马逊", "Shopify", "TikTok",
            "跨境电商", "询盘", "开发信", "领英", "LinkedIn"]

AI_KEYS = ["AI剪辑", "AI剪", "Agent", "智能体", "大模型", "AI工作台", "codex", "Codex",
           "提示词", "AI工具", "AI提效", "BOSS", "ChatGPT", "Claude", "DeepSeek", "开源模型"]

INTERVIEW_KEYS = ["访谈", "对谈", "播客", "采访", "对话", "聊聊"]


def main():
    ap = argparse.ArgumentParser(description="按规则把下载好的素材移动到归档目录")
    ap.add_argument("--src", required=True)
    ap.add_argument("--month", required=True, help="YYYY-MM，例如 2026-11")
    ap.add_argument("--default", choices=["other", "root"], default="other",
                    help="无法归类的内容：other=其他/，root=当月根目录")
    ap.add_argument("--robot-verdict", default="", help="classify_frames.py 判为 ROBOT 的文件名列表（逗号分隔）")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    robot_extra = {x.strip() for x in a.robot_verdict.split(",") if x.strip()}
    month_dir = os.path.join(VIDEO_ROOT, a.month)
    other_dir = os.path.join(month_dir, "其他")
    interview_dir = os.path.join(other_dir, "访谈")
    for d in (month_dir, other_dir, interview_dir, ROBOT_DIR, SEA_DIR, AI_DIR):
        os.makedirs(d, exist_ok=True)

    moved = []
    for name in sorted(os.listdir(a.src)):
        p = os.path.join(a.src, name)
        if not (os.path.isfile(p) or os.path.isdir(p)):
            continue
        if any(k in name for k in ROBOT_KEYS) or any(x and x in name for x in robot_extra):
            dest_dir, tag = ROBOT_DIR, "ROBOT"
        elif any(k in name for k in SEA_KEYS):
            dest_dir, tag = SEA_DIR, "SEA"
        elif any(k in name for k in AI_KEYS):
            dest_dir, tag = AI_DIR, "AI"
        elif any(k in name for k in INTERVIEW_KEYS):
            dest_dir, tag = interview_dir, "INTERVIEW"
        else:
            dest_dir, tag = (month_dir if a.default == "root" else other_dir), "OTHER"
        dst = os.path.join(dest_dir, name)
        if os.path.exists(dst):
            print(f"SKIP  {name[:60]}（目标已存在）")
            continue
        print(f"{'DRY ' if a.dry_run else 'MOVE'} {tag:9s} -> {name[:60]}")
        if not a.dry_run:
            shutil.move(p, dst)
        moved.append({"name": name, "dest": dst, "tag": tag})
    print(json.dumps({"moved": len(moved)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
