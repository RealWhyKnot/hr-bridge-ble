"""Decodes the Bluetooth Heart Rate Measurement characteristic, 0x2A37."""

import struct
from typing import NamedTuple, Optional, Tuple

UINT16_FORMAT = 0x01
CONTACT_DETECTED = 0x02
CONTACT_SUPPORTED = 0x04
ENERGY_PRESENT = 0x08
RR_PRESENT = 0x10

RR_UNITS_PER_SECOND = 1024.0


class Reading(NamedTuple):
    bpm: int
    contact: Optional[bool]
    energy_kj: Optional[int]
    rr_intervals_ms: Tuple[float, ...]


def parse_measurement(data):
    """Raises ValueError when the packet is shorter than its own flags claim."""
    if len(data) < 2:
        raise ValueError("packet holds {} bytes, expected at least 2".format(len(data)))
    flags = data[0]
    offset = 1
    if flags & UINT16_FORMAT:
        if len(data) < offset + 2:
            raise ValueError("packet declares a 16 bit rate but ends after {} bytes".format(len(data)))
        bpm = struct.unpack_from("<H", data, offset)[0]
        offset += 2
    else:
        bpm = data[offset]
        offset += 1
    contact = bool(flags & CONTACT_DETECTED) if flags & CONTACT_SUPPORTED else None
    energy = None
    if flags & ENERGY_PRESENT:
        if len(data) < offset + 2:
            raise ValueError("packet declares energy expended but ends after {} bytes".format(len(data)))
        energy = struct.unpack_from("<H", data, offset)[0]
        offset += 2
    intervals = []
    if flags & RR_PRESENT:
        while offset + 2 <= len(data):
            raw = struct.unpack_from("<H", data, offset)[0]
            intervals.append(raw * 1000.0 / RR_UNITS_PER_SECOND)
            offset += 2
    return Reading(bpm, contact, energy, tuple(intervals))
