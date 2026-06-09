import os
import zipfile
import requests
import shutil


VOSK_MODELS = {
    "small-en": {
        "name": "vosk-model-small-en-us-0.15",
        "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
        "size_mb": 40,
        "description": "Small English (~40MB, Recommended)",
    },
    "en": {
        "name": "vosk-model-en-us-0.22",
        "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
        "size_mb": 1800,
        "description": "Large English (~1.8GB, High Accuracy)",
    },
}


def download_model(model_key: str, extract_dir: str, progress_callback=None) -> str:
    info = VOSK_MODELS.get(model_key)
    if not info:
        raise ValueError(f"Unknown model: {model_key}")

    zip_path = os.path.join(extract_dir, f"{info['name']}.zip")
    model_dir = os.path.join(extract_dir, info["name"])

    if os.path.isdir(model_dir):
        conf = os.path.join(model_dir, "conf", "model.conf")
        mdl = os.path.join(model_dir, "am", "final.mdl")
        if os.path.isfile(conf) and os.path.isfile(mdl):
            if progress_callback:
                progress_callback("already_downloaded", 100, model_dir)
            return model_dir

    _download_file(info["url"], zip_path, progress_callback)
    _extract_zip(zip_path, extract_dir, progress_callback)

    try:
        os.remove(zip_path)
    except Exception:
        pass

    if progress_callback:
        progress_callback("complete", 100, model_dir)

    return model_dir


def _download_file(url: str, dest: str, progress_callback=None):
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))
    downloaded = 0

    with open(dest, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if progress_callback and total > 0:
                pct = int(downloaded * 100 / total)
                progress_callback("downloading", pct, None)


def _extract_zip(zip_path: str, dest_dir: str, progress_callback=None):
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        total = len(names)
        for i, name in enumerate(names):
            zf.extract(name, dest_dir)
            if progress_callback:
                pct = int((i + 1) * 100 / total)
                progress_callback("extracting", pct, None)

    if progress_callback:
        progress_callback("complete", 100, None)
