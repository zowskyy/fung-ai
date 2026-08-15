import ctypes
import sys


_INSTANCE_MUTEX = None


def _acquire_single_instance() -> bool:
    """Ensure only one fungai window runs at a time.

    This runs BEFORE importing PySide6 so the guard takes effect almost
    immediately after launch. Without it, users click the exe repeatedly while
    it starts and end up with many windows ("it keeps coming up").

    Returns True if this is the first/only instance.
    """
    if sys.platform != "win32":
        return True
    # use_last_error=True so GetLastError reflects the CreateMutexW call.
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    mutex = kernel32.CreateMutexW(None, 0, "Global\\fungai_single_instance")
    last_error = ctypes.get_last_error()
    global _INSTANCE_MUTEX
    _INSTANCE_MUTEX = mutex
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(mutex)
        _INSTANCE_MUTEX = None
        return False
    if not mutex:
        return False
    return True


if not _acquire_single_instance():
    sys.exit(0)

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.theme import ASCII_FUNGAI, apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("fungai")
    app.setOrganizationName("fungai")
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
