import os
import sys


def get_app_dir() -> str:
    """返回应用程序主目录（exe 所在目录或项目根目录）"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_data_dir() -> str:
    """返回用户数据目录。

    优先级：
    1. config.json 中 data_dir 字段的值
    2. 若 data_dir 不存在（首次启动），默认 = app 目录（便携模式）
    """
    app_dir = get_app_dir()
    cfg_path = os.path.join(app_dir, "config.json")

    data_dir = None
    if os.path.isfile(cfg_path):
        try:
            import json
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            raw = cfg.get("data_dir")
            if raw:
                data_dir = _resolve_data_dir(raw, app_dir)
        except Exception:
            pass

    if data_dir is None:
        data_dir = app_dir

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_config_path() -> str:
    """config.json 始终在 app 目录（安装版由安装程序写入，便携版用户直接编辑）"""
    return os.path.join(get_app_dir(), "config.json")


def get_env_path() -> str:
    """.env 在数据目录（安装版中 app 目录不可写）"""
    return os.path.join(get_data_dir(), ".env")


def get_db_path() -> str:
    """materials.db 在数据目录"""
    return os.path.join(get_data_dir(), "materials.db")


def get_vosk_model_dir() -> str:
    """Vosk 模型在数据目录"""
    return get_data_dir()


def _resolve_data_dir(raw: str, app_dir: str) -> str:
    raw = raw.strip()
    if raw.lower() == "app":
        return app_dir
    if raw.upper().startswith("%APPDATA%"):
        resolved = os.path.expandvars(raw)
        return resolved
    if os.path.isabs(raw):
        return raw
    return None
