# RIShadowing

**AI 驱动的英语影子跟读（Shadowing）桌面训练工具**

UI 采用**明日方舟（Arknights）暗色科幻工业风**主题，离线语音识别（Vosk），实时跟读评分。

---

## 功能特性

- **文本输入 / 素材库管理** — 手动输入或从素材库选择参考文本
- **多引擎 TTS 合成** — Edge TTS（在线免费）/ Piper（离线）/ pyttsx3（系统 TTS）
- **AI 语音转写打轴** — Vosk（离线）或 OpenAI Whisper API（在线精密）
- **实时跟读练习** — 播放参考音频 + 麦克风采集 + 实时语音识别
- **词距匹配评分** — 黄色样本光标指示当前应跟读位置，按词距三色着色：
  - 绿色：匹配词距光标 ≤ 1 词（精准）
  - 黄色：匹配词距光标 ≤ 3 词（稍偏）
  - 红色：匹配词距光标 ≤ 5 词（偏差）
- **双光标追踪** — 黄色光标（跟读样本位）+ 蓝色光标（音频播放位）
- **语速/准确率仪表盘** — 实时绿/黄/红三色反馈
- **低置信度词汇总** — 训练结束后标记需复习的单词
- **练习记录** — SQLite 持久化，追踪练习次数与最佳得分
- **Vosk 模型自动下载** — 启动时弹窗可选小模型（40MB）/ 大模型（1.8GB）
- **自动更新检查** — GitHub API 检测新版本，支持一键下载更新

---

## 安装与运行

### 环境要求

- Windows 10/11（64 位）
- Python 3.9+
- 麦克风 + 扬声器

### 从源码运行

```bash
# 克隆仓库
git clone https://github.com/NaBCberry/RIShadowing.git
cd RIShadowing

# 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 如果使用离线 Vosk 语音识别，下载模型到项目根目录
# 或首次运行时在弹窗中选择自动下载

# 运行
python main.py
```

### 使用打包版本

前往 [Releases](https://github.com/NaBCberry/RIShadowing/releases) 页面下载：

| 文件 | 说明 |
|------|------|
| `RIShadowing_x.x.x_Lite_Setup.exe` | 安装版（不含模型，首次启动自动下载） |
| `RIShadowing_x.x.x_Portable_Lite.zip` | 便携版（不含模型） |
| `RIShadowing_x.x.x_Portable_Full.zip` | 便携版（含 Vosk 小模型） |

---

## 使用指南

### 1. 准备参考文本

在**设置屏**输入或选择一段英文文本作为跟读素材。

- **手动输入**：在文本框粘贴或输入英文文本
- **素材库**：点击 "MATERIAL LIBRARY" 从素材库中选择已有素材
- **文件加载**：加载 `.txt` 文件

### 2. 生成参考音频

点击 **"GENERATE AUDIO"** 按钮，系统将：

1. 使用 TTS 引擎合成参考语音（推荐 Edge TTS）
2. 自动用 Vosk 或 Whisper 对生成的音频进行文字打轴
3. 指示灯变绿表示准备就绪

### 3. 开始跟读练习

点击 **"START SHADOWING"** 进入训练屏：

- 倒计时后开始播放参考音频
- 界面显示两个光标和一个图例面板：

```
● 精准 (≤1词)  ● 稍偏 (≤3词)  ● 偏差 (≤5词)  │  ■ 跟读光标  ■ 音频光标

跟读指南：跟随黄色光标朗读，优先匹配离光标近的参考词，保持与音频播放节奏一致
```

- **蓝色光标** = 音频当前播放位置（已知词）
- **黄色光标** = 应跟读到的参考词位置（目标词）
- 你朗读的词会自动在参考文本中匹配并着色（绿/黄/红）
- 底部显示实时语音识别结果和语速状态

练习在黄色样本光标到达文本末尾时自动结束。

### 4. 查看结果

训练结束后显示总评（G:Y:R 计数及绿词占比），练习记录自动保存到数据库。

### 5. 设置调整

点击右下角齿轮图标打开设置面板：

- **倒计时秒数** — 开始跟读前的倒计时（0.5-10 秒）
- **绿色匹配距离** — 词距在此范围内标绿色（默认 1）
- **黄色匹配距离** — 词距在此范围内标黄色（默认 3）
- **红色匹配距离** — 词距在此范围内标红色（默认 5）
- **跟读滞后时间** — 黄色样本光标落后音频的时间（0.5-10 秒）

---

## 从源码构建

```bash
# 安装构建依赖
pip install pyinstaller

# 构建便携版（Lite，无模型）
python build.py --portable

# 构建便携版 Full（含 Vosk 小模型）
python build.py --portable --full

# 构建安装版（需要 Inno Setup 6）
python build.py --installer

# 构建全部版本
python build.py --all
```

构建产物输出到 `dist_output/`。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| UI | `customtkinter` + `tkinter` |
| 音频 I/O | `sounddevice` / `soundfile` |
| 语音识别 | `vosk`（离线实时） / OpenAI Whisper API |
| 语音合成 | `edge-tts` / `pyttsx3` / Piper |
| 数据存储 | SQLite（WAL 模式） |
| 打包 | PyInstaller + Inno Setup |
| 语言 | Python 3 |

---

## 项目结构

```
RIShadowing/
├── main.py                 # 入口
├── build.py                # 构建脚本
├── build.spec              # PyInstaller 规格
├── installer.iss.template  # Inno Setup 模板
├── version.txt             # 版本号
├── requirements.txt
├── RIShadowing.ico
├── src/
│   ├── app.py              # 主控制器（状态机 + 更新循环）
│   ├── gui/                # UI 面板
│   │   ├── styles.py       # 明日方舟主题色
│   │   └── panels/
│   │       ├── display_panel.py    # 参考文本展示 + 评分着色
│   │       ├── feedback_panel.py   # 语速/准确率仪表盘
│   │       ├── input_panel.py      # 文本输入 + TTS
│   │       ├── material_panel.py   # 素材库 CRUD
│   │       ├── device_panel.py     # 设备选择 + 电平表
│   │       ├── settings_dialog.py  # 设置窗口
│   │       └── download_dialog.py  # 模型下载弹窗
│   ├── services/            # 业务服务
│   │   ├── audio_player.py
│   │   ├── audio_recorder.py
│   │   ├── speech_recognizer.py
│   │   ├── comparator.py
│   │   ├── asr/             # 语音转写引擎
│   │   └── tts/             # 语音合成引擎
│   ├── models/              # 数据层
│   │   ├── db.py
│   │   └── material.py
│   └── utils/               # 工具
│       ├── config.py
│       ├── paths.py
│       ├── updater.py
│       ├── error_diagnosis.py
│       └── model_downloader.py
└── docs/
    └── PROJECT_OVERVIEW.md  # 详细项目文档
```

---

## 许可证

MIT License

---

## 作者

- GitHub: [@NaBCberry](https://github.com/NaBCberry)
