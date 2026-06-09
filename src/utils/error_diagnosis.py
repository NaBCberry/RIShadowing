import sys
import io
import traceback
import re
import ctypes


ERROR_DATABASE = [
    {
        "code": "E001",
        "pattern": "ModuleNotFoundError|ImportError",
        "description": "Missing Python dependency",
        "solution": (
            "Reinstall dependencies:\n"
            "  1. Open terminal in project directory\n"
            "  2. Run: .venv\\Scripts\\pip install -r requirements.txt\n"
            "  3. If venv is broken, recreate it:\n"
            "     python -m venv .venv\n"
            "     .venv\\Scripts\\pip install -r requirements.txt"
        ),
    },
    {
        "code": "E002",
        "pattern": "PortAudio|sounddevice.*error|OSError.*audio|Pa_Initialize",
        "description": "Audio device or PortAudio library error",
        "solution": (
            "Audio backend failed to initialize:\n"
            "  1. Check that your microphone and speakers are connected\n"
            "  2. Try restarting your computer\n"
            "  3. Reinstall sounddevice:\n"
            "     .venv\\Scripts\\pip uninstall sounddevice -y\n"
            "     .venv\\Scripts\\pip install sounddevice\n"
            "  4. If using Bluetooth audio, switch to wired/built-in"
        ),
    },
    {
        "code": "E003",
        "pattern": "config\\.json|config.*corrupt|json.*decode",
        "description": "Configuration file corrupted",
        "solution": (
            "Delete and regenerate config.json:\n"
            "  1. Delete the file: del config.json\n"
            "  2. Restart the application — it will auto-generate a fresh config\n"
            "  3. Your previous settings will be reset to defaults"
        ),
    },
    {
        "code": "E004",
        "pattern": "PermissionError|permission denied",
        "description": "File permission denied",
        "solution": (
            "The application cannot access a required file:\n"
            "  1. Check that the project directory is not read-only\n"
            "  2. Close other programs that might lock files (e.g. audio editors)\n"
            "  3. Run as Administrator if needed"
        ),
    },
    {
        "code": "E005",
        "pattern": "Vosk.*model.*not found|No Vosk model",
        "description": "Vosk speech model not downloaded",
        "solution": (
            "The app will prompt you to download the model automatically.\n"
            "If auto-download fails:\n"
            "  1. Visit https://alphacephei.com/vosk/models\n"
            "  2. Download vosk-model-small-en-us-0.15.zip\n"
            "  3. Extract it to the project root directory"
        ),
    },
    {
        "code": "E006",
        "pattern": "MemoryError|numpy.*memory|out of memory",
        "description": "Out of memory",
        "solution": (
            "The audio file or model is too large for available memory:\n"
            "  1. Close other applications to free RAM\n"
            "  2. Use shorter audio files\n"
            "  3. Use the small Vosk model (vosk-model-small-en-us-0.15)"
        ),
    },
    {
        "code": "E007",
        "pattern": "TclError|_tkinter\\.TclError",
        "description": "GUI display error",
        "solution": (
            "The graphical interface failed to initialize:\n"
            "  1. Ensure you have a display/monitor connected\n"
            "  2. Try reinstalling customtkinter:\n"
            "     .venv\\Scripts\\pip uninstall customtkinter -y\n"
            "     .venv\\Scripts\\pip install customtkinter\n"
            "  3. If on remote/headless server, GUI is not supported"
        ),
    },
    {
        "code": "E999",
        "pattern": None,
        "description": "Unhandled application error",
        "solution": (
            "An unexpected error occurred:\n"
            "  1. Copy the console output below\n"
            "  2. Check the project issue tracker or report a new issue\n"
            "  3. Try restarting the application"
        ),
    },
]


class ConsoleCapture:
    def __init__(self):
        self._buffer = io.StringIO()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
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
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

    def write(self, data):
        self._original_stdout.write(data)
        self._buffer.write(data)

    def flush(self):
        self._original_stdout.flush()

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
    root.title("STARTUP ERROR")
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
