"""Sends readings to hr-osc's HTTP receiver."""

import urllib.request

DEFAULT_URL = "http://127.0.0.1:8080"
DEFAULT_TIMEOUT = 2.0


class HrOscSink:
    def __init__(self, url=DEFAULT_URL, timeout=DEFAULT_TIMEOUT):
        self.url = url
        self.timeout = timeout

    def send(self, bpm):
        """Returns False when hr-osc is unreachable, which is normal while it is closed."""
        request = urllib.request.Request(self.url, data=str(int(bpm)).encode("ascii"), method="POST")
        try:
            urllib.request.urlopen(request, timeout=self.timeout).read()
        except OSError:
            return False
        return True
