# Verification report

Date: 2026-11-10. Package: OPTIMIZE SUPER | MTDEV 1.0.0.

## Executed locally

Host: Linux x86_64, Python 3.12.14, PySide6 6.12.0, psutil 7.2.2. Qt platform: `offscreen`.

- Python compile check over all source modules.
- **19 automated tests passed.**
- Qt integration: all eleven pages; dark/light themes; English/Vietnamese navigation selection; real host telemetry; process search; background job result delivery; clean monitor-thread shutdown.
- Cleaner: preview has no side effects; changed-file skip; allowed-root and age policy; executable protection; symlink/junction-path exclusion; hard-link exclusion; cancellation; parent-path replacement with a symlink cannot redirect the reviewed deletion in the tested scenario.
- File analysis: equal-size different-content files are not duplicates; SHA-256 duplicate grouping; no personal-file deletion.
- State/restore: original data persisted before attempted mutation; failed operation retains backup; binary registry value/type preserved; external change conflict; newest-first restore; animation preference snapshot/undo; corrupt preferences are not silently overwritten; independent default preference instances.
- Network: failed change retains original snapshot; restore refuses an external switch to DHCP.
- Processes: critical names and PIDs blocked before a termination attempt; PID creation-time change rejected.
- DirectX parser: explicit scheduling support/enabled fields and missing-output behavior.
- Interface PNGs visually inspected. Screenshots under this folder contain actual **Linux test-host telemetry**, not Windows validation evidence or sample Windows statistics.

The local pytest environment emits one deprecation warning from its preinstalled `anyio` plugin. No test failed.

## Not executed here

No Windows machine is attached to this environment. The following are implemented but **not runtime-validated on Windows here**:

- Windows registry mutations and typed restore through winreg.
- Windows SystemParametersInfo, process protection query and termination.
- Native Recycle Bin API, Windows locked-file/reparse behavior.
- UAC/elevation, logon startup, Windows tray and DPI behavior.
- powercfg plan activation and Modern Standby restrictions.
- DNS adapter state capture, IPv4 changes, static/DHCP recovery and IPv6 preservation.
- System Protection restore-point creation, frequency restrictions and verification.
- Windows hardware/CIM identity, NVIDIA metrics and dxdiag output across drivers/locales.
- Windows native tool launch paths and ms-settings handlers.
- PyInstaller Windows executable creation, dependency bundling and clean-machine execution.

No `.exe` was built or tested here. Run [WINDOWS_ACCEPTANCE.md](WINDOWS_ACCEPTANCE.md) on Windows 10 and Windows 11 before treating a build as release-ready. Mocked unit checks are evidence of control-flow and backup safeguards, not proof of Windows integration compatibility.
