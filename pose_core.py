"""
pose_core.py —— 共用模块：读图、估姿态、算角度、判定深蹲

被 demo_keypoints.py / squat_counter.py / evaluate.py 共同调用。
所有可调阈值都集中在 RULES 字典里，改这一个地方就够。

重要：项目所在路径必须是纯英文（例如 D:\\Work\\squat-coach）。
      Windows 下 OpenCV 和 mediapipe 对中文路径支持很差。
"""

import os

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "pose_landmarker_lite.task")

# ---- 关键点编号（MediaPipe Pose 33 点定义） ----
L_SHOULDER, R_SHOULDER = 11, 12
L_HIP, R_HIP = 23, 24
L_KNEE, R_KNEE = 25, 26
L_ANKLE, R_ANKLE = 27, 28
L_HEEL, R_HEEL = 29, 30
L_TOE, R_TOE = 31, 32

POSE_EDGES = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24),
    (23, 25), (25, 27), (24, 26), (26, 28),
    (27, 29), (29, 31), (28, 30), (30, 32),
]

# ---- 判定阈值：本项目的「规则库」，可自行调整 ----
RULES = {
    "knee_angle_down": 110.0,     # 膝角小于它 = 已蹲下（开始计数）
    "knee_angle_up": 160.0,       # 膝角大于它 = 已站直（完成计数）
    "min_depth": 100.0,           # 一次动作的最小膝角 <= 它才算够深
    "max_trunk_lean": 45.0,       # 躯干与竖直方向最大夹角（度）
    "max_knee_forward": 0.18,     # 膝盖超出脚踝的水平距离 / 身高 上限
    "min_rep_seconds": 0.8,       # 单次动作最短用时（秒）
    "max_lr_diff": 15.0,          # 左右膝角最大差值（度）
}


# ---------- 中文路径兼容（仅图片，视频路径必须纯英文） ----------

def safe_imread(path):
    """cv2.imread 遇到中文路径会静默返回 None，这里绕开。"""
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def safe_imwrite(path, img):
    ext = os.path.splitext(path)[1] or ".png"
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise RuntimeError("图片编码失败：" + path)
    buf.tofile(path)


# ---------- 姿态估计 ----------

