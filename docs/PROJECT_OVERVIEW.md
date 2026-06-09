# 影子跟读训练软件 — 项目概览

> AI 驱动的英语影子跟读（Shadowing）桌面训练工具  
> 当前版本：**v1.2** | 平台：Windows（可跨平台）  
> UI 主题：**明日方舟（Arknights）暗色科幻工业风**

---

## 目录

- [技术栈](#技术栈)
- [文件罗列及简介](#文件罗列及简介)
- [架构与数据流](#架构与数据流)
- [编程风格](#编程风格)
- [当前功能清单](#当前功能清单)
- [未来计划增加的功能](#未来计划增加的功能)
- [已知问题与技术债](#已知问题与技术债)
- [开发约定](#开发约定)

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **UI** | `customtkinter` + `tkinter` | 明日方舟风格暗色科幻 GUI，六边形装饰 + 青橙双色点缀 |
| **音频 I/O** | `sounddevice` / `soundfile` | 录音与播放 |
| **语音识别（实时）** | `vosk` | 离线实时 STT，Kaldi 内核 |
| **语音识别（精密）** | OpenAI Whisper API (`openai`) | 在线高精度转写+逐词时间戳 |
| **语音合成** | `edge-tts` / `pyttsx3` / Piper | 三引擎可切换 |
| **音频处理** | `numpy` | 数组运算与重采样 |
| **持久化** | `sqlite3` (WAL 模式) | 练习素材库 + 练习记录 |
| **配置** | `config.json` + `.env` | 首次启动自动生成 |
| **语言** | Python 3 | 中英双语界面 |

---

## 文件罗列及简介

### 根目录

| 文件 | 职责 |
|------|------|
| `main.py` | 入口：初始化配置 → 启动 `ShadowingApp`（含错误诊断包裹） |
| `启动影子跟读.bat` | Windows 启动脚本，自动选择 venv 或系统 Python |
| `requirements.txt` | 依赖声明（8 个包） |
| `config.example.json` | 参考配置文件，首次运行自动生成 `config.json` |
| `.env.example` | 参考环境变量（`WHISPER_API_KEY`） |
| `.gitignore` | 排除 pycache、vosk 模型、venv、临时文件等 |
| `version.txt` | 语义化版本号源（如 `1.3.0`） |
| `build.py` | 一键构建脚本：PyInstaller → Inno Setup / 便携 zip |
| `build.spec` | PyInstaller 打包规格文件 |
| `installer.iss.template` | Inno Setup 安装脚本模板（含数据目录选择页） |

### `src/` — 源代码

#### 核心控制器

| 文件 | 职责 |
|------|------|
| `src/app.py` | **`ShadowingApp` 类**（~391 行）。构建 GUI、协调录音/播放/TTS/ASR/比较全过程；维护状态机（generate → shadowing → finished）；每 200ms 轮询更新 UI |

#### `src/utils/` — 配置工具

| 文件 | 职责 |
|------|------|
| `src/utils/config.py` | 配置管理：从硬编码默认值自动生成 `config.json` 和 `.env`；`init_config()` / `get_config()` / `deep_merge()` |
| `src/utils/paths.py` | 数据目录解析：`get_app_dir()` / `get_data_dir()` / `get_db_path()` 等，支持便携版和安装版的目录解耦 |
| `src/utils/model_downloader.py` | 模型下载工具：从 alphacephei.com 下载 Vosk 模型 ZIP，解压到数据目录，带进度回调 |
| `src/utils/error_diagnosis.py` | 启动错误诊断：8 条错误码（E001~E999），含控制台捕获 + 中文解决方案弹窗 |

#### `src/models/` — 数据层

| 文件 | 职责 |
|------|------|
| `src/models/db.py` | SQLite 单例，WAL 模式，线程安全 |
| `src/models/material.py` | `Material` 数据类 + CRUD（materials 表、practice_records 表） |
| `src/models/practice_record.py` | **空文件，预留占位** |

#### `src/services/` — 业务服务

| 文件 | 职责 |
|------|------|
| `src/services/audio_player.py` | 参考音频播放：`sounddevice.play()` 全异步，`position` 基于 `time.time()` 增量 |
| `src/services/audio_recorder.py` | 麦克风采集：`InputStream` 回调 → `queue.Queue`，实时 RMS 电平 |
| `src/services/speech_recognizer.py` | Vosk 实时语音识别：后台线程消费音频队列，逐词输出（word/start/end/conf） |
| `src/services/comparator.py` | 跟读对比引擎：`SequenceMatcher` 逐词对齐 Vosk 转写与参考文本（处理词数不一致），语速比对（绿/黄/红），准确率（`difflib.SequenceMatcher`） |
| `src/services/asr/__init__.py` | ASR 工厂：`create_asr_engine("vosk"\|"whisper")` |
| `src/services/asr/base.py` | ASR 抽象基类 `BaseASREngine` |
| `src/services/asr/vosk_asr.py` | 离线 Vosk 音频文件转写，支持重采样到 16kHz |
| `src/services/asr/whisper_asr.py` | OpenAI Whisper API 在线转写，逐词时间戳 |
| `src/services/tts/__init__.py` | TTS 工厂：`create_tts_engine("edge"\|"piper"\|"pyttsx3")`；**含一份冗余的 `BaseTTSEngine` 定义** |
| `src/services/tts/base.py` | TTS 抽象基类 `BaseTTSEngine`（与 `__init__.py` 中重复，实际未被使用） |
| `src/services/tts/edge_tts.py` | Azure Edge TTS（在线免费），默认语音 `en-US-JennyNeural` |
| `src/services/tts/piper_tts.py` | Piper TTS（离线），子进程调用 `piper.exe` |
| `src/services/tts/pyttsx3_tts.py` | 系统 TTS（离线），rate=155，保存为 WAV |

#### `src/gui/` — 图形界面

| 文件 | 职责 |
|------|------|
| `src/gui/panels/feedback_panel.py` | 语速/准确率实时仪表盘（Canvas 水平进度条 + 发光效果） |

#### `src/gui/` — 图形界面

| 文件 | 职责 |
|------|------|
| `src/gui/styles.py` | 主题常量：明日方舟暗色调色板 + 六边形/边框装饰工具函数（`draw_hex_indicator`, `draw_panel_border`） |
| `src/gui/panels/device_panel.py` | 设备选择 + 画布实时电平表（绿/黄/红发光效果） |
| `src/gui/panels/input_panel.py` | 文本输入区 + TTS 引擎选择 + 文件加载 + Whisper 精密转写按钮 |
| `src/gui/panels/feedback_panel.py` | 语速/准确率实时仪表盘（Canvas 水平进度条 + 发光效果）——仅训练屏可见 |
| `src/gui/panels/display_panel.py` | 富文本展示区：左栏参考文本逐词高亮+准确率色条，右栏用户实时识别文本+低置信度标记，底部详细统计——仅训练屏可见 |
| `src/gui/panels/material_panel.py` | 素材库面板：可折叠、可搜索、CRUD 弹窗——仅设置屏可见 |
| `src/gui/panels/download_dialog.py` | 模型下载弹窗：启动时未找到模型时弹出，可选小/大模型，显示下载+解压进度条 |
| `src/gui/panels/settings_dialog.py` | 设置窗口：倒计时秒数配置 + 开发人员选项（手动触发各错误码诊断弹窗） |

### 构建文件

| 文件 | 职责 |
|------|------|
| `build.py` | 一键构建脚本：`python build.py [--full] [--portable]` |
| `build.spec` | PyInstaller 打包规格定义 |
| `installer.iss.template` | Inno Setup 安装脚本模板（含数据目录选择页） |
| `version.txt` | 语义化版本号源 |

---

## 架构与数据流

```
main.py ──► ShadowingApp (src/app.py)
              │
              ├─ utils/config.py           # 配置自生成
              ├─ models/db.py              # SQLite 单例
              ├─ models/material.py        # 素材+记录 CRUD
              │
              ├─ services/audio_player.py   # 播放参考音频
              ├─ services/audio_recorder.py # 采集麦克风
              ├─ services/speech_recognizer.py # 实时 Vosk STT
              ├─ services/comparator.py     # 语速+准确率评分
              ├─ services/asr/*            # 离线/在线文字转写
              ├─ services/tts/*            # 多引擎语音合成
              │
               └─ gui/panels/*              # 6 个 UI 面板
```

### 状态机 + 双屏布局

```
┌─────────────────────────────────────┐
│  SETUP SCREEN（设置屏）               │
│  ┌─────────────────────────────────┐│
│  │ Device Panel (Input/Output)     ││
│  │ Input Panel (Text + TTS Engine) ││
│  │ Material Panel (collapsible)    ││
│  ├─────────────────────────────────┤│
│  │ [GENERATE AUDIO] [START SHADOWING] ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
  [输入文本/加载素材]
        │
        ▼
  MODE: generate       按钮：「GENERATE AUDIO」
        │ 点击
        ▼
  TTS 合成 → Vosk 打轴 → 加载播放器
        │
        ▼
  MODE: shadowing      按钮：「START SHADOWING」
        │ 点击
        ▼
┌─────────────────────────────────────┐
│  TRAINING SCREEN（训练屏）            │
│  ┌─────────────────────────────────┐│
│  │ Feedback Panel (Speed + Accuracy) ││
│  │ Display Panel (Ref + User Text)  ││
│  ├─────────────────────────────────┤│
│  │ [TERMINATE]                     ││
│  └─────────────────────────────────┘│
│  RUNNING: 播放 + 录音 + 实时 STT     │
│  + 对比评分 → 播放结束自动返回设置屏   │
└─────────────────────────────────────┘
```

### 数据流（训练过程中）

```
麦克风 ──► AudioRecorder ──► queue.Queue ──► SpeechRecognizer (Vosk)
                                                    │
                                                    ▼
                                           recognized_words[]
                                                    │
参考音频 ──► AudioPlayer ──► position ──────────────┤
              │                                      │
              ▼                                      ▼
         Comparator ─────────────────────────────────
              │                    │
     compare_speed()      compare_accuracy()
              │                    │
              ▼                    ▼
       FeedbackPanel          DisplayPanel
      (语速/准确率仪表)     (逐词高亮 + 用户文本 + 详情)
```

---

## 编程风格

### 命名规范

| 类型 | 风格 | 示例 |
|------|------|------|
| 类名 | PascalCase | `ShadowingApp`, `VoskASREngine`, `AudioRecorder` |
| 函数/方法 | snake_case | `init_config()`, `compare_accuracy()`, `list_materials()` |
| 私有成员 | `_` 前缀 | `_audio_data`, `_is_running`, `_on_text_changed()` |
| 常量 | UPPER_SNAKE | `FONT_FAMILY`, `VOSK_AVAILABLE` |
| 模块文件 | snake_case 后缀 | `vosk_asr.py`, `audio_recorder.py` |

### 设计模式

- **单例** — `Database` 类（双检锁线程安全）
- **工厂函数** — `create_tts_engine()` / `create_asr_engine()` 按名称创建实例
- **策略模式** — `BaseTTSEngine` / `BaseASREngine` 抽象基类 + 多实现
- **观察者轮询** — 200ms `_update_loop()` via `root.after()`
- **生产者-消费者** — `AudioRecorder` → `queue.Queue` → `SpeechRecognizer` 线程

### 代码组织特征

- **三层架构**：`gui/`（展示）→ `app.py`（控制器）→ `services/` + `models/`（逻辑+数据）
- **懒加载导入**：外部依赖在函数内部 `import`，避免循环引用和可选依赖问题
- **Print 日志**：全项目使用 `[ModuleName]` 前缀的 `print()` 日志
- **优雅降级**：所有外部依赖包裹 `try/except`，失败时有中文提示
- **中英双语**：代码标识符用英文，UI 文本为 Arknights 风格英文大写（原为中文）

---

## 当前功能清单

- [x] 自定义 Tkinter 明日方舟风格 UI（暗色科幻工业风 + 六边形装饰 + 青橙双色点缀）
- [x] 文本输入 + 文件加载（TXT / 粘贴）
- [x] 三引擎 TTS 合成参考语音（Edge 在线 + Piper 离线 + pyttsx3 离线）
- [x] 在线/离线音频转写打轴（Vosk 离线 + Whisper API 在线）
- [x] 音频设备选择 + 实时输入电平表
- [x] 参考音频播放（分块流式）
- [x] 麦克风实时录音 + Vosk 实时语音识别
- [x] 语速比对（绿/黄/红三色指示）
- [x] 发音准确率评分（`SequenceMatcher` 逐词比对）
- [x] 参考文本逐词高亮（当前词/已读/未读）
- [x] 用户识别文本实时展示（逐词置信度下划线+色标）
- [x] 低置信度词星标 + 训练后复习列表
- [x] 素材库：SQLite 持久化 + GUI CRUD
- [x] 练习记录追踪（次数、最佳得分）
- [x] 按钮模式切换（生成语音 ↔ 开始跟读）
- [x] 文本修改自动检测
- [x] 首次启动自动生成 `config.json` + `.env`
- [x] Vosk 模型自动下载（启动时弹窗，可选小模型 40MB / 大模型 1.8GB，带进度条）

---

## 未来计划增加的功能

> 基于代码中预留的扩展点、空占位文件、当前架构可自然延伸的方向推测：

### 短期

- [ ] **练习记录详情面板** — `src/models/practice_record.py` 为空占位文件，预计独立出练习记录的 Model 层逻辑，或增加历史记录可视化（趋势图）
- [ ] **素材库音频批量导入** — 当前仅支持单文件加载，添加文件夹批量导入+自动 Vosk 打轴
- [ ] **快捷键支持** — 空格键开始/停止跟读，上下键选素材
- [ ] **设置面板 GUI** — 当前所有配置通过 `config.json` 硬编码，无 GUI 设置界面

### 中期

- [ ] **多语言素材支持** — 当前硬编码英文 ASR 模型，增加其他语言的 Vosk 模型切换
- [ ] **更多 TTS 引擎** — 代码架构已预留工厂模式，可接入 Coqui TTS / XTTS / OpenAI TTS API
- [ ] **更多 ASR 引擎** — 架构已预留，可接入 faster-whisper 本地推理、Azure Speech API
- [ ] **跟读历史趋势图** — 基于 SQLite 中的 `practice_records` 表绘制得分变化曲线
- [ ] **导出训练报告** — PDF / CSV 导出某素材的跟读历史
- [ ] **素材难度自动分级** — 基于文本长度、词汇复杂度自动标记素材难度

### 长期

- [ ] **跨平台打包** — macOS/Linux 支持，PyInstaller 打包发布
- [ ] **联网素材库** — 从公开 API（如 TED、VOA）搜索和导入素材
- [ ] **社区素材分享** — 用户上传/下载跟读素材
- [ ] **AI 教练反馈** — 接入大模型，对发音错误给出具体纠正建议（如音标、口型）

---

## 已知问题与技术债

| 问题 | 位置 | 说明 |
|------|------|------|
| 重复 ABC 定义 | `src/services/tts/__init__.py` vs `src/services/tts/base.py` | `BaseTTSEngine` 在两处定义，实际只用 `__init__.py` 版本，`base.py` 为死代码 |
| 空占位文件 | `src/models/practice_record.py` | 完全为空，实际练习记录逻辑全在 `material.py` 中 |
| 无类型标注 | 全局 | 大多数方法参数无类型提示，仅少量使用 `typing` |
| Print 日志 | 全局 | 未使用 `logging` 模块，全项目 `print()` 调试输出 |
| 硬编码默认文本 | `src/gui/panels/input_panel.py:51-55` | 内置了一段英文绕口令作为默认文本 |
| 无单元测试 | 全局 | 项目中无任何测试文件 |
| Windows 路径假设 | `piper_tts.py` 等 | `piper.exe` 搜索逻辑隐含 Windows 假设 |

---

## 开发约定

1. **提交信息**使用中文，格式为 `type: description`（如 `feat: xxx`、`fix: xxx`、`refactor: xxx`）
2. **代码本身**：标识符英文、UI 字符串中文
3. **新增服务引擎**：继承对应 ABC 基类，在工厂函数 `__init__.py` 中注册
4. **新增 GUI 面板**：在 `src/gui/panels/` 下新建文件，在 `app.py` 中实例化并加入布局
5. **素材库操作**：通过 `src/models/material.py` 中的函数操作，不直接写 SQL
6. **播放/录音**：使用 `sounddevice` 的 InputStream/OutputStream，不另起线程直接操作 PyAudio
