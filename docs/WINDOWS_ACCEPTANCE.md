# Windows acceptance checks — required before release

These are explicit manual checks, not claims that they were run in the Linux build environment. Use disposable Windows 10/11 x64 VMs with snapshots. Test standard-user and same-account elevated sessions. Take an independent VM snapshot before configuration tests.

| Area | Procedure | Acceptance |
| --- | --- | --- |
| Source launch | Run launch script on a fresh Python 3.11 x64 install. Reopen without internet after dependencies install. | Dashboard loads; no setting changes merely from launching. |
| Frozen build | Run build script on Windows x64. Copy EXE to machines with no Python. | Starts with icon/version metadata; Qt plugins and psutil load; no forced startup UAC. |
| Display | Check 1366×768, 1920×1080 and 125/150/200% DPI, dark/light themes. Navigate all pages while monitoring. | Scroll works, text remains readable, no stuck worker or clipped modal controls. |
| Dashboard | Compare CPU/RAM/disks/network/uptime with Task Manager, allowing different sampling windows. | Real readings; permissions/sensor limitations are explicit. |
| NVIDIA | Test compatible NVIDIA driver with nvidia-smi in a supported location; also test absent utility, unsupported GPU and multiple GPUs. | Reports first supported GPU or unavailable; never synthetic stats. |
| CPU temperature | Test without an exposed sensor. | Explicit unavailable; no fabricated Celsius number. |
| HAGS | Run DirectX check on supported, unsupported and localized OS versions. | Explicit DirectX-reported fields or unknown; Windows settings shortcut works. |
| Preview | Create a harmless file older than 48 hours in user Temp; also create a recent file and an old `.exe` fixture. Scan. | Only old non-executable regular file is offered. Paths and bytes shown before deletion. |
| Changed/locked files | Modify a candidate after scan, lock another file, deny one folder. | Changed/locked/denied items skipped and errors reported accurately. |
| Reparse points | Create a temp junction to a directory outside the allowed cleanup roots; include linked files. | No linked directory/file is deleted or traversed. |
| Windows Temp | Scan as standard user then elevated. | Permission failures explicit; no wider Windows directories touched. |
| Cache | Test thumbnail cache in use; test browser cache with browsers open, closed, and reopened after preview. | Browser-open and locked files skipped; history/cookies/passwords unaffected. |
| Recycle Bin | Put only disposable test files in Bin, review size/path, cancel, then separately confirm. | Cancel preserves files; confirmed deletion is correctly reported and marked irreversible. |
| Large/duplicate scan | Use a folder with equal-sized different contents, actual duplicates, hard links, denied files and large files. Cancel mid-scan. | Only SHA-256 matches grouped; no files deleted; cancellation produces partial-results notice. |
| Startup registry | Create a disposable HKCU Run entry (including one REG_EXPAND_SZ value), disable and restore. Repeat with HKLM under admin. | Exact type/data restored; backup exists before mutation. |
| Startup folders | Use a disposable user Startup shortcut; disable and restore. Occupy original path before restore. | Shortcut restored without execution; existing destination never overwritten. |
| Critical process | Try selecting System, svchost, Defender, explorer, another user's app and session-0 service. | All refused, without termination. |
| Allowed process | Start a disposable user test app with no unsaved work; confirm closing. | Only selected creation-time-validated process closes; before/current RAM shown without claiming fixed savings. |
| Power | Test Balanced/High performance on desktop; test Modern Standby laptop with no High performance plan. Restore original. | Correct active plan verified; unavailable plan reported without false success. |
| Windows animation | Change client-area animation preference, inspect saved original value, then undo. | SPI readback matches after each action; unrelated preferences preserved. |
| Game Mode | Save existing current-user preference, enable, inspect Windows settings, restore. | Preference backed up; no security/services changed. |
| Game profiles | Add and launch a disposable game/app with Keep current then supported power profile. | Chosen executable runs only after confirmation; original power plan can be restored. |
| DNS static | Record IPv4/IPv6 DNS independently. Apply profile on selected physical adapter and restore. | IPv4 sequence restored exactly; IPv6 unchanged; adapter identified by GUID. |
| DNS DHCP | Start with DHCP DNS; apply profile and restore. Repeat after adapter index changes. | Restores automatic IPv4 DNS using original adapter GUID; IPv6 unchanged. |
| DNS failure | Deny admin or disconnect/remove adapter during operation. | No fabricated success; before-state remains in journal; meaningful failure shown. |
| External changes | Change a modified registry value/DNS/power plan outside this app, then request undo. | Conflicting later values are not overwritten automatically. |
| Undo chain | Apply two changes to same setting; attempt older undo first, then restore defaults. | Older undo refused; newest-first restore returns to original. |
| Restore point | Try standard user, disabled System Protection, frequency-limited creation, then a permitted checkpoint. | Failure explicit; success only with a newly verified checkpoint. |
| Native tools | Exercise every Windows Tools shortcut and Settings links. | Correct native tool opens; app makes no extra configuration changes. |
| App startup | Enable startup, sign out/in, disable and sign in again. Repeat frozen/source install. | Only this app's entry added/removed, with original value saved. |
| Preferences | Save both themes, navigation languages, animations, notification/tray settings; restart and reset app preferences. | Persistence works; Windows settings and backups not reset with app preferences. |
| Automatic review | In a test build advance elapsed interval; create eligible fixture. | Scan prompts for review; cancellation never deletes; only app-running behavior promised. |
| Journal | Force a failure, restart after interrupted operation, inspect entries and logs. | Original before-state retained; failed/prepared status visible; no success claim. |
| Shutdown | Close during scan, cancel, retry close. Test tray close and explicit tray exit. | No QThread destroyed while running; no background operation abandoned mid-write. |

Do not distribute as a verified release until the relevant rows have evidence from both supported Windows versions. Store acceptance results separately from fixtures and use real hardware where VM graphics do not expose vendor sensors.
