import sys
import io
import traceback
import re
import ctypes


ERROR_DATABASE = [
    {
        "code": "E001",
        "pattern": "ModuleNotFoundError|ImportError",
        "description": "缺少 Python 依赖包",
        "solution": (
            "请重新安装依赖：\n"
            "  1. 在项目目录下打开终端\n"
            "  2. 运行：.venv\\Scripts\\pip install -r requirements.txt\n"
            "  3. 如果虚拟环境损坏，请重建：\n"
            "     python -m venv .venv\n"
            "     .venv\\Scripts\\pip install -r requirements.txt"
        ),
    },
    {
        "code": "E002",
        "pattern": "PortAudio|sounddevice.*error|OSError.*audio|Pa_Initialize",
        "description": "音频设备或 PortAudio 驱动错误",
        "solution": (
            "音频后端初始化失败：\n"
            "  1. 检查麦克风和扬声器是否正确连接\n"
            "  2. 尝试重启电脑\n"
            "  3. 重新安装 sounddevice：\n"
            "     .venv\\Scripts\\pip uninstall sounddevice -y\n"
            "     .venv\\Scripts\\pip install sounddevice\n"
            "  4. 如果使用蓝牙音频设备，请切换到有线或内置设备"
        ),
    },
    {
        "code": "E003",
        "pattern": "config\\.json|config.*corrupt|json.*decode",
        "description": "配置文件损坏",
        "solution": (
            "请删除并重新生成 config.json：\n"
            "  1. 删除文件：del config.json\n"
            "  2. 重启程序 — 将自动生成全新配置文件\n"
            "  3. 之前的设置将恢复为默认值"
        ),
    },
    {
        "code": "E004",
        "pattern": "PermissionError|permission denied",
        "description": "文件权限不足",
        "solution": (
            "程序无法访问所需文件：\n"
            "  1. 检查项目目录是否被设为只读\n"
            "  2. 关闭可能占用文件的其他程序（如音频编辑器）\n"
            "  3. 如有必要，以管理员身份运行"
        ),
    },
    {
        "code": "E005",
        "pattern": "Vosk.*model.*not found|No Vosk model",
        "description": "Vosk 语音模型未下载",
        "solution": (
            "程序启动时会自动弹出下载对话框。\n"
            "如果自动下载失败：\n"
            "  1. 访问 https://alphacephei.com/vosk/models\n"
            "  2. 下载 vosk-model-small-en-us-0.15.zip\n"
            "  3. 解压到项目根目录"
        ),
    },
    {
        "code": "E006",
        "pattern": "MemoryError|numpy.*memory|out of memory",
        "description": "内存不足",
        "solution": (
            "音频文件或模型超出可用内存：\n"
            "  1. 关闭其他应用程序释放内存\n"
            "  2. 使用较短的音频文件\n"
            "  3. 使用小型 Vosk 模型 (vosk-model-small-en-us-0.15)"
        ),
    },
    {
        "code": "E007",
        "pattern": "TclError|_tkinter\\.TclError",
        "description": "图形界面显示异常",
        "solution": (
            "图形界面初始化失败：\n"
            "  1. 确保已连接显示器\n"
            "  2. 尝试重新安装 customtkinter：\n"
            "     .venv\\Scripts\\pip uninstall customtkinter -y\n"
            "     .venv\\Scripts\\pip install customtkinter\n"
            "  3. 远程/无头服务器不支持 GUI"
        ),
    },
    {
        "code": "E999",
        "pattern": None,
        "description": "未预期的程序错误",
        "solution": (
            "发生了未预期的错误：\n"
            "  1. 请复制下方的控制台输出\n"
            "  2. 查看项目问题追踪或提交新 issue\n"
            "  3. 尝试重启程序"
        ),
    },
]


class ConsoleCapture:
    def __init__(self):
        self._buffer = io.StringIO()
        self._original_stdout = sys.stdout if sys.stdout else None
        self._original_stderr = sys.stderr if sys.stderr else None
        self._active = False

    def start(self):
        if self._active:
            return
        self._active = True
        sys.stdout = self
        sys.stderr = self

    def stop(self):
        if not self._active:
            return
        self._active = False
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
        if self._original_stderr is not None:
            sys.stderr = self._original_stderr

    def write(self, data):
        if self._original_stdout:
            try:
                self._original_stdout.write(data)
            except Exception:
                pass
        self._buffer.write(data)

    def flush(self):
        if self._original_stdout:
            try:
                self._original_stdout.flush()
            except Exception:
                pass

    def get_output(self, tail_lines=20):
        lines = self._buffer.getvalue().splitlines()
        if len(lines) <= tail_lines:
            return "\n".join(lines)
        return "...\n" + "\n".join(lines[-tail_lines:])


