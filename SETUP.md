# 今晚操作细则 · squat-coach

> 版本：v2（重写版）  
> 适用环境：Windows 10 / 11 · Python 3.13  
> 项目固定路径：`D:\Work\squat-coach`  
> **本文件之外的操作说明一律作废，只按这份做。**

---

## 先搞清楚上次为什么错

上次报错不是代码的错，是两个路径问题叠加：

| 编号 | 原因                        | 表现                                                                                                          |
| -- | ------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 1  | 项目放在 `D:\工作\...` 下，路径含中文  | OpenCV 和 mediapipe 的底层是 C++，对中文路径处理很差。`cv2.imread` 会**静默返回 None 且不报错**；mediapipe 会直接报 `Unable to open file` |
| 2  | 虚拟环境 `.venv` 里写死了创建时的绝对路径 | 文件夹一移动或改名，`.venv\Scripts\activate` 里记的还是旧路径，激活后找不到解释器，报一堆 `Fatal error in launcher` / `No module named ...` |

**这次的彻底解法**：

1. 项目搬到纯英文路径 `D:\Work\squat-coach`，从目录名到文件名全部 ASCII；
2. 虚拟环境在**最终位置**重新创建，不再移动；
3. 所有命令统一用绝对路径 `cd /d D:\Work\squat-coach`，不靠当前目录。

**当前状态**：这三件事我已经做完了，环境也装好并通过自检。你从第 1 步开始验证即可。

---

## 第 1 步 · 打开命令行，进入项目目录

按 `Win + R`，输入 `cmd`，回车。

```bat
cd /d D:\Work\squat-coach
```

**预期结果**：命令行提示符变成 `D:\Work\squat-coach>`

**验证一下目录对不对**：

```bat
dir
```

应该能列出这些文件：`pose_core.py`、`demo_keypoints.py`、`squat_counter.py`、`evaluate.py`、`selftest.py`、`requirements.txt`、`README.md`、`SETUP.md`，以及 `models`、`samples`、`output` 三个文件夹。

| 常见错误              | 原因                        | 解法                                                |
| ----------------- | ------------------------- | ------------------------------------------------- |
| `系统找不到指定的路径`      | `D:\Work\squat-coach` 不存在 | 回到本文档顶部确认，或重新执行「重建」步骤（见附录 C）                      |
| `dir` 里没有那些 py 文件 | 进错目录了                     | `cd /d D:\Work\squat-coach`，注意 `/d` 不能省，否则跨盘符切换无效 |
| 中文显示成乱码           | cmd 默认 GBK                | 输入 `chcp 65001` 回车，或忽略（不影响运行）                     |

---

## 第 2 步 · 激活虚拟环境

```bat
.venv\Scripts\activate
```

**预期结果**：提示符前面多出一对括号：

```
(.venv) D:\Work\squat-coach>
```

看到 `(.venv)` 才算激活成功。**后面每一步都要在这个状态下执行。**

| 常见错误                                   | 原因                     | 解法                                              |
| -------------------------------------- | ---------------------- | ----------------------------------------------- |
| `无法加载文件 ...activate.ps1，因为在此系统上禁止运行脚本` | 你用的是 PowerShell，不是 cmd | 换回 cmd（本文档全部用 cmd 语法）                           |
| `不是内部或外部命令`                            | `.venv` 目录不存在          | 执行附录 C 的「重建」步骤                                  |
| 提示符前没有 `(.venv)`                       | 没激活或激活失败               | 直接执行下一步，用 `.venv\Scripts\python.exe` 全路径调用，效果一样 |
| `Fatal error in launcher`              | 曾经移动过文件夹，venv 路径失效     | 删掉 `.venv` 重建（附录 C）                             |

> 怕激活出问题？**所有命令都可以用 `.venv\Scripts\python.exe` 替代 `python`**，绕开激活这一环。两种写法我都给。

---

## 第 3 步 · 跑自检（最重要的一步）

```bat
python selftest.py
```

**预期结果**：七项全部 PASS，最后一行是「自检通过」。

