import unittest
from unittest import mock

from hr_bridge_ble import ble_source


class FakeDevice:
    def __init__(self, name, address="AA:BB:CC:DD:EE:FF"):
        self.name = name
        self.address = address


class MatchesTest(unittest.TestCase):
    def test_no_filter_matches_anything(self):
        self.assertTrue(ble_source.matches(FakeDevice("H6M 29014"), None))

    def test_match_is_case_insensitive_and_partial(self):
        self.assertTrue(ble_source.matches(FakeDevice("H6M 29014"), "h6m"))

    def test_rejects_a_different_strap(self):
        self.assertFalse(ble_source.matches(FakeDevice("Polar H10"), "h6m"))

    def test_unnamed_device_never_matches_a_filter(self):
        self.assertFalse(ble_source.matches(FakeDevice(None), "h6m"))


class FindStrapTest(unittest.IsolatedAsyncioTestCase):
    def scanner(self, discover=None, by_address=None):
        patcher = mock.patch.object(ble_source, "BleakScanner")
        scanner = patcher.start()
        self.addCleanup(patcher.stop)
        scanner.discover = mock.AsyncMock(side_effect=discover or [[]])
        scanner.find_device_by_address = mock.AsyncMock(return_value=by_address)
        return scanner

    async def test_an_address_skips_scanning(self):
        device = FakeDevice("H6M")
        scanner = self.scanner(by_address=device)
        self.assertIs(await ble_source.find_strap(address=device.address), device)
        scanner.discover.assert_not_awaited()

    async def test_takes_the_first_strap_when_no_name_is_given(self):
        first = FakeDevice("H6M 29014")
        self.scanner(discover=[[first, FakeDevice("Polar H10")]])
        self.assertIs(await ble_source.find_strap(), first)

    async def test_picks_the_named_strap(self):
        wanted = FakeDevice("Polar H10")
        self.scanner(discover=[[FakeDevice("H6M 29014"), wanted]])
        self.assertIs(await ble_source.find_strap(name="polar"), wanted)

    async def test_falls_back_to_an_unfiltered_scan_for_a_named_strap(self):
        wanted = FakeDevice("Polar H10")
        scanner = self.scanner(discover=[[], [wanted]])
        self.assertIs(await ble_source.find_strap(name="polar"), wanted)
        self.assertEqual(scanner.discover.await_count, 2)

    async def test_no_fallback_scan_without_a_name(self):
        scanner = self.scanner(discover=[[]])
        self.assertIsNone(await ble_source.find_strap())
        self.assertEqual(scanner.discover.await_count, 1)

    async def test_returns_none_when_the_named_strap_is_absent(self):
        self.scanner(discover=[[], [FakeDevice("H6M 29014")]])
        self.assertIsNone(await ble_source.find_strap(name="polar"))


class SayOnceTest(unittest.TestCase):
    def test_says_a_new_message(self):
        lines = []
        self.assertEqual(ble_source.say_once(lines.append, None, "down"), "down")
        self.assertEqual(lines, ["down"])

    def test_swallows_a_repeat(self):
        lines = []
        ble_source.say_once(lines.append, "down", "down")
        self.assertEqual(lines, [])

    def test_says_it_again_once_something_else_happened(self):
        lines = []
        ble_source.say_once(lines.append, "up", "down")
        self.assertEqual(lines, ["down"])


class Stop(Exception):
    """Breaks out of the retry loop, which otherwise runs forever by design."""


class RunTest(unittest.IsolatedAsyncioTestCase):
    async def drive(self, outcomes):
        lines = []
        remaining = list(outcomes)

        async def find(*_args, **_kwargs):
            if not remaining:
                raise Stop
            outcome = remaining.pop(0)
            if isinstance(outcome, Exception):
                raise outcome
            return outcome

        with mock.patch.object(ble_source, "find_strap", find):
            with self.assertRaises(Stop):
                await ble_source.run(lambda _reading: None, lines.append, retry_seconds=0)
        return lines

    async def test_logs_a_missing_strap_once(self):
        lines = await self.drive([None, None, None])
        self.assertEqual(lines, ["waiting for a heart rate strap"])

    async def test_logs_a_missing_adapter_once(self):
        error = ble_source.BleakError("No Bluetooth adapter found")
        lines = await self.drive([error, error, error])
        self.assertEqual(lines, ["bluetooth error: No Bluetooth adapter found"])

    async def test_reports_a_change_of_state(self):
        lines = await self.drive([None, ble_source.BleakError("adapter went away"), None])
        self.assertEqual(
            lines,
            [
                "waiting for a heart rate strap",
                "bluetooth error: adapter went away",
                "waiting for a heart rate strap",
            ],
        )


if __name__ == "__main__":
    unittest.main()
