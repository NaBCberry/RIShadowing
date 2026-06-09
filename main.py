from src.utils.config import init_config
from src.utils.error_diagnosis import (
    start_capture, stop_capture, diagnose, show_error_dialog,
)
import traceback

if __name__ == "__main__":
    start_capture()
    try:
        init_config()
        from src.app import ShadowingApp
        app = ShadowingApp()
        stop_capture()
        app.run()
    except Exception as e:
        stop_capture()
        traceback.print_exc()
        diagnosis = diagnose(type(e), e, e.__traceback__)
        show_error_dialog(diagnosis)