```
============================================================
squat-coach 环境自检
============================================================
[PASS] 路径为纯英文 D:\Work\squat-coach
[PASS] 依赖版本 Python 3.13.9 / mediapipe 1.2.2 / opencv 5.0.0 / numpy 2.5.4
[PASS] 模型文件存在 5.5 MB
[PASS] 模型可加载 模型加载成功，DLL 正常
[PASS] 角度计算正确 直角=90 直腿=180
[PASS] 计数状态机正确 模拟 3 次深蹲 -> 计数 3 次
[PASS] 视频读写正常 15 帧读写正常
============================================================
自检通过。环境没问题，可以进入下一步。
```

中间会冒出一堆 `W0000`、`I0000`、`INFO:` 开头的日志，那是 mediapipe 的正常输出，**不用管**。

| 常见错误                                                     | 原因                     | 解法                                               |
| -------------------------------------------------------- | ---------------------- | ------------------------------------------------ |
| `[FAIL] 路径为纯英文`                                          | 项目被移动到了含中文的目录          | 移回 `D:\Work\squat-coach`，或删 `.venv` 在新位置重建       |
| `[FAIL] 依赖版本 ModuleNotFoundError`                        | 没激活 venv，或依赖没装         | `pip install -r requirements.txt`                |
| `[FAIL] 模型文件存在`                                          | `models` 目录里没有 task 文件 | 见附录 B「下载模型」                                      |
| `[FAIL] 模型可加载 AttributeError: function 'free' not found` | mediapipe 版本不对         | `pip install mediapipe==1.2.2 --force-reinstall` |
| `[FAIL] 角度计算正确`                                          | 代码被改坏了                 | 用原始文件覆盖 `pose_core.py`                           |

**这一步不通过，后面一步都别做。** 环境问题在这里暴露，比在评委面前暴露好。

---

## 第 4 步 · 出一张自己的关键点图

### 4.1 拍照片

手机拍一张**全身侧面**照片：

- 头顶到脚完整入镜，**脚不能出框**
- 正侧面，或斜前 45°
- 光线充足，背景别太乱
- 蹲到底部的姿势（大腿接近水平）

