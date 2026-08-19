import unittest

from hr_bridge_ble.hr_parse import parse_measurement


class ParseMeasurementTest(unittest.TestCase):
    def test_eight_bit_rate(self):
        reading = parse_measurement(b"\x00\x48")
        self.assertEqual(reading.bpm, 72)
        self.assertIsNone(reading.contact)
        self.assertIsNone(reading.energy_kj)
        self.assertEqual(reading.rr_intervals_ms, ())

    def test_sixteen_bit_rate(self):
        self.assertEqual(parse_measurement(b"\x01\x2c\x01").bpm, 300)

    def test_contact_is_unknown_when_the_strap_does_not_report_it(self):
        self.assertIsNone(parse_measurement(b"\x00\x48").contact)

    def test_contact_detected(self):
        self.assertIs(parse_measurement(b"\x06\x48").contact, True)

    def test_contact_supported_but_not_detected(self):
        self.assertIs(parse_measurement(b"\x04\x48").contact, False)

    def test_energy_expended(self):
        reading = parse_measurement(b"\x08\x48\xe8\x03")
        self.assertEqual(reading.bpm, 72)
        self.assertEqual(reading.energy_kj, 1000)

    def test_rr_intervals_are_converted_to_milliseconds(self):
        reading = parse_measurement(b"\x10\x3c\x00\x04")
        self.assertEqual(reading.bpm, 60)
        self.assertEqual(reading.rr_intervals_ms, (1000.0,))

    def test_several_rr_intervals(self):
        reading = parse_measurement(b"\x10\x3c\x00\x04\x00\x02")
        self.assertEqual(reading.rr_intervals_ms, (1000.0, 500.0))

    def test_energy_and_rr_together(self):
        reading = parse_measurement(b"\x18\x3c\xe8\x03\x00\x04")
        self.assertEqual(reading.bpm, 60)
        self.assertEqual(reading.energy_kj, 1000)
        self.assertEqual(reading.rr_intervals_ms, (1000.0,))

    def test_sixteen_bit_rate_with_rr(self):
        reading = parse_measurement(b"\x11\x2c\x01\x00\x04")
        self.assertEqual(reading.bpm, 300)
        self.assertEqual(reading.rr_intervals_ms, (1000.0,))

    def test_a_trailing_odd_byte_is_ignored(self):
        self.assertEqual(parse_measurement(b"\x10\x3c\x00\x04\x07").rr_intervals_ms, (1000.0,))

    def test_zero_is_reported_rather_than_hidden(self):
        self.assertEqual(parse_measurement(b"\x00\x00").bpm, 0)

    def test_empty_packet(self):
        with self.assertRaises(ValueError):
            parse_measurement(b"")

    def test_flags_only(self):
        with self.assertRaises(ValueError):
            parse_measurement(b"\x00")

    def test_sixteen_bit_rate_cut_short(self):
        with self.assertRaises(ValueError):
            parse_measurement(b"\x01\x2c")

    def test_energy_cut_short(self):
        with self.assertRaises(ValueError):
            parse_measurement(b"\x08\x48\xe8")


if __name__ == "__main__":
    unittest.main()
