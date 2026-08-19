import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from hr_bridge_ble.sink import HrOscSink

RECEIVED = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        RECEIVED.append(self.rfile.read(length))
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args):
        pass


class HrOscSinkTest(unittest.TestCase):
    def setUp(self):
        RECEIVED.clear()
        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(self.server.shutdown)
        self.url = "http://127.0.0.1:{}".format(self.server.server_address[1])

    def test_posts_the_bare_number(self):
        self.assertTrue(HrOscSink(self.url).send(72))
        self.assertEqual(RECEIVED, [b"72"])

    def test_coerces_to_an_integer(self):
        self.assertTrue(HrOscSink(self.url).send(72.9))
        self.assertEqual(RECEIVED, [b"72"])

    def test_reports_failure_when_nothing_is_listening(self):
        self.server.shutdown()
        self.assertFalse(HrOscSink(self.url, timeout=0.5).send(72))

    def test_unreachable_host_does_not_raise(self):
        self.assertFalse(HrOscSink("http://127.0.0.1:1", timeout=0.5).send(72))


if __name__ == "__main__":
    unittest.main()
