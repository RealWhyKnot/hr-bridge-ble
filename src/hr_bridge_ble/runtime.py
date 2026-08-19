"""Log file handling and a single-instance lock that works on every platform."""

import os
import sys
import time

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


def default_data_dir(app):
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_STATE_HOME") or os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, app)


def _ensure_parent(path):
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)


class Log:
    def __init__(self, path=None, echo=True):
        self.path = path
        self.echo = echo
        if path:
            _ensure_parent(path)

    def __call__(self, message):
        line = time.strftime("%Y-%m-%d %H:%M:%S ") + message
        if self.path:
            try:
                with open(self.path, "a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
            except OSError:
                pass
        if self.echo:
            print(line, flush=True)


class SingleInstance:
    """A lock the operating system drops when the holder dies, so a crash leaves nothing stale."""

    def __init__(self, path):
        self.path = path
        self._handle = None

    def acquire(self):
        _ensure_parent(self.path)
        handle = open(self.path, "a+")
        try:
            if sys.platform == "win32":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        self._handle = handle
        return True

    def release(self):
        if self._handle is None:
            return
        try:
            if sys.platform == "win32":
                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        self._handle.close()
        self._handle = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
