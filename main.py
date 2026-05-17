from src.app import ShadowingApp
from src.utils.config import init_config

if __name__ == "__main__":
    init_config()
    app = ShadowingApp()
    app.run()
