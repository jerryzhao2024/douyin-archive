import argparse, json, os, shutil, sys

ROBOT_DIR = r"E:\机器人工作视频"
VIDEO_ROOT = r"H:\Videos\视频"

ROBOT_KEYS = ["机器人", "机械臂", "robot", "Robot", "ROBOT", "产线", "焊装", "点焊", "弧焊",
              "上下料", "码垛", "AGV", "PLC", "自动化线", "涂胶", "夹具", "示教器", "伺服",
              "发那科", "库卡", "安川", "那智", "ABB", "FANUC", "KUKA", "Yaskawa",
              "管线包", "FULLLINK", "釜菱", "冲压", "热锻", "主机厂", "焊装车间", "机器人调试",
              "机器人工程师", "机器人维修", "减速机", "工博会"]

INTERVIEW_KEYS = ["访谈", "对谈", "播客", "采访", "对话", "聊聊"]


def main():
    ap = argparse.ArgumentParser(description="按规则把下载好的素材移动到归档目录")
    ap.add_argument("--src", required=True)
    ap.add_argument("--month", required=True, help="YYYY-MM，例如 2026-11")
    ap.add_argument("--default", choices=["other", "root"], default="other",
                    help="非机器人内容的落点：other=其他/，root=当月根目录")
    ap.add_argument("--robot-verdict", default="", help="classify_frames.py 判为 ROBOT 的文件名列表（逗号分隔）")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    robot_extra = {x.strip() for x in a.robot_verdict.split(",") if x.strip()}
    month_dir = os.path.join(VIDEO_ROOT, a.month)
    other_dir = os.path.join(month_dir, "其他")
    interview_dir = os.path.join(other_dir, "访谈")
    for d in (month_dir, other_dir, interview_dir, ROBOT_DIR):
        os.makedirs(d, exist_ok=True)

    moved = []
    for name in sorted(os.listdir(a.src)):
        p = os.path.join(a.src, name)
        base = os.path.splitext(name)[0]
        is_robot = any(k in name for k in ROBOT_KEYS) or any(x and x in name for x in robot_extra)
        if is_robot:
            dest_dir = ROBOT_DIR
        elif any(k in name for k in INTERVIEW_KEYS):
            dest_dir = interview_dir
        else:
            dest_dir = month_dir if a.default == "root" else other_dir
        dst = os.path.join(dest_dir, name)
        if os.path.exists(dst):
            print(f"SKIP  {name[:60]}（目标已存在）")
            continue
        print(f"{'DRY ' if a.dry_run else 'MOVE'} {('ROBOT' if is_robot else 'OTHER'):5s} -> {name[:60]}")
        if not a.dry_run:
            shutil.move(p, dst)
        moved.append({"name": name, "dest": dst, "robot": is_robot})
    print(json.dumps({"moved": len(moved)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
