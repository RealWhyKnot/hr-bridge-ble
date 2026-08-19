# hr-bridge-ble

Streams your heart rate into VRChat using the Bluetooth adapter your computer
already has. It connects to the chest strap directly and forwards each reading to
[hr-osc](https://github.com/kamyu1537/hr-osc), which turns them into OSC for VRChat.

```
chest strap  --BLE-->  hr-bridge-ble  --HTTP-->  hr-osc  --OSC-->  VRChat
```

No extra hardware, no phone app in the middle, no account anywhere. If your PC
has no usable Bluetooth, use [hr-bridge-pico](https://github.com/RealWhyKnot/hr-bridge-pico),
which puts a Raspberry Pi Pico W in front of the strap instead.

## Compatibility

| | |
|---|---|
| Strap | Anything that advertises the standard heart rate service `0x180D`: CooSpo, Polar, Garmin, Wahoo, Magene, most gym chest straps and many watches |
| Windows | 10 or 11. Windows 10 needs `pip install "bleak<3"` |
| macOS | 10.15 or newer |
| Linux | BlueZ 5.55 or newer |
| Python | 3.10 or newer, or none at all if you use the Windows executable |
| Consumer | hr-osc, or anything that accepts an HTTP POST holding a bare number |

Bluetooth Classic headsets and ANT+ straps will not work. The strap has to speak
Bluetooth Low Energy, which almost every strap sold since about 2015 does.

## Install

### Windows, no Python

Download the zip from [Releases](https://github.com/RealWhyKnot/hr-bridge-ble/releases),
unpack it anywhere, and run `hr-bridge-ble.exe`.

### macOS and Linux

```bash
pipx install https://github.com/RealWhyKnot/hr-bridge-ble/releases/latest/download/hr_bridge_ble-0.1.0-py3-none-any.whl
```

Or from a clone:

```bash
pip install -e .
```

## Running it

Wear the strap, then:

```bash
hr-bridge-ble
```

It scans, connects to the first heart rate strap it finds, and posts every
reading to `http://127.0.0.1:8080`. It keeps scanning if the strap is not there
yet, reconnects when the strap drops out, and keeps running if hr-osc is closed,
so start order does not matter.

To see what is in range:

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

hr-osc defaults to a different heart rate source, so it ignores the bridge until
you tell it to listen for HTTP. This is the single most common reason for a
working bridge showing nothing.

1. Open hr-osc.
2. On the **General** tab, set the service type to **HTTP**. It is on General, not
   on the HTTP tab, which only holds the port.
3. On the **HTTP** tab, confirm the port is `8080`.
4. Check that OSC is pointed at `127.0.0.1:9000`, which is where VRChat listens.

The config file is at `%APPDATA%\me.kamyu.hr-osc\data\config.json` on Windows if
you would rather edit it directly. The field is `service_type` and it must be
`"http"`.

VRChat also needs OSC switched on: in the radial menu, Options, OSC, Enabled.

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

The log is written to `bridge.log` under your platform's data directory:

- Windows: `%LOCALAPPDATA%\hr-bridge-ble\bridge.log`
- macOS: `~/Library/Application Support/hr-bridge-ble/bridge.log`
- Linux: `~/.local/state/hr-bridge-ble/bridge.log`

## Starting it automatically

Templates for all three platforms are in `packaging/`, and in the `autostart`
folder of the release zip.

**Windows.** Copy `start-hidden.vbs` into the folder that holds
`hr-bridge-ble.exe`, or the folder that holds `.venv` if you installed from a
clone, then put a shortcut to it in the Startup folder. Press Win+R and enter
`shell:startup` to open that folder. The script works out its own location, so
you can move the folder later without breaking it.

**macOS.** Edit `dev.whyknot.hr-bridge-ble.plist` to replace `USERNAME`, then:

```bash
cp packaging/dev.whyknot.hr-bridge-ble.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/dev.whyknot.hr-bridge-ble.plist
```

macOS will ask for Bluetooth permission the first time. If you never see the
prompt, grant it under System Settings, Privacy and Security, Bluetooth.

**Linux.**

```bash
cp packaging/hr-bridge-ble.service ~/.config/systemd/user/
systemctl --user enable --now hr-bridge-ble
```

## When something is wrong

**Read the log first.** It records every state change: what it connected to, the
first reading it saw, and every disconnect. Repeated failures are logged once
rather than every few seconds, so a quiet log means nothing has changed.

**"waiting for a heart rate strap".** Most straps only advertise while worn
against skin. Put it on, moisten the contacts, and give it ten seconds. Run
`--list` to confirm the computer can see it at all.

**The strap is visible but will not connect.** A strap can only hold one
connection. Close any phone app, watch, or bike computer that is paired to it.
On Windows, also check that the strap is not paired in Settings, Bluetooth and
devices; heart rate straps should be left unpaired for this.

**"No Bluetooth adapter found".** The adapter is off or absent. On Windows check
Settings, Bluetooth and devices. On Linux check `bluetoothctl show` and that the
`bluetooth` service is running. If the machine genuinely has no adapter, use
[hr-bridge-pico](https://github.com/RealWhyKnot/hr-bridge-pico).

**"no skin contact".** The strap is connected but reporting that it is not
against skin, so the readings are meaningless and are dropped. Moisten the
contact pads.

**Nothing appears in hr-osc.** Confirm the log says `streaming, first bpm ...`.
If it does, the bridge is working and the problem is in hr-osc's configuration;
go back to the hr-osc section above.

**Linux permission errors.** Scanning normally works without root. If it does
not, your user needs to be allowed to talk to BlueZ over D-Bus; on most
distributions that is automatic for a desktop session and missing in a bare
container.

## Development

```bash
python -m venv .venv
.venv/bin/pip install -e . -r requirements-dev.txt
python -m ruff format --check .
python -m ruff check .
python -m unittest discover
```

Tests use only the standard library, mock out the Bluetooth layer, and never
touch hardware, so they run anywhere.

The interesting part is `src/hr_bridge_ble/hr_parse.py`, which decodes the
Bluetooth Heart Rate Measurement characteristic: 8 or 16 bit rate, skin contact,
energy expended, and RR intervals. It is a pure function and is tested against
byte vectors for each of those.

Releases are cut by pushing a `vYYYY.M.D.N` tag. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

GPL-3.0-or-later. See [LICENSE](LICENSE).
