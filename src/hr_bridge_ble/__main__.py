"""Relays heart rate from a Bluetooth strap straight to hr-osc."""

import argparse
import asyncio
import os
import sys
import traceback

from bleak.exc import BleakError

from . import __version__
from .ble_source import SCAN_SECONDS, run, scan
from .runtime import Log, SingleInstance, default_data_dir
from .sink import DEFAULT_URL, HrOscSink

APP = "hr-bridge-ble"


def build_parser():
    parser = argparse.ArgumentParser(
        prog=APP,
        description="Relay heart rate from a Bluetooth chest strap or watch to hr-osc.",
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="hr-osc HTTP receiver (default: %(default)s)")
    parser.add_argument("--name", help="only connect to a strap whose advertised name contains this text")
    parser.add_argument("--address", help="connect straight to this Bluetooth address, skipping the name match")
    parser.add_argument(
        "--scan-timeout",
        type=float,
        default=SCAN_SECONDS,
        help="seconds to scan before retrying (default: %(default)s)",
    )
    parser.add_argument("--list", action="store_true", help="list nearby heart rate straps and exit")
    parser.add_argument("--log", help="log file path (default: bridge.log under the platform data directory)")
    parser.add_argument("--no-log-file", action="store_true", help="log to the console only")
    parser.add_argument("--quiet", action="store_true", help="do not echo the log to the console")
    parser.add_argument("--allow-multiple", action="store_true", help="skip the single-instance check")
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    return parser


async def list_straps(timeout):
    try:
        devices = await scan(timeout)
    except BleakError as error:
        print("Bluetooth is unavailable: {}".format(error))
        return 1
    if not devices:
        print("No heart rate straps found. Wear the strap and make sure nothing else is connected to it.")
        return 0
    for device in devices:
        print("{}  {}".format(device.address, device.name or "(unnamed)"))
    return 0


def build_handler(sink, log):
    state = {"fresh": True, "off_body": False}

    def on_reading(reading):
        if reading.contact is False:
            if not state["off_body"]:
                log("no skin contact")
                state["off_body"] = True
            return
        state["off_body"] = False
        if not reading.bpm:
            return
        if state["fresh"]:
            log("streaming, first bpm {}".format(reading.bpm))
            state["fresh"] = False
        sink.send(reading.bpm)

    return on_reading


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.list:
        return asyncio.run(list_straps(args.scan_timeout))

    data_dir = default_data_dir(APP)
    log_path = None if args.no_log_file else (args.log or os.path.join(data_dir, "bridge.log"))
    log = Log(log_path, echo=not args.quiet)
    lock = SingleInstance(os.path.join(data_dir, "instance.lock"))
    if not args.allow_multiple and not lock.acquire():
        log("another instance is already running")
        return 0

    on_reading = build_handler(HrOscSink(args.url), log)
    log("{} {} start".format(APP, __version__))
    try:
        asyncio.run(run(on_reading, log, name=args.name, address=args.address, scan_timeout=args.scan_timeout))
    except KeyboardInterrupt:
        log("stopped")
    except Exception:
        log("fatal:\n" + traceback.format_exc())
        raise
    finally:
        lock.release()
    return 0


if __name__ == "__main__":
    sys.exit(main())
