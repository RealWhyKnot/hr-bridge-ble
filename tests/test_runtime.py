import os
import subprocess
import sys
import tempfile
import unittest

from hr_bridge_ble.runtime import Log, SingleInstance, default_data_dir

HOLDER = (
    "import sys\n"
    "from hr_bridge_ble.runtime import SingleInstance\n"
    "print('acquired' if SingleInstance(sys.argv[1]).acquire() else 'blocked')\n"
)


def acquire_in_child(path):
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(entry for entry in sys.path if entry))
    result = subprocess.run(
        [sys.executable, "-c", HOLDER, path],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class SingleInstanceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, "nested", "instance.lock")

    def test_acquires_when_free(self):
        lock = SingleInstance(self.path)
        self.assertTrue(lock.acquire())
        lock.release()

    def test_blocks_a_second_process(self):
        lock = SingleInstance(self.path)
        self.assertTrue(lock.acquire())
        try:
            self.assertEqual(acquire_in_child(self.path), "blocked")
        finally:
            lock.release()

    def test_frees_the_lock_on_release(self):
        lock = SingleInstance(self.path)
        self.assertTrue(lock.acquire())
        lock.release()
        self.assertEqual(acquire_in_child(self.path), "acquired")

    def test_release_without_acquire_is_harmless(self):
        SingleInstance(self.path).release()


class LogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_writes_a_timestamped_line(self):
        path = os.path.join(self.tmp.name, "nested", "bridge.log")
        Log(path, echo=False)("hello")
        with open(path, encoding="utf-8") as handle:
            line = handle.read().strip()
        self.assertTrue(line.endswith(" hello"))
        self.assertRegex(line, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} ")

    def test_appends(self):
        path = os.path.join(self.tmp.name, "bridge.log")
        log = Log(path, echo=False)
        log("one")
        log("two")
        with open(path, encoding="utf-8") as handle:
            self.assertEqual(len(handle.read().strip().splitlines()), 2)

    def test_survives_an_unwritable_path(self):
        log = Log(self.tmp.name, echo=False)
        log("the log path is a directory")

    def test_no_path_means_no_file(self):
        Log(None, echo=False)("nowhere")
        self.assertEqual(os.listdir(self.tmp.name), [])


class DataDirTest(unittest.TestCase):
    def test_is_absolute_and_named_after_the_app(self):
        path = default_data_dir("hr-bridge-ble")
        self.assertTrue(os.path.isabs(path))
        self.assertTrue(path.endswith("hr-bridge-ble"))


if __name__ == "__main__":
    unittest.main()