存到 `D:\Work\squat-coach\samples\`，**文件名必须纯英文**，例如 `me_squat.png`。

> 文件名也别用中文。图片读取那段我做了兼容，但视频没有，统一用英文最省事。

### 4.2 跑命令

```bat
python demo_keypoints.py --input samples\me_squat.png --output output\me_keypoints.png
```

**预期结果**：

```
[OK] 检测到 33 个关键点
[OK] 膝角 92.3 度 / 髋角 94.1 度 / 躯干前倾 23.5 度
[OK] 已输出：output\me_keypoints.png
```

打开 `output\me_keypoints.png`，应该看到绿色骨架贴在你自己身上，膝盖位置是橙色圈。

**这就是报告图 1 的素材。**

| 常见错误                                               | 原因                      | 解法                                             |
| -------------------------------------------------- | ----------------------- | ---------------------------------------------- |
| `[警告] 没检测到人体`                                      | 人没拍全 / 太暗 / 背景太乱 / 躺着侧身 | 重拍，站着做深蹲底部姿势，全身入镜                              |
| `读不到图片`                                            | 文件名或路径写错                | `dir samples` 看一下真实文件名，注意扩展名是 `.jpg` 还是 `.png` |
| `ModuleNotFoundError: No module named 'pose_core'` | 不在项目根目录执行               | `cd /d D:\Work\squat-coach` 后重试                |
| 骨架位置明显偏移                                           | 视频/照片被旋转过 90 度          | 用画图工具另存为正向，或手机横拍时注意方向                          |

---

## 第 5 步 · 数深蹲（今晚的核心产出）

### 5.1 拍视频

手机固定好（靠墙、放椅子上都行），拍**侧面**，做 **5 次标准深蹲**。

拍摄要点：

1. 镜头高度约在**腰部**，别俯拍别仰拍
2. 距离 2–3 米，人占画面高度 70% 左右
3. 全身入镜，**脚不能出框**
4. 每次深蹲之间站直停顿 1 秒
5. 全程 20–30 秒

存成如果是 iPhone 默认格式（HEVC），先在手机里导出成兼容格式，或用剪映转一次。

### 5.2 跑计数

```bat
python squat_counter.py --input samples\me_squat_5.mp4 --output output\me_result.mp4 --json output\me_result.json
```

**预期结果**：

```
========================================================
文件      : me_squat_5.mp4
帧数      : 620（检测到人体 615 帧，99.2%）
深蹲次数  : 5
问题提示  : 未发现明显问题（或本次动作数为 0）
========================================================
标注视频  : output\me_result.mp4
结果 JSON : output\me_result.json
```

打开 `output\me_result.mp4`，左上角实时显示：

```
COUNT  5
KNEE   92.0 deg
HIP    94.0 deg
LEAN   23.5 deg
STATE  down
```

**这段视频是答辩现场最有杀伤力的东西——放视频，比讲十句话管用。**

| 常见错误             | 原因                  | 解法                          |
| ---------------- | ------------------- | --------------------------- |
| `打不开视频` + 文件确实存在 | 编码是 HEVC/H.265      | 用剪映或格式工厂转成 H.264 的 mp4      |
| `检测到人体 0 帧`      | 人太小 / 背对镜头 / 光线不足   | 人占到画面高度 70%，侧面对镜头           |
| `深蹲次数 0`         | 蹲得不够深（膝角没到 110° 以下） | 加大幅度重拍，或按第 6 步调阈值           |
| 少算 1 次           | 没站直到 160° 以上        | 把 `knee_angle_up` 调到 155    |
| 多算 1–2 次         | 站直后晃动被误判            | 把 `knee_angle_down` 调到 105  |
| 输出视频打不开          | 播放器不支持 mp4v 编码      | 用 PotPlayer / VLC 播放，或用剪映转码 |

---

## 第 6 步 · 数不准时的调参方法

打开 `pose_core.py`，找到 `RULES` 这个字典（大概在第 40 行）：

```python
RULES = {
    "knee_angle_down": 110.0,     # 膝角小于它 = 已蹲下（开始计数）
    "knee_angle_up": 160.0,       # 膝角大于它 = 已站直（完成计数）
    "min_depth": 100.0,           # 最小膝角 <= 它才算够深
    "max_trunk_lean": 45.0,
    "max_knee_forward": 0.18,
    "min_rep_seconds": 0.8,
    "max_lr_diff": 15.0,
}
```

**只改前三个就够，每次改 5 度，改完重跑对比。**

| 现象              | 改哪个               | 怎么改                 |
| --------------- | ----------------- | ------------------- |
| 完全数不出来          | `knee_angle_down` | 110 → 120（更容易判定为蹲下） |
| 少数了             | `knee_angle_up`   | 160 → 155（更容易判定为站直） |
| 多数了             | `knee_angle_down` | 110 → 105（更难判定为蹲下）  |
| 提示"深度不足"但自己蹲得很深 | `min_depth`       | 100 → 105           |

**每次改完必须重跑同一段视频**，把结果记在下面这张表里，这就是你报告里的"参数敏感性分析"：

| 参数 | 值                 | 算法计数 | 人工计数 | 误差 |
| -- | ----------------- | ---- | ---- | -- |
| 基线 | down=110 / up=160 |      | 5    |    |
| 放宽 | down=120 / up=160 |      | 5    |    |
| 收紧 | down=105 / up=160 |      | 5    |    |

评委问"你怎么知道参数取得对"，这张表就是答案。

---

## 第 7 步 · 批量评测（30 段样本）

### 7.1 第一次运行，生成模板

```bat
python evaluate.py --dir samples
```

**预期结果**：

```
[模板] 已生成：samples\labels.csv
       把每段视频你人工数出的次数填进 true_count 列，保存后重新运行本脚本。
