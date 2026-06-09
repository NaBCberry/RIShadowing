import os, json, tempfile, sys
sys.path.insert(0, '.')

# Simulate frozen env
sys.frozen = True
sys.executable = r'D:\AI_Interpreter\AI_Interpreter.exe'

from src.utils.paths import get_app_dir, get_data_dir, get_env_path

app_dir = get_app_dir()
print(f'app_dir: {app_dir}')

# Create a mock config.json (like the installer would)
cfg_path = os.path.join(app_dir, 'config.json')
os.makedirs(app_dir, exist_ok=True)
with open(cfg_path, 'w') as f:
    f.write('{"data_dir": "%APPDATA%\\\\AI_Interpreter"}')

print(f'config written: {cfg_path}')

data_dir = get_data_dir()
print(f'data_dir: {data_dir}')
print(f'data_dir writable: {os.access(data_dir, os.W_OK)}')

env_path = get_env_path()
print(f'env_path: {env_path}')

import shutil
shutil.rmtree(app_dir, ignore_errors=True)
print('OK')
