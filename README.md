# OPTIMIZE SUPER | MTDEV

A Python desktop application for real Windows monitoring, reviewed cleanup and reversible configuration changes. Built with PySide6 and psutil. Core features work offline after dependencies are installed.

**Target:** Windows 10/11, x64, Python 3.11+. **Developer branding:** MTDEV.

**Delivery status:** Implemented source application, not an executable build. Automated checks and offscreen GUI rendering were run on Linux. Windows APIs, UAC, restore points, DNS changes, hardware sensors, Windows shortcuts and the frozen executable require the Windows acceptance checks in [docs/WINDOWS_ACCEPTANCE.md](docs/WINDOWS_ACCEPTANCE.md). This package does not claim production certification or measured gaming improvements.

## Run on Windows

1. Extract the entire ZIP to a permanent folder. Do not run files inside the ZIP.
2. Install **Python 3.11 x64 or newer** from [python.org](https://www.python.org/downloads/windows/), with the Python Launcher. The scripts default to `py -3.11`; change that to your installed version if necessary.
3. Double-click **launch_windows.bat**. The first launch creates a virtual environment and installs dependencies; that initial step needs an internet connection.
4. Begin as a standard user. For an operation that reports administrator permission is required, open **Settings → Restart as administrator**, accept the Windows UAC prompt, and retry. Use the same account to retain the same per-user backups.

Manual installation:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py
```

No Windows settings change when you merely launch the app. Only real monitoring starts. On non-Windows hosts, system monitoring and read-only/file analysis remain usable; Windows-specific actions report that they are unsupported.

## Build a standalone Windows executable

Build **on Windows with x64 Python**. PyInstaller is not a Windows cross-compiler when running on Linux.

Double-click **build_windows.bat**, or use:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm OptimizeSuper.spec
```

Result: **dist\OptimizeSuper-MTDEV.exe**. The spec bundles the Python interpreter, Qt runtime and branding, uses a Windows version resource and requests ordinary user privileges at startup. End users of the executable do not need Python installed. Keep the executable in a stable folder if enabling application startup. Exercise the build on clean Windows 10 and Windows 11 x64 VMs before distribution. Signing, an installer and an update service are not included. Dependency version ranges are in requirements files; versions used for local verification are recorded in [docs/TEST_REPORT.md](docs/TEST_REPORT.md).

## Modules and actual behavior

| Module | Implemented behavior |
| --- | --- |
| Dashboard | CPU, RAM, disks, upload/download rates, uptime, visible process count, Windows/CPU/GPU identity. History graphs use actual samples. |
| Super Optimize | Individually selectable temporary cleanup, separately confirmed Recycle Bin, startup/process audits, client-area animation preference and supported High performance power plan. Every stage reports failures independently. |
| Gaming Boost | Windows Game Mode preference and settings shortcut; read-only DirectX HAGS diagnostics and graphics settings shortcut; game list with Keep current/Balanced/High performance profiles, launch action and saved-plan restore. |
| RAM Management | Memory-heavy process list, reviewed application close, real before/current memory usage. No artificial cache purges. |
| Storage Cleaner | User/Windows Temp, D3D shader cache, thumbnail cache, optional default Chrome/Edge disk cache, Recycle Bin. Full paths and sizes before deletion. Read-only large-file (100 MB+) and SHA-256 duplicate scanners with folder selection and cancellation. |
| Startup Manager | 64-/32-bit registry Run entries and user/shared Startup folders. Disable with backup; enable again by restoring that entry in Restore Center. CompanyName executable metadata when present, explicitly not a verified signature. |
| Process Manager | Search by name/PID, sortable sampled CPU/RAM/name, same-user process termination with confirmation and critical-process protection. |
| Network | Interface addresses, connection/link status, aggregate live speeds, physical adapter selection, Cloudflare/Google IPv4 DNS, cache flush and original static/DHCP restore. |
| Windows Tools | Native Disk Cleanup, Update, Device Manager, Task Manager, Security, System Information, Power Options, Network Settings, System Restore. |
| Restore Center | Before-state operation journal, status/error details, supported undo, restore original settings newest-first, Windows restore point creation and history export. |
| Settings | Dark/light, English/Vietnamese navigation, transitions, tray behavior, notifications, optimization defaults, app startup, automatic cleanup review interval and preference reset. Technical reports/descriptions remain English. |

### Telemetry and hardware support

- A monitor thread samples approximately once per second. Process rows refresh every two seconds when their page is visible. The first per-process CPU sample is a baseline; multithreaded processes may exceed 100% because psutil counts core utilization.
- CPU temperature is shown only if the platform supplies a CPU sensor through psutil. It is normally unavailable on Windows without additional sensor support.
- GPU utilization/temperature currently use an installed NVIDIA `nvidia-smi.exe`, queried at most once every ten seconds. The first NVIDIA GPU is sampled. AMD/Intel GPU identity is available via CIM, but their utilization/temperature is marked unavailable. No fabricated readings or FPS values are shown.
- HAGS checks read dxdiag scheduling fields. Unsupported, older or localized output produces an explicit unknown result and a link to Windows graphics settings. No HAGS registry hack is applied.
- Network rates use aggregate OS interface counters, not a speed-test request. Virtual interfaces can contribute to these counters.

### Cleanup policy

- Only regular, single-link files at least **48 hours old** in explicitly supported cache/temp roots qualify. Windows executables, DLLs, drivers, installers, shortcuts and command/script files are excluded.
- Candidates are scanned first. A dialog displays full locations, categories, sizes and estimated bytes. Uncheck any item you want to keep. A changed file identity/size/modification time is skipped when deleting.
- Symbolic links and Windows reparse-point paths are rejected; scans do not traverse redirected directories. Locked/inaccessible files are skipped and reported. No directory tree is recursively deleted.
- Optional browser cleanup is limited to the default Chrome and Edge `Cache/Cache_Data` locations. It does not touch browser history, cookies, passwords or profiles. Known browsers must be closed before scan and deletion. Other browser profiles/caches are not included.
- Thumbnail caches in use may be locked and remain untouched. Permission failures do not count as successful deletion.
- Large-file and duplicate scans are **read-only**. They support opening a result's location for manual review. Equal-size files are hashed and grouped by SHA-256; hard links are not counted as duplicate storage.
- Recycle Bin uses the native Windows API with a separate location/item-count/size preview and confirmation. Cleanup and Recycle Bin emptying permanently delete files and **cannot be undone** by this application.
- Automatic cleanup configuration schedules scans only while this app is running. It presents a review dialog before any deletion; it installs no background service/task and performs no silent file deletion.

### Changes, backup and restore

- Before changing a registry value, power plan, startup shortcut, DNS configuration or Windows client-area animation preference, an atomic JSON snapshot is written under the current user's application data.
- Registry snapshots preserve the original type, binary data and whether the value existed. Startup shortcuts are moved to a backup location, not destroyed. Public Windows APIs are used for UI animation preferences.
- Power changes only activate already-installed Balanced or High performance plans. No custom plan is invented. Devices with Modern Standby may not offer High performance; the app reports unsupported and preserves the original plan.
- Game power profiles persist until restored; **Restore last power change** restores the saved original plan. Higher performance plans may increase power draw, fan noise and heat. The game launch flow asks before applying a profile.
- DNS snapshots retain the adapter GUID and original static-versus-DHCP configuration. Only IPv4 is changed. A DHCP restore uses the IPv4-specific Windows command so IPv6 remains unchanged. DNS changes do not guarantee lower ping.
- Restore Center refuses out-of-order changes to the same setting and refuses unexpected external value changes. Failed/interrupted operations retain their original snapshots for recovery. The default-restore button reverses **this application's saved changes**, not unrelated Windows configuration.
- Creating a restore point requires elevation and enabled System Protection; Windows can limit creation frequency. A new point is verified before success is reported. Restore Center opens the native Windows tool for full system recovery.
- Never move, edit or delete backups if you want to retain undo support. No registry cleaning, service disabling, Defender/Firewall/Update disabling, memory-cache purging or automatic process killing is implemented.

### Process close policy

A selected PID and its creation timestamp are revalidated before termination. The app refuses its own process/ancestors, protected names, other users' processes, all executables under the Windows directory, service/session-0 processes and processes whose Windows protection state cannot be verified. Unsaved work may be lost even for a permitted application. There is no automatic process termination in Super Optimize or Gaming Boost.

## Data and troubleshooting

User-specific state is stored in:

```text
%LOCALAPPDATA%\MTDEV\OptimizeSuper\
  config\settings.json
  logs\app.log
  backups\<operation-id>.json
  backups\<id>_<disabled-startup-shortcut>
  data\
```

Logs rotate at 2 MB with three older copies. Audit entries and exported reports can contain local paths, adapter configuration, startup commands and application names. No telemetry is sent. The package's empty `logs`, `backups`, `data`, `config` folders document the project structure; active state uses the per-user location, including in frozen builds.

- **Permission denied:** keep the report, restart as administrator if the requested operation needs it, then retry. Do not disable security software.
- **Power plan unavailable:** use Windows Power Options; no change was claimed.
- **Restore failed:** examine the saved entry in Restore Center, restore newer operations first, and reconnect the original network adapter if needed. A later external setting is not overwritten silently.
- **Startup entry absent:** Windows also supports scheduled tasks, services and packaged startup apps, which this list does not modify. Use the Windows Startup settings shortcut for those other app mechanisms.
- **Unavailable sensor:** the driver or supported vendor utility does not expose the metric. This is not replaced by a fake number.
- **Corrupt configuration:** startup stops with an error rather than silently replacing state. Back up the affected files before repairing preferences.
- **Close while work runs:** the application waits for an active operation to finish; cancellable file scans expose a Cancel button. Tray mode can be disabled in Settings.
- **Sign-in startup from source:** keep the project and `.venv` at their installed paths. After moving them, disable and re-enable app startup.

## Development

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

Tests operate on temporary fixture files and mocked configuration APIs. They do not change your Windows settings or kill a live application. The Qt integration test renders offscreen, exercises all pages/themes, real read-only monitoring, search and worker shutdown. Windows mutation acceptance tests are manual and listed separately.

```text
main.py                       Startup, single-instance lock, exception handling
core/state.py                 Atomic preferences, snapshots, rolling logs
core/windows.py               Windows-only gateway, PowerShell encoding, native tools
core/monitor.py               Read-only system monitoring
core/tasks.py                 Thread-pool jobs and monitoring thread
modules/cleaner.py             Reviewed cleanup / read-only file analysis
modules/processes.py           Process sampling and guarded termination
modules/settings_engine.py     Backed-up settings and ordered restore
modules/startup.py             Registry and Startup-folder inventory
modules/network.py             Adapter inventory and reversible IPv4 DNS
modules/gaming.py              DirectX scheduling diagnostics
modules/version_info.py        Optional executable company metadata
ui/window.py                   Application pages and connected actions
ui/widgets.py                  Metrics, sorting tables and file-review dialog
ui/theme.py                    Dark/light styles
assets/                        MTDEV vector logo, PNG, Windows ICO/version info
OptimizeSuper.spec             PyInstaller Windows one-file configuration
launch_windows.bat             Source launch and first dependency installation
build_windows.bat              Windows test/build pipeline
```

## Primary technical references

- [Qt for Python deployment](https://doc.qt.io/qtforpython-6/deployment/index.html)
- [PyInstaller Windows builds](https://pyinstaller.org/en/stable/usage.html#windows)
- [psutil API reference](https://psutil.readthedocs.io/)
- [Windows SystemParametersInfo](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfow)
- [Windows DNS configuration API](https://learn.microsoft.com/en-us/powershell/module/dnsclient/set-dnsclientserveraddress)
- [Windows restore checkpoint command](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/checkpoint-computer)

Bundled dependencies retain their respective licenses. Include appropriate third-party notices when distributing a frozen build.