_capture = ConsoleCapture()


def start_capture():
    _capture.start()


def stop_capture():
    _capture.stop()


def get_console_tail(lines=20):
    return _capture.get_output(lines)


def diagnose(exc_type, exc_value, exc_tb) -> dict:
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

    for entry in ERROR_DATABASE:
        pattern = entry["pattern"]
        if pattern is None:
            continue
        if re.search(pattern, tb_text, re.IGNORECASE):
            return {
                "code": entry["code"],
                "description": entry["description"],
                "solution": entry["solution"],
                "traceback": tb_text,
                "console": get_console_tail(),
            }

    fallback = ERROR_DATABASE[-1]
    return {
        "code": fallback["code"],
        "description": fallback["description"],
        "solution": fallback["solution"],
        "traceback": tb_text,
        "console": get_console_tail(),
    }


def show_error_dialog(diagnosis: dict):
    try:
        import tkinter as tk
        from tkinter import messagebox, scrolledtext
        import customtkinter as ctk
    except ImportError:
        _fallback_print(diagnosis)
        return

    ctk.set_appearance_mode("dark")

    root = ctk.CTk()
    root.title("ERROR DIAGNOSIS / 错误诊断")
    root.geometry("680x520")
    root.configure(fg_color="#08080f")

    header = tk.Frame(root, bg="#08080f", height=44)
    header.pack(fill=tk.X)
    header.pack_propagate(False)

    tk.Label(
        header,
        text=f"  ERROR {diagnosis['code']}: {diagnosis['description']}",
        font=("Microsoft YaHei", 12, "bold"),
        bg="#08080f", fg="#ff4455",
        anchor="w",
    ).pack(fill=tk.X, padx=12, pady=10)

    sep = tk.Frame(root, bg="#ff6b35", height=2)
    sep.pack(fill=tk.X)

    body = ctk.CTkFrame(root, fg_color="transparent")
    body.pack(fill=tk.BOTH, expand=True, padx=14, pady=(10, 4))

    tk.Label(
        body,
        text="SOLUTION / 修复方案:",
        font=("Microsoft YaHei", 11, "bold"),
        bg="#08080f", fg="#00d4ff",
        anchor="w",
    ).pack(fill=tk.X)

    sol_text = ctk.CTkTextbox(
        body, height=110,
        font=("Consolas", 11),
        fg_color="#1a1a30",
        text_color="#e8e8f4",
        border_width=1,
        border_color="#555572",
        corner_radius=2,
        wrap="word",
    )
    sol_text.pack(fill=tk.X, pady=(4, 8))
    sol_text.insert("1.0", diagnosis["solution"])
    sol_text.configure(state="disabled")

    tk.Label(
        body,
        text="CONSOLE OUTPUT / 控制台输出:",
        font=("Microsoft YaHei", 11, "bold"),
        bg="#08080f", fg="#c9a96e",
        anchor="w",
    ).pack(fill=tk.X)

    console_text = ctk.CTkTextbox(
        body,
        font=("Consolas", 10),
        fg_color="#1a1a30",
        text_color="#8888a8",
        border_width=1,
        border_color="#555572",
        corner_radius=2,
        wrap="word",
    )
    console_text.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
    console_text.insert("1.0", diagnosis.get("console", ""))
    console_text.configure(state="disabled")

    btn = ctk.CTkButton(
        body, text="CLOSE / 关闭",
        font=("Microsoft YaHei", 11, "bold"),
        fg_color="#ff6b35",
        hover_color="#ff8855",
        text_color="#08080f",
        corner_radius=2,
        width=160, height=36,
        command=root.destroy,
    )
    btn.pack(pady=(10, 0))

    root.mainloop()


def _fallback_print(diagnosis):
    print(f"\n{'='*60}", file=sys.stderr)
    print(f" ERROR {diagnosis['code']}: {diagnosis['description']}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    print(f"\nSOLUTION:\n{diagnosis['solution']}", file=sys.stderr)
    print(f"\nCONSOLE OUTPUT:\n{diagnosis.get('console', '')}", file=sys.stderr)
    print(f"\nTRACEBACK:\n{diagnosis['traceback']}", file=sys.stderr)