def build_landmarker(mode="video"):
    """创建姿态估计器。mode 取 'image' 或 'video'。"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            "找不到模型文件：" + MODEL_PATH + "\n"
            "请把 pose_landmarker_lite.task 放到 models 目录下。"
        )

    # 传字节流而不是路径，避免任何路径解析问题
    with open(MODEL_PATH, "rb") as f:
        model_bytes = f.read()

    running_mode = (
        vision.RunningMode.VIDEO if mode == "video" else vision.RunningMode.IMAGE
    )
    options = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_buffer=model_bytes),
        running_mode=running_mode,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(options)


# ---------- 几何计算 ----------

def to_pixels(landmarks, w, h):
    """归一化坐标转像素坐标。算角度必须用像素坐标，否则长宽比会扭曲结果。"""
    return np.array([[lm.x * w, lm.y * h] for lm in landmarks], dtype=np.float64)


def angle_at(a, b, c):
    """求关节 b 处的夹角（a、b、c 为三点像素坐标）。"""
    v1 = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    v2 = np.asarray(c, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 < 1e-6 or n2 < 1e-6:
        return float("nan")
    cos = np.clip(np.dot(v1, v2) / (n1 * n2), -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def trunk_lean(shoulder, hip):
    """躯干与竖直方向的夹角（度）。0 表示完全直立。"""
    v = np.asarray(shoulder, dtype=np.float64) - np.asarray(hip, dtype=np.float64)
    n = np.linalg.norm(v)
    if n < 1e-6:
        return float("nan")
    cos = np.clip(v[1] / n * -1.0, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def body_height(pts):
    """用肩到踝的垂直距离近似身高，用于把像素距离归一化。"""
    top = min(pts[L_SHOULDER][1], pts[R_SHOULDER][1])
    bottom = max(pts[L_ANKLE][1], pts[R_ANKLE][1])
    return max(bottom - top, 1.0)


def frame_metrics(pts):
    """从一帧像素坐标算出全部指标。侧视时取膝盖更弯的一侧代表动作幅度。"""
    knee_l = angle_at(pts[L_HIP], pts[L_KNEE], pts[L_ANKLE])
    knee_r = angle_at(pts[R_HIP], pts[R_KNEE], pts[R_ANKLE])
    hip_l = angle_at(pts[L_SHOULDER], pts[L_HIP], pts[L_KNEE])
    hip_r = angle_at(pts[R_SHOULDER], pts[R_HIP], pts[R_KNEE])
    lean_l = trunk_lean(pts[L_SHOULDER], pts[L_HIP])
    lean_r = trunk_lean(pts[R_SHOULDER], pts[R_HIP])

    use_left = np.nan_to_num(knee_l) <= np.nan_to_num(knee_r)

    return {
        "knee": knee_l if use_left else knee_r,
        "hip": hip_l if use_left else hip_r,
        "lean": lean_l if use_left else lean_r,
        "knee_l": knee_l,
        "knee_r": knee_r,
        "lr_diff": abs(np.nan_to_num(knee_l) - np.nan_to_num(knee_r)),
        "pts": pts,
        "use_left": use_left,
    }


# ---------- 深蹲状态机 ----------

class SquatCounter:
    """用膝角做状态机计数。两个阈值形成滞回，避免抖动误计。"""

    def __init__(self, rules=None):
        self.rules = rules or RULES
        self.count = 0
        self.state = "up"
        self.rep_start_t = None
        self.rep_min_knee = 999.0
        self.reps = []

    def update(self, m, t):
        """m 是 frame_metrics 的结果，t 是当前时间（秒）。返回本次是否完成一个动作。"""
        knee = m["knee"]
        if np.isnan(knee):
            return False

        finished = False

        if self.state == "up" and knee < self.rules["knee_angle_down"]:
            self.state = "down"
            self.rep_start_t = t
            self.rep_min_knee = knee

        elif self.state == "down":
            self.rep_min_knee = min(self.rep_min_knee, knee)
            if knee > self.rules["knee_angle_up"]:
                self.state = "up"
                finished = True
                self.count += 1
                dur = (t - self.rep_start_t) if self.rep_start_t is not None else 0.0
                self.reps.append({
                    "idx": self.count,
                    "duration": round(dur, 2),
                    "min_knee": round(self.rep_min_knee, 1),
                    "lean": round(m["lean"], 1) if not np.isnan(m["lean"]) else None,
                    "lr_diff": round(m["lr_diff"], 1),
                })
                self.rep_min_knee = 999.0
                self.rep_start_t = None

        return finished

    def judge(self):
        """对已完成动作做合规判定，返回问题清单。"""
        issues = []
        if not self.reps:
            return issues

        shallow = [r["idx"] for r in self.reps if r["min_knee"] > self.rules["min_depth"]]
        if shallow:
            issues.append("深度不足：第 " + str(shallow) + " 次最小膝角超过 "
                          + str(int(self.rules["min_depth"])) + " 度")

        fast = [r["idx"] for r in self.reps if r["duration"] < self.rules["min_rep_seconds"]]
        if fast:
            issues.append("节奏过快：第 " + str(fast) + " 次用时不足 "
                          + str(self.rules["min_rep_seconds"]) + " 秒")

        leans = [r["lean"] for r in self.reps if r["lean"] is not None]
        if leans and max(leans) > self.rules["max_trunk_lean"]:
            issues.append("躯干过度前倾：最大 %.0f 度" % max(leans))

        diffs = [r["lr_diff"] for r in self.reps if r["lr_diff"] is not None]
        if diffs and max(diffs) > self.rules["max_lr_diff"]:
            issues.append("左右不对称：最大膝角差 %.0f 度" % max(diffs))

        return issues


# ---------- 画图 ----------

def draw_skeleton(bgr, pts, color=(0, 200, 120)):
    for a, b in POSE_EDGES:
        cv2.line(bgr, tuple(pts[a].astype(int)), tuple(pts[b].astype(int)),
                 color, 2, cv2.LINE_AA)
    for i in range(len(pts)):
        cv2.circle(bgr, tuple(pts[i].astype(int)), 4, (255, 255, 255), -1, cv2.LINE_AA)
    for i in (L_KNEE, R_KNEE):
        cv2.circle(bgr, tuple(pts[i].astype(int)), 7, (0, 120, 255), 2, cv2.LINE_AA)
    return bgr


def draw_hud(bgr, metrics, count, state, issues=None):
    knee = metrics["knee"] if metrics else float("nan")
    hip = metrics["hip"] if metrics else float("nan")
    lean = metrics["lean"] if metrics else float("nan")

    def fmt(label, v):
        return label + ("%6.1f deg" % v if v == v else "    --")

    lines = [
        "COUNT  " + str(count),
        fmt("KNEE   ", knee),
        fmt("HIP    ", hip),
        fmt("LEAN   ", lean),
        "STATE  " + state,
    ]
    y = 34
    for line in lines:
        cv2.putText(bgr, line, (14, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (40, 220, 140), 2, cv2.LINE_AA)
        y += 26

    if issues:
        cv2.putText(bgr, "! " + issues[0], (14, y + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (60, 60, 235), 2, cv2.LINE_AA)
    return bgr
