## RIShadowing v1.3.0

### 新增功能
- 明日方舟风格 UI 重制（双屏布局、三色指示灯、按钮 hover 效果）
- 倒计时（可配置秒数）后开始跟读
- 模型自动下载（可选小模型 40MB / 大模型 1.8GB）
- 错误诊断系统（E001-E999 错误码 + 解决方案 + 控制台输出）
- 设置窗口（倒计时配置 + 开发人员选项可手动触发各错误弹窗）
- 训练完成后停留在结果页面，手动点击 RETURN 返回

### Bug 修复
- 逐词高亮与音频不同步（position 计算 2x 速 bug）
- TERMINATE 中途终止卡顿闪退
- Vosk 在 PyInstaller 打包环境下 FileNotFoundError 崩溃
- 安装版 Program Files 只读目录 PermissionError（.env 移至 data_dir）
- 色条比高亮慢一个词 / 第一个词不显示（off-by-one 修复）
- 标点符号被计入词条（逗号句号不再占用色条）
- 生成完成后按钮变绿并显示 GENERATION ACCOMPLISHED!
- 黄灯闪烁被 TTS 阻塞（TTS 改后台线程执行）
- 模型下载后未自动加载（extract_dir 路径多一层 dirname）
- AudioPlayer 双 close 导致 PortAudio 崩溃

### 变更
- 项目全面更名为 RIShadowing
- build.py 一键构建（PyInstaller + Inno Setup + zip）
- 数据目录与程序目录分离（便携模式 / 安装模式双支持）
- 安装版可选择数据存储位置（AppData / 应用目录）
- 打包产物不再包含 AGENTS.md 和 .env.example
- 参考文本字体增大 12 -> 16

### 构建产物说明
| 产物 | 说明 | 大小 |
|------|------|------|
| Lite_Setup.exe | 安装向导版，需以管理员身份运行 | ~51 MB |
| Portable_Lite.zip | 便携版，首次启动自动下载 Vosk 模型 | ~58 MB |
| Portable_Full.zip | 便携版，内置 Vosk 模型，开箱即用 | ~97 MB |
