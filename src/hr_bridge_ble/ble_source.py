"""Talks to a heart rate strap with the host's own Bluetooth adapter."""

import asyncio

from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError

from .hr_parse import parse_measurement

HR_SERVICE = "0000180d-0000-1000-8000-00805f9b34fb"
HR_MEASUREMENT = "00002a37-0000-1000-8000-00805f9b34fb"

SCAN_SECONDS = 10.0
RETRY_SECONDS = 3.0


def matches(device, name):
    return not name or name.lower() in (device.name or "").lower()


async def scan(timeout=SCAN_SECONDS):
    """Every device advertising the standard heart rate service."""
    return await BleakScanner.discover(timeout=timeout, service_uuids=[HR_SERVICE])


async def find_strap(name=None, address=None, timeout=SCAN_SECONDS):
    if address:
        return await BleakScanner.find_device_by_address(address, timeout=timeout)
    for device in await scan(timeout):
        if matches(device, name):
            return device
    if not name:
        return None
    # Some straps keep the heart rate service out of their advertisement, so fall back to the name.
    for device in await BleakScanner.discover(timeout=timeout):
        if matches(device, name):
            return device
    return None


async def stream(device, on_reading, log):
    stopped = asyncio.Event()

    def handle(_characteristic, data):
        try:
            reading = parse_measurement(bytes(data))
        except ValueError as error:
            log("ignored packet: {}".format(error))
            return
        on_reading(reading)

    async with BleakClient(device, disconnected_callback=lambda _client: stopped.set()) as client:
        await client.start_notify(HR_MEASUREMENT, handle)
        log("subscribed")
        await stopped.wait()


def say_once(log, previous, message):
    """Keeps a retry loop from filling the log with the same line every few seconds."""
    if message != previous:
        log(message)
    return message


async def run(on_reading, log, name=None, address=None, scan_timeout=SCAN_SECONDS, retry_seconds=RETRY_SECONDS):
    said = None
    while True:
        try:
            device = await find_strap(name, address, scan_timeout)
            if device is None:
                said = say_once(log, said, "waiting for a heart rate strap")
                await asyncio.sleep(retry_seconds)
                continue
            said = None
            log("connecting to " + (device.name or device.address))
            await stream(device, on_reading, log)
            log("strap disconnected")
        except BleakError as error:
            said = say_once(log, said, "bluetooth error: {}".format(error))
        except asyncio.TimeoutError:
            said = say_once(log, said, "connection timed out")
        await asyncio.sleep(retry_seconds)