```

### 7.2 填真值

用 Excel 或记事本打开 `samples\labels.csv`，在 `true_count` 列填你**人工数的次数**，保存。

> 如果保存后中文变乱码，用 Excel 打开另存为「CSV UTF-8」格式。

### 7.3 再运行

```bat
python evaluate.py --dir samples --report output\eval_report.csv
```

**预期结果**：

```
============================================================
样本数        : 30（跳过 0 段未填真值）
平均绝对误差  : 0.43 次/组
完全命中率    : 70.0%
偏差最大样本  : me_squat_12.mp4（真值 5，算法 7）
评测表        : output\eval_report.csv
============================================================
```

**把「平均绝对误差」和「完全命中率」两个数写进报告。** 目标误差 ≤ 2 次/组。

### 7.4 30 段怎么拍才有说服力

别拍 30 段一样的，评委会问"你的失败样本是什么"。

| 维度   | 取值                    | 覆盖什么    |
| ---- | --------------------- | ------- |
| 拍摄者  | 自己 / 室友 / 同学          | 体型差异    |
| 机位   | 正侧 / 斜前 45° / 略俯视     | 视角鲁棒性   |
| 速度   | 慢 3 秒 / 中 2 秒 / 快 1 秒 | 快速动作漏检  |
| 故意失败 | 2 段只入镜半身、2 段逆光        | 明确的失败样本 |

| 常见错误          | 原因                           | 解法                      |
| ------------- | ---------------------------- | ----------------------- |
| `目录下没有找到视频文件` | 视频放在子文件夹里                    | 视频要直接放在 `samples\` 根下   |
| 一直提示生成模板      | `labels.csv` 的 true_count 全空 | 至少填一行再运行                |
| 某一段一直失败       | 编码问题                         | 单独转码，或把它从 labels.csv 删掉 |

---

## 第 8 步 · 建 GitHub 仓库

### 8.1 网页建仓库

登录 GitHub，右上角 `+` → `New repository`：

- Repository name：`squat-coach`
- 选 `Public`
- **不要**勾 "Add a README file"（本地已经有了）
- 点 `Create repository`

### 8.2 本地提交

回到命令行（确认还在 `D:\Work\squat-coach`）：

```bat
git init
git config user.name "你的名字"
git config user.email "你的邮箱"
git add .
git commit -m "feat: 姿态估计跑通，可输出关键点图与深蹲计数"
git branch -M main
git remote add origin https://github.com/你的用户名/squat-coach.git
git push -u origin main
```

**预期结果**：刷新 GitHub 页面，能看到 `README.md`、`pose_core.py`、`models/` 等文件。

| 常见错误                                  | 原因              | 解法                                     |
| ------------------------------------- | --------------- | -------------------------------------- |
| `Author identity unknown`             | 没配 git 身份       | 执行上面两条 `git config`                    |
| `src refspec main does not match any` | 提交前没 add/commit | 按顺序重做 `git add .` 和 `git commit`       |
| `failed to push some refs`            | 网页建仓库时勾了 README | `git pull --rebase origin main` 再 push |
| `remote origin already exists`        | 之前加过            | `git remote set-url origin 新地址`        |
| 推送很慢 / 超时                             | 网络              | 重试几次；或配置代理                             |

### 8.3 加分项

仓库页面右侧 `About` 齿轮里填：

- Description：`用摄像头判断深蹲做得对不对 · MediaPipe + OpenCV`
- Topics：`computer-vision`、`mediapipe`、`pose-estimation`、`fitness`

---

## 第 9 步 · 回填报告

打开 `D:\Work\reports\生涯发展报告_院赛改写版.md`，把第二部分（三）动手 的 ②③④ 改成**完成时**：

**改之前**：

> ② 工具落地：搭建 MediaPipe 与 OpenCV 环境，跑通官方姿态估计示例……  
> ③ 工程留痕：建立 GitHub 仓库 squat-coach……  
> ④ 数据验证：自采 30 段深蹲视频……

**改之后**（数字换成你自己的真实结果）：

> ② 工具落地：在 Python 3.13 + Windows 环境跑通 MediaPipe 姿态估计，输出 33 个关键点骨架，实现膝角、髋角、躯干前倾四项指标实时计算；  
> ③ 工程留痕：开源仓库 squat-coach（GitHub），已提交 N 次，README 记录 6 条环境踩坑（旧 API 移除、DLL 加载失败、中文路径、坐标系失真等）；  
> ④ 数据校验：自采 30 段样本，人工计数与算法计数平均绝对误差 X.XX 次/组，完全命中率 XX%，并完成深度阈值的参数敏感性分析。

---

## 附录 A · 错误速查表

按报错关键字查：

| 报错 / 现象                                            | 原因                                        | 解法                                               |
| -------------------------------------------------- | ----------------------------------------- | ------------------------------------------------ |
| `module 'mediapipe' has no attribute 'solutions'`  | mediapipe 1.x 删了旧 API                     | 本项目已用新 API，报这个说明代码被覆盖成旧版了                        |
| `AttributeError: function 'free' not found`        | mediapipe 0.10.x 在 Py3.13 + Win 的 DLL bug | `pip install mediapipe==1.2.2 --force-reinstall` |
| `Unable to open file ...pose_landmarker_lite.task` | 路径含中文                                     | 项目移到纯英文路径，重建 venv                                |
| `cv2.imread` 返回 None（不报错）                          | 中文路径 / 文件名写错                              | 已用 `safe_imread` 兼容图片；视频路径必须纯英文                  |
| `不是内部或外部命令`                                        | 命令拼错 / 不在项目目录                             | `cd /d D:\Work\squat-coach` 后重试                  |
| `No module named 'pose_core'`                      | 在别的目录执行                                   | 同上                                               |
| `ModuleNotFoundError: mediapipe`                   | venv 没激活                                  | `.venv\Scripts\activate`                         |
| `Fatal error in launcher`                          | 移动过文件夹，venv 路径失效                          | 删 `.venv` 重建                                     |
| 中文显示乱码                                             | cmd 编码                                    | `chcp 65001`                                     |
| 摄像头打不开                                             | 被微信/钉钉占用                                  | 关掉其他软件，或改用 `--input` 传视频                         |
| 输出视频花屏                                             | mp4v 编码兼容性差                               | 用 VLC 播放，或剪映转码                                   |

---

## 附录 B · 路径铁律（照做就不会再出错）

1. **项目根目录必须是 `D:\Work\squat-coach`**，不要改。
2. 所有文件名用英文 + 下划线：`me_squat.png` 可以，`我的深蹲.png` 不行。
3. 移动项目文件夹后，**必须删掉 `.venv` 重建**，否则一定报错。
4. 命令里的路径统一用反斜杠 `\`，或在 cmd 里也行用 `/`。
5. 每次新开命令行，第一句都是 `cd /d D:\Work\squat-coach`。
6. 不要在中文目录（桌面、我的文档）里解压或另存项目。
7. 报告类文件放 `D:\Work\reports\`，不要放回 `D:\工作`。

### 下载模型（万一 models 目录空了）

浏览器直接打开这个链接，会下载 `pose_landmarker_lite.task`（5.8 MB）：

```
https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task
```

下载完放进 `D:\Work\squat-coach\models\`。

---

## 附录 C · 从零重建（环境彻底坏掉时用）

```bat
cd /d D:\Work
rmdir /s /q squat-coach\.venv
cd /d D:\Work\squat-coach
"D:\Developer\Python\python.exe" -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python selftest.py
```


````

预计 1–2 分钟。装依赖时如果卡住，换国内镜像：

```bat
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
````

---

## 附录 D · 今晚时间表

| 时段    | 步骤                | 产出        |
| ----- | ----------------- | --------- |
| 20 分钟 | 第 1–3 步：进目录、激活、自检 | 环境确认可用    |
| 20 分钟 | 第 4 步：拍照、出关键点图    | 一张自己的骨架图  |
| 40 分钟 | 第 5 步：拍视频、数深蹲     | 一段标注视频    |
| 20 分钟 | 第 6 步：调参、记录结果     | 参数敏感性表    |
| 30 分钟 | 第 8 步：建仓库、推送      | GitHub 链接 |
| 20 分钟 | 第 9 步：回填报告        | 报告的完成时表述  |

合计约 2.5 小时。**做完第 5 步，你的报告就已经从"全是计划"变成"有作品"了。**

---

## 一句话

允许代码丑、允许数不准、允许视频糊。

**丑但能跑的东西叫作品，漂亮但跑不起来的想法叫笔记。**
