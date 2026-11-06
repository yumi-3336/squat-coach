"""
squat_counter.py —— 深蹲计数与动作合规判定（第 3 步用这个）

用法：
    python squat_counter.py --input samples/me_squat_5.mp4 --output output/me_result.mp4 --json output/me_result.json

输出：
    1. 带骨架、角度、计数、告警的标注视频
    2. 一份 JSON：每次动作的最小膝角、用时、左右对称差 + 问题清单
"""

import os
import json
import argparse

import cv2
import mediapipe as mp

import pose_core as pc


def analyze_video(src, dst_video, dst_json=None):
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise FileNotFoundError(
            "打不开视频：" + src + "\n"
            "常见原因：文件不存在 / 编码是 HEVC / 路径含中文。"
        )

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    os.makedirs(os.path.dirname(dst_video) or ".", exist_ok=True)
    writer = cv2.VideoWriter(dst_video, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    landmarker = pc.build_landmarker("video")
    counter = pc.SquatCounter()

    idx, hit = 0, 0
    issues_live = []

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1
        t = idx / fps

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_image, int(idx * 1000 / fps))

        if result.pose_landmarks:
            hit += 1
            pts = pc.to_pixels(result.pose_landmarks[0], w, h)
            m = pc.frame_metrics(pts)
            if counter.update(m, t):
                issues_live = counter.judge()
            pc.draw_skeleton(frame, pts)
            pc.draw_hud(frame, m, counter.count, counter.state, issues_live)
        else:
            pc.draw_hud(frame, None, counter.count, "no-pose")

        writer.write(frame)

    cap.release()
    writer.release()

    summary = {
        "file": os.path.basename(src),
        "fps": fps,
        "frames": idx,
        "pose_frames": hit,
        "pose_rate": round(hit / max(idx, 1), 4),
        "count": counter.count,
        "reps": counter.reps,
        "issues": counter.judge(),
    }

    print("=" * 56)
    print("文件      : " + summary["file"])
    print("帧数      : %d（检测到人体 %d 帧，%.1f%%）" % (idx, hit, summary["pose_rate"] * 100))
    print("深蹲次数  : %d" % summary["count"])
    if summary["issues"]:
        print("问题提示  :")
        for it in summary["issues"]:
            print("  - " + it)
    else:
        print("问题提示  : 未发现明显问题（或本次动作数为 0）")
    print("=" * 56)
    print("标注视频  : " + dst_video)

    if dst_json:
        os.makedirs(os.path.dirname(dst_json) or ".", exist_ok=True)
        with open(dst_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print("结果 JSON : " + dst_json)

    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="输入视频路径")
    ap.add_argument("--output", default="output/squat_result.mp4", help="输出标注视频")
    ap.add_argument("--json", default=None, help="输出 JSON 结果（可选）")
    args = ap.parse_args()

    analyze_video(args.input, args.output, args.json)


if __name__ == "__main__":
    main()
