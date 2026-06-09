import os
import json
from src.utils.paths import get_config_path, get_env_path, get_data_dir

_DEFAULTS = {
    "audio": {
        "input_device": None,
        "output_device": None,
        "sample_rate": 16000,
        "block_size": 4000,
    },
    "vosk": {
        "model_path": None,
    },
    "tts": {
        "engine": "edge",
        "edge_tts_voice": "en-US-JennyNeural",
        "piper_model_path": None,
    },
    "asr": {
        "whisper_api_key": None,
        "whisper_endpoint": "https://api.openai.com/v1/audio/transcriptions",
    },
    "ui": {
        "language": "zh",
        "theme": "dark",
    },
    "training": {
        "default_language": "en",
        "difficulty_filter": "all",
        "countdown_seconds": 3.0,
    },
    "data_dir": "app",
}

_CONFIG_PATH = None
_ENV_PATH = None


def _ensure_paths():
    global _CONFIG_PATH, _ENV_PATH
    if _CONFIG_PATH is None:
        _CONFIG_PATH = get_config_path()
    if _ENV_PATH is None:
        _ENV_PATH = get_env_path()


def _generate_config_file(path, defaults):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(defaults, f, ensure_ascii=False, indent=2)
    print(f"[Config] generated {os.path.basename(path)}")


def _generate_env_file(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "# 在此填入 API 密钥\n"
            "# 获取方式见 README.md\n\n"
            "WHISPER_API_KEY=\n"
            "# EDGE_TTS 为免费服务，无需密钥\n"
        )
    print(f"[Config] generated .env")


def _load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Some installers write paths with single backslashes (invalid JSON escapes)
    # Fix by replacing single backslashes not followed by valid escapes with forward slashes
    content = content.replace("\\", "/")
    return json.loads(content)


def _load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip()
    return env


def init_config():
    _ensure_paths()
    if not os.path.exists(_CONFIG_PATH):
        _generate_config_file(_CONFIG_PATH, _DEFAULTS)
    if not os.path.exists(_ENV_PATH):
        _generate_env_file(_ENV_PATH)
    get_data_dir()


def get_config():
    _ensure_paths()
    config = dict(_DEFAULTS)
    if os.path.exists(_CONFIG_PATH):
        try:
            loaded = _load_config(_CONFIG_PATH)
            deep_merge(config, loaded)
        except Exception as e:
            print(f"[Config] load error: {e}, using defaults")
    return config


def get_env():
    _ensure_paths()
    return _load_env(_ENV_PATH) if os.path.exists(_ENV_PATH) else {}


def deep_merge(base, override):
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        else:
            base[key] = value
