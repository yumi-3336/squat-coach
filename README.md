# squat-coach · 深蹲动作识别与纠错

用摄像头判断「这一下深蹲做得对不对」。

不需要穿戴设备，一部手机 + 一段视频，就能得到膝角、躯干前倾、左右对称性等指标，以及"有没有蹲到位"的判定。

> 项目缘起：室友照着短视频练深蹲，膝盖内扣、耸肩代偿，三个月后伤了膝盖。私教一节课几百元，他负担不起。

---

## 运行环境

| 项目 | 要求 |
|---|---|
| 操作系统 | Windows 10 / 11 |
| Python | 3.13（本项目在 3.13.9 上验证通过） |
| 项目路径 | **必须纯英文**，例如 `D:\Work\squat-coach` |

> ⚠️ **路径是第一个坑**。Windows 上 OpenCV 和 mediapipe 对中文路径支持很差，
> 容易报"文件不存在"或"读不到模型"，但不给出明确原因。
> 项目路径里只要出现一个中文字，请先改名再跑。

---

## 效果

| 输入 | 输出 |
|---|---|
| 一张全身照 | 33 个关键点的骨架图 + 膝角/髋角/前倾角 |
| 一段深蹲视频 | 带骨架、实时角度、计数的标注视频 + 每次动作明细 JSON |

标注视频左上角会显示：

```
COUNT  3
KNEE   92.0 deg
HIP    94.0 deg
LEAN   23.5 deg
STATE  down
```

---

## 快速开始

```bat
cd /d D:\Work\squat-coach
.venv\Scripts\activate
python demo_keypoints.py --input samples\me_squat.png --output output\me_keypoints.png
```

## 目录结构

```
D:\Work\squat-coach\
├── models\                      pose_landmarker_lite.task（模型，5.8 MB）
├── samples\                     你的照片和视频放这里
│   └── labels.csv               批量评测时的人工真值表
├── output\                      所有输出（已 gitignore）
├── pose_core.py                 共用模块：几何计算 + 规则库 + 状态机
├── demo_keypoints.py            出关键点图/视频
├── squat_counter.py             计数 + 合规判定
├── evaluate.py                  批量评测
├── requirements.txt
└── SETUP.md                     逐步操作细则
```

---

## 判定规则（规则库）

全部阈值集中在 `pose_core.py` 的 `RULES` 字典里，改这一处即可。

| 规则 | 阈值 | 依据 |
|---|---|---|
| 蹲下判定 | 膝角 < 110° | 大腿接近水平时膝角约 90–110° |
| 站直判定 | 膝角 > 160° | 计数复位点，留滞回避免抖动误计 |
| 深度合格 | 最小膝角 ≤ 100° | 低于 100° 才算蹲到位 |
| 躯干前倾 | ≤ 45° | 超过则腰背剪切力显著上升 |
| 膝盖前移 | ≤ 0.18 × 身高 | 前移过大会增加髌股压力 |
| 动作节奏 | ≥ 0.8 s/次 | 离心阶段过快容易失控 |
| 左右对称 | 膝角差 ≤ 15° | 差值过大提示单侧代偿 |

侧视视角可判定深度、前倾、节奏、对称性。膝内扣需要正视视角，属下一步计划。

---

## 评测方法

```bat
python evaluate.py --dir samples
:: 填写 samples\labels.csv 的 true_count 列
python evaluate.py --dir samples --report output\eval_report.csv
```

目标是平均绝对误差 **≤ 2 次/组**。

---

## 踩坑记录

| 现象 | 原因 | 解法 |
|---|---|---|
| `module 'mediapipe' has no attribute 'solutions'` | mediapipe 1.x 删除了旧 API | 改用 Tasks API（`vision.PoseLandmarker`） |
| `AttributeError: function 'free' not found` | mediapipe 0.10.x 在 Py3.13 + Win 的 DLL bug | 固定 `mediapipe==1.2.2` |
| `Unable to open file ...pose_landmarker_lite.task` | 路径含中文，C++ 层打不开 | 路径改纯英文；且代码用 `model_asset_buffer` 传字节流 |
| `cv2.imread` 返回 None 但不报错 | 中文路径 | 用 `np.fromfile` + `imdecode` |
| 角度算出来明显偏小/偏大 | 用归一化坐标算角度，被长宽比拉伸 | 先转像素坐标（`x*width, y*height`） |
| 换了文件夹后 `activate` 失效 | venv 里记录的是创建时的绝对路径 | 移动后删掉 `.venv` 重建 |

---

## 下一步

- [ ] 正视视角，补膝内扣（Knee Valgus）判定
- [ ] 多动作扩展：硬拉、卧推、箭步蹲
- [ ] 端侧轻量化（模型量化 + TFLite）
- [ ] 30 段样本评测表 + 参数敏感性分析
- [ ] 小程序封装，让寝室同学真的用起来

---

## 免责声明

学习与研究性质的工程实践，输出结果不构成医疗或康复建议。有疼痛或既往损伤者请咨询专业人士。
