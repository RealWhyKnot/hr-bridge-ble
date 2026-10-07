# hr-bridge-ble

Streams your heart rate into VRChat through the Bluetooth adapter your computer
already has. It connects to the chest strap directly and forwards each reading to
[hr-osc](https://github.com/kamyu1537/hr-osc), which turns them into OSC for VRChat.

```
chest strap  --BLE-->  hr-bridge-ble  --HTTP-->  hr-osc  --OSC-->  VRChat
```

You don't need a phone app or an account. If your PC's Bluetooth won't do, use
[hr-bridge-pico](https://github.com/RealWhyKnot/hr-bridge-pico), which puts a
Raspberry Pi Pico W between the strap and the PC instead.

## Compatibility

| | |
|---|---|
| Strap | Anything that advertises the standard heart rate service `0x180D`: CooSpo, Polar, Garmin, Wahoo, Magene, most gym chest straps and many watches |
| Windows | 10 or 11. Windows 10 needs `pip install "bleak<3"` |
| macOS | 10.15 or newer |
| Linux | BlueZ 5.55 or newer |
| Python | 3.10 or newer, or none at all if you use the Windows executable |
| Consumer | hr-osc, or anything that accepts an HTTP POST holding a bare number |

Bluetooth Classic headsets and ANT+ straps won't work. The strap has to speak
Bluetooth Low Energy, which almost every strap sold since about 2015 does.

## Install

On Windows you can skip Python. Download the zip from
[Releases](https://github.com/RealWhyKnot/hr-bridge-ble/releases), unpack it
anywhere and run `hr-bridge-ble.exe`.

On macOS and Linux:

```bash
pipx install https://github.com/RealWhyKnot/hr-bridge-ble/releases/latest/download/hr_bridge_ble-0.1.0-py3-none-any.whl
```

Or from a clone:

```bash
pip install -e .
```

## Running it

Put the strap on, then:

```bash
hr-bridge-ble
```

It scans, connects to the first heart rate strap it finds and posts every reading
to `http://127.0.0.1:8080`. If the strap isn't there yet it keeps scanning, and it
reconnects when the strap drops out. It also keeps running while hr-osc is closed.
Start them in either order.

To see what's in range:

```bash
hr-bridge-ble --list
```

```
C4:35:12:9A:0B:7E  H6M 29014
E8:11:03:44:21:AF  Polar H10
```

With more than one strap around, pick the one you mean:

```bash
hr-bridge-ble --name "H6M"
hr-bridge-ble --address C4:35:12:9A:0B:7E
```

`--name` matches any part of the advertised name and ignores case. `--address` is
exact and skips the scan, which makes startup faster.

## Setting up hr-osc

hr-osc uses a different heart rate source by default and ignores HTTP until you
switch it over. When the bridge works but VRChat doesn't get a heart rate, that's
nearly always why.

1. Open hr-osc.
2. On the **General** tab, set the service type to HTTP. The setting is on General.
   The HTTP tab only has the port.
3. On the HTTP tab, check that the port is `8080`.
4. Check that OSC points at `127.0.0.1:9000`, where VRChat listens.

If you'd rather edit the config file, it's at
`%APPDATA%\me.kamyu.hr-osc\data\config.json` on Windows. Set `service_type` to
`"http"`.

VRChat needs OSC switched on too: in the radial menu, Options, OSC, Enabled.

## Options

```
--url URL                 hr-osc HTTP receiver (default: http://127.0.0.1:8080)
--name NAME               only connect to a strap whose name contains this text
--address ADDRESS         connect straight to this Bluetooth address
--scan-timeout SECONDS    seconds to scan before retrying (default: 10.0)
--list                    list nearby heart rate straps and exit
--log LOG                 log file path
--no-log-file             log to the console only
--quiet                   do not echo the log to the console
--allow-multiple          skip the single-instance check
--version                 print the version and exit
```

The log is `bridge.log` in your platform's data directory:

- Windows: `%LOCALAPPDATA%\hr-bridge-ble\bridge.log`
- macOS: `~/Library/Application Support/hr-bridge-ble/bridge.log`
- Linux: `~/.local/state/hr-bridge-ble/bridge.log`

## Starting it automatically

Templates for all three platforms are in `packaging/` and in the `autostart`
folder of the release zip.

### Windows

Put a shortcut to `start-hidden.vbs` in the Startup folder (Win+R, then
`shell:startup`). In the release zip the script is in `autostart`, one folder
below `hr-bridge-ble.exe`. In a clone it's in `packaging`, one folder below the
`.venv`. It finds either one without being moved.

If you move the folder afterwards, the logon start breaks. The shortcut still
has the old path, and so does an editable install. Re-create the shortcut, and
in a clone run `pip install -e .` again.

### macOS

Edit `dev.whyknot.hr-bridge-ble.plist` to replace `USERNAME`, then:

```bash
cp packaging/dev.whyknot.hr-bridge-ble.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/dev.whyknot.hr-bridge-ble.plist
```

macOS asks for Bluetooth permission the first time. If the prompt never shows
up, grant it under System Settings, Privacy and Security, Bluetooth.

### Linux

```bash
cp packaging/hr-bridge-ble.service ~/.config/systemd/user/
systemctl --user enable --now hr-bridge-ble
```

## When something is wrong

Read the log first. It records every state change: what it connected to, the
first reading it saw, and every disconnect. If the same failure keeps happening
it's logged once instead of every few seconds. A log with no new lines means the
state hasn't changed.

### "waiting for a heart rate strap"

Most straps only advertise while they're against skin. Put it on, wet the
contacts and give it ten seconds, then run `--list` to check that the computer
can see it at all.

### The strap is visible but won't connect

A strap holds one connection at a time. Close any phone app, watch or bike
computer that's paired to it. On Windows, also make sure the strap isn't paired
in Settings, Bluetooth and devices. Leave heart rate straps unpaired for this.

### "No Bluetooth adapter found"

The adapter is off or missing. On Windows check Settings, Bluetooth and devices.
On Linux check `bluetoothctl show` and that the `bluetooth` service is running.
If the machine has no adapter, use
[hr-bridge-pico](https://github.com/RealWhyKnot/hr-bridge-pico).

### "no skin contact"

The strap is connected but says it isn't against skin. Those readings are wrong
and the bridge drops them. Wet the contact pads.

### hr-osc gets nothing

Check that the log says `streaming, first bpm ...`. If it does, the bridge is
working and hr-osc needs setting up. Go back to the hr-osc section above.

### Linux permission errors

Scanning normally works without root. If it doesn't, your user needs permission
to talk to BlueZ over D-Bus. Most distributions give a desktop session that by
default, and a bare container doesn't have it.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e . -r requirements-dev.txt
python -m ruff format --check .
python -m ruff check .
python -m unittest discover
```

The tests only use the standard library and mock the Bluetooth layer. They run
without any hardware.

`src/hr_bridge_ble/hr_parse.py` decodes the Bluetooth Heart Rate Measurement
characteristic: 8 or 16 bit rate, skin contact, energy expended and RR
intervals.

Releases are cut by pushing a `vYYYY.M.D.N` tag. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

GPL-3.0-or-later. See [LICENSE](LICENSE).
