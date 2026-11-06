"""
demo_keypoints.py —— 关键点可视化（第 2 步用这个）

用法：
    python demo_keypoints.py --input samples/me_squat.png --output output/me_keypoints.png
    python demo_keypoints.py --input samples/me_squat_5.mp4 --output output/me_keypoints.mp4
    python demo_keypoints.py --camera --output output/camera.mp4

前两种分别处理图片和视频，--camera 打开摄像头（按 q 退出）。
"""

import os
import argparse

import cv2
import numpy as np
import mediapipe as mp

import pose_core as pc

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def run_image(src, dst):
    bgr = pc.safe_imread(src)
    if bgr is None:
        raise FileNotFoundError("读不到图片：" + src)

    landmarker = pc.build_landmarker("image")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_image)

    if not result.pose_landmarks:
        print("[警告] 没检测到人体。请确认：全身入镜 / 光线充足 / 背景不杂乱。")
        return None

    pts = pc.to_pixels(result.pose_landmarks[0], bgr.shape[1], bgr.shape[0])
    pc.draw_skeleton(bgr, pts)
    pc.safe_imwrite(dst, bgr)

    m = pc.frame_metrics(pts)
    print("[OK] 检测到 %d 个关键点" % len(result.pose_landmarks[0]))
    print("[OK] 膝角 %.1f 度 / 髋角 %.1f 度 / 躯干前倾 %.1f 度"
          % (m["knee"], m["hip"], m["lean"]))
    print("[OK] 已输出：" + dst)
    return pts


def run_video(src, dst):
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise FileNotFoundError(
            "打不开视频：" + src + "\n"
            "常见原因：文件不存在 / 编码是 HEVC / 路径含中文。"
        )

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    writer = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    landmarker = pc.build_landmarker("video")
    idx, hit = 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_image, int(idx * 1000 / fps))

        if result.pose_landmarks:
            hit += 1
            pts = pc.to_pixels(result.pose_landmarks[0], w, h)
            pc.draw_skeleton(frame, pts)
            pc.draw_hud(frame, pc.frame_metrics(pts), hit, "tracking")

        writer.write(frame)

    cap.release()
    writer.release()
    print("[OK] 共 %d 帧，检测到人体 %d 帧（%.1f%%）" % (idx, hit, hit / max(idx, 1) * 100))
    print("[OK] 已输出：" + dst)


def run_camera(dst):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("打不开摄像头，检查是否被其他程序占用。")

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 25
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    writer = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    landmarker = pc.build_landmarker("video")
    idx = 0
    print("摄像头已开启，按 q 退出。")
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        idx += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect_for_video(mp_image, int(idx * 1000 / fps))
        if result.pose_landmarks:
            pts = pc.to_pixels(result.pose_landmarks[0], w, h)
            pc.draw_skeleton(frame, pts)
        writer.write(frame)
        cv2.imshow("squat-coach (press q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()
    print("[OK] 录像已保存：" + dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="输入图片或视频路径")
    ap.add_argument("--output", default="output/keypoints.png", help="输出路径")
    ap.add_argument("--camera", action="store_true", help="使用摄像头")
    args = ap.parse_args()

    if args.camera:
        run_camera(args.output)
        return
    if not args.input:
        ap.error("请用 --input 指定文件，或加 --camera 用摄像头")
    if not os.path.exists(args.input):
        raise FileNotFoundError("文件不存在：" + os.path.abspath(args.input))

    if os.path.splitext(args.input)[1].lower() in IMG_EXT:
        run_image(args.input, args.output)
    else:
        run_video(args.input, args.output)


if __name__ == "__main__":
    main()
