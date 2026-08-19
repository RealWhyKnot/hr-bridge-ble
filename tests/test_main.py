import unittest

from hr_bridge_ble.__main__ import build_handler, build_parser
from hr_bridge_ble.hr_parse import Reading


class FakeSink:
    def __init__(self):
        self.sent = []

    def send(self, bpm):
        self.sent.append(bpm)
        return True


def reading(bpm, contact=None):
    return Reading(bpm, contact, None, ())


class HandlerTest(unittest.TestCase):
    def setUp(self):
        self.sink = FakeSink()
        self.lines = []
        self.handle = build_handler(self.sink, self.lines.append)

    def test_forwards_a_reading(self):
        self.handle(reading(72))
        self.assertEqual(self.sink.sent, [72])

    def test_announces_only_the_first_reading(self):
        self.handle(reading(72))
        self.handle(reading(73))
        self.assertEqual(self.lines, ["streaming, first bpm 72"])

    def test_drops_readings_taken_off_the_body(self):
        self.handle(reading(72, contact=False))
        self.assertEqual(self.sink.sent, [])
        self.assertEqual(self.lines, ["no skin contact"])

    def test_does_not_repeat_the_contact_warning(self):
        self.handle(reading(72, contact=False))
        self.handle(reading(72, contact=False))
        self.assertEqual(self.lines, ["no skin contact"])

    def test_warns_again_after_contact_returns(self):
        self.handle(reading(72, contact=False))
        self.handle(reading(72, contact=True))
        self.handle(reading(72, contact=False))
        self.assertEqual(self.lines.count("no skin contact"), 2)

    def test_forwards_when_contact_is_unknown(self):
        self.handle(reading(72, contact=None))
        self.assertEqual(self.sink.sent, [72])

    def test_drops_zero(self):
        self.handle(reading(0))
        self.assertEqual(self.sink.sent, [])


class ParserTest(unittest.TestCase):
    def test_defaults(self):
        args = build_parser().parse_args([])
        self.assertEqual(args.url, "http://127.0.0.1:8080")
        self.assertIsNone(args.name)
        self.assertFalse(args.list)

    def test_overrides(self):
        args = build_parser().parse_args(["--url", "http://127.0.0.1:9999", "--name", "H6M", "--scan-timeout", "4"])
        self.assertEqual(args.url, "http://127.0.0.1:9999")
        self.assertEqual(args.name, "H6M")
        self.assertEqual(args.scan_timeout, 4.0)


if __name__ == "__main__":
    unittest.main()
