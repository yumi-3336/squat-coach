"""
selftest.py —— 环境自检（每次换电脑、换路径、重装依赖后先跑这个）

用法：
    python selftest.py

全部通过会打印「自检通过」，任何一项失败都会告诉你卡在哪一步、怎么修。
"""

import os
import sys
import math
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
OK, FAIL = "[PASS]", "[FAIL]"
results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((True, name, detail or ""))
        print(OK, name, detail or "")
    except Exception as e:
        results.append((False, name, str(e)))
        print(FAIL, name, "->", e)


def t_path_ascii():
    if not BASE.isascii():
        raise RuntimeError("项目路径含非英文字符：" + BASE + "，请先把文件夹改成纯英文名")
    return BASE


def t_versions():
    import mediapipe
    import cv2
    import numpy
    return "Python %d.%d.%d / mediapipe %s / opencv %s / numpy %s" % (
        sys.version_info[0], sys.version_info[1], sys.version_info[2],
        mediapipe.__version__, cv2.__version__, numpy.__version__)


def t_model():
    import pose_core as pc
    if not os.path.exists(pc.MODEL_PATH):
        raise RuntimeError("模型缺失：" + pc.MODEL_PATH + "（需先下载 pose_landmarker_lite.task 到 models 目录）")
    size = os.path.getsize(pc.MODEL_PATH) / 1024 / 1024
    if size < 1:
        raise RuntimeError("模型文件过小（%.2f MB），可能下载不完整，请重新下载" % size)
    return "%.1f MB" % size


def t_load_model():
    import pose_core as pc
    lm = pc.build_landmarker("image")
    return "模型加载成功，DLL 正常"


def t_angle_math():
    import pose_core as pc
    # 直角：髋(0,0) 膝(0,100) 踝(100,100) -> 膝角应为 90 度
    a = pc.angle_at((0, 0), (0, 100), (100, 100))
    if abs(a - 90) > 0.5:
        raise RuntimeError("角度计算错误，期望 90，实际 %.2f" % a)
    # 直腿：髋(0,0) 膝(0,100) 踝(0,200) -> 180 度
    b = pc.angle_at((0, 0), (0, 100), (0, 200))
    if abs(b - 180) > 0.5:
        raise RuntimeError("角度计算错误，期望 180，实际 %.2f" % b)
    return "直角=%.0f 直腿=%.0f" % (a, b)


def t_counter_logic():
    import pose_core as pc
    c = pc.SquatCounter()
    fps = 30
    for i in range(fps * 6):
        t = i / fps
        knee = 175 - 85 * (0.5 - 0.5 * math.cos(2 * math.pi * t / 2.0))
        c.update({"knee": knee, "hip": 90.0, "lean": 20.0,
                  "knee_l": knee, "knee_r": knee, "lr_diff": 0.0}, t)
    if c.count != 3:
        raise RuntimeError("状态机计数错误，模拟 3 次实际数到 %d 次" % c.count)
    return "模拟 3 次深蹲 -> 计数 %d 次" % c.count


def t_video_io():
    import cv2
    import numpy as np
    import squat_counter as sc

    tmp_dir = os.path.join(BASE, "output")
    os.makedirs(tmp_dir, exist_ok=True)
    src = os.path.join(tmp_dir, "_selftest_in.mp4")
    dst = os.path.join(tmp_dir, "_selftest_out.mp4")

    writer = cv2.VideoWriter(src, cv2.VideoWriter_fourcc(*"mp4v"), 15, (320, 320))
    frame = np.full((320, 320, 3), 200, dtype=np.uint8)
    for _ in range(15):
        writer.write(frame)
    writer.release()

    summary = sc.analyze_video(src, dst)
    if not os.path.exists(dst):
        raise RuntimeError("标注视频没有生成，写入可能失败")
    for p in (src, dst):
        if os.path.exists(p):
            os.remove(p)
    return "%d 帧读写正常（无真人画面，计数为 %d 属正常）" % (summary["frames"], summary["count"])


def main():
    print("=" * 60)
    print("squat-coach 环境自检")
    print("=" * 60)

    check("路径为纯英文", t_path_ascii)
    check("依赖版本", t_versions)
    check("模型文件存在", t_model)
    check("模型可加载", t_load_model)
    check("角度计算正确", t_angle_math)
    check("计数状态机正确", t_counter_logic)
    check("视频读写正常", t_video_io)

    print("=" * 60)
    failed = [r for r in results if not r[0]]
    if failed:
        print("自检未通过，共 %d 项失败。按上面提示逐条修复。" % len(failed))
        sys.exit(1)
    print("自检通过。环境没问题，可以进入下一步。")


if __name__ == "__main__":
    main()
