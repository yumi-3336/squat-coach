"""
evaluate.py —— 批量评测：算法计数 vs 人工真值（第 5 步用这个）

用法：
    # 第一次运行：自动生成标注模板 samples/labels.csv
    python evaluate.py --dir samples

    # 打开 labels.csv，把每段视频你人工数出的次数填进 true_count 列
    # 再运行一次，输出评测结果
    python evaluate.py --dir samples --report output/eval_report.csv

输出：
    output/eval_report.csv —— 每段视频的真值 / 算法值 / 误差 / 问题清单
    终端打印：平均绝对误差、完全命中率、偏差最大样本
"""

import os
import csv
import argparse

import squat_counter as sc

VIDEO_EXT = (".mp4", ".avi", ".mov", ".mkv", ".m4v")


def find_videos(folder):
    names = []
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(VIDEO_EXT):
            names.append(name)
    return names


def load_labels(path):
    rows = {}
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("filename") or "").strip()
            if not name:
                continue
            raw = (row.get("true_count") or "").strip()
            rows[name] = int(raw) if raw.isdigit() else None
    return rows


def write_template(path, videos):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["filename", "true_count", "note"])
        for v in videos:
            w.writerow([v, "", ""])
    print("[模板] 已生成：" + path)
    print("       把每段视频你人工数出的次数填进 true_count 列，保存后重新运行本脚本。")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="samples", help="视频所在目录")
    ap.add_argument("--report", default="output/eval_report.csv", help="输出评测表")
    ap.add_argument("--video-out", default="output/annotated", help="标注视频输出目录")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        print("[!] 目录不存在：" + os.path.abspath(args.dir))
        return

    videos = find_videos(args.dir)
    if not videos:
        print("[!] " + args.dir + " 下没有找到视频文件（支持 mp4/avi/mov/mkv）。")
        return

    labels_path = os.path.join(args.dir, "labels.csv")
    labels = load_labels(labels_path)
    if not labels:
        write_template(labels_path, videos)
        return

    os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
    os.makedirs(args.video_out, exist_ok=True)

    rows, errors, skipped = [], [], 0

    for name in videos:
        true_count = labels.get(name)
        if true_count is None:
            skipped += 1
            print("[跳过] " + name + "（未填真值）")
            continue

        print("[分析] " + name + " ...")
        out_video = os.path.join(args.video_out, os.path.splitext(name)[0] + "_annotated.mp4")
        try:
            summary = sc.analyze_video(os.path.join(args.dir, name), out_video)
        except Exception as e:
            print("  [失败] " + str(e))
            continue

        err = summary["count"] - true_count
        errors.append(abs(err))
        avg_min_knee = ""
        if summary["reps"]:
            avg_min_knee = round(sum(r["min_knee"] for r in summary["reps"]) / len(summary["reps"]), 1)

        rows.append({
            "filename": name,
            "true_count": true_count,
            "pred_count": summary["count"],
            "error": err,
            "abs_error": abs(err),
            "pose_rate": "%.1f%%" % (summary["pose_rate"] * 100),
            "min_knee_avg": avg_min_knee,
            "issues": " / ".join(summary["issues"]),
        })

    if not rows:
        print("[!] 没有可评测的样本。")
        return

    with open(args.report, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    mae = sum(errors) / len(errors)
    perfect = sum(1 for e in errors if e == 0) / len(errors)

    print()
    print("=" * 60)
    print("样本数        : %d（跳过 %d 段未填真值）" % (len(rows), skipped))
    print("平均绝对误差  : %.2f 次/组" % mae)
    print("完全命中率    : %.1f%%" % (perfect * 100))
    worst = max(rows, key=lambda r: r["abs_error"])
    print("偏差最大样本  : %s（真值 %s，算法 %s）"
          % (worst["filename"], worst["true_count"], worst["pred_count"]))
    print("评测表        : " + args.report)
    print("=" * 60)
    print()
    print("把上面四个数字写进报告，并准备好回答评委两个追问：")
    print("  1) 误差最大的那几段，失败原因是什么？（遮挡 / 侧身角度 / 抖动 / 半身出镜）")
    print("  2) 深度阈值从 100 度调到 110 度，命中率会变成多少？（参数敏感性分析是加分项）")


if __name__ == "__main__":
    main()
