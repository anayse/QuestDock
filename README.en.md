<div align="center">

[简体中文](README.md) · **English**

![QuestDock — Small steps. Real progress.](docs/assets/hero.svg)

# QuestDock

**Turn today's work into quests, progress, and rewards.**

Tap the floating orb to plan your day, earn experience, and redeem rewards you choose.

[![Release](https://img.shields.io/github/v/release/anayse/QuestDock?style=flat-square&color=ac9cff)](https://github.com/anayse/QuestDock/releases/latest)
![Platform](https://img.shields.io/badge/platform-Windows-83dfc2?style=flat-square)
![Python](https://img.shields.io/badge/python-3.12-9cbaff?style=flat-square)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-ac9cff?style=flat-square)](LICENSE)
[![Build](https://github.com/anayse/QuestDock/actions/workflows/release.yml/badge.svg)](https://github.com/anayse/QuestDock/actions/workflows/release.yml)

[**Download the EXE installer**](https://github.com/anayse/QuestDock/releases/latest/download/QuestDock-Setup.exe) · [All releases](https://github.com/anayse/QuestDock/releases) · [User guide (中文)](docs/USER_GUIDE.md) · [Development guide (中文)](docs/DEVELOPMENT.md)

</div>

---

## Keep progress in view

Your task list does not need to take over your screen. QuestDock stays at the edge of your desktop until you need it. Expand the panel, take a small step, and see your progress, tokens, and experience grow.

Use **Daily Tasks** for recurring habits, **Story Quests** for milestones, and **Research** or custom categories for longer projects. Choose what deserves your attention today instead of putting your entire backlog on display.

| Feature | What it does |
| --- | --- |
| **Floating desktop orb** | Open the task panel with a click. Snap to an edge, hide automatically, lock the position, and adjust opacity from 1–100%. |
| **Today's plan** | Pick tasks manually or add them automatically by category. The orb and progress bar reflect the same daily plan. |
| **Progress and levels** | Earn tokens and XP for each step of a multi-step task. Gain a level for every 200 XP earned. |
| **Reward shop** | Define your own rewards and prices, redeem them with tokens, and use them from your inventory. |
| **Completion calendar** | Browse daily-task completion history by week, month, or a custom date range. |
| **Focus timer** | Start a 25-minute session, pause or resume it, and record the result in your activity history. |

**Your quests are yours to create.** A fresh installation contains no preset personal tasks. Default categories and general shop items are included. Existing users keep their local data when upgrading.

The application and installer currently use a Chinese interface. This English README does not change the application's display language.

## Install and get started

### 1. Download

Choose a file from [GitHub Releases](https://github.com/anayse/QuestDock/releases/latest):

| File | Purpose |
| --- | --- |
| **`QuestDock-Setup.exe`** | Recommended. Run it to open the installer. |
| **`QuestDock-vX.Y.Z-Windows.zip`** | Extract the entire archive, then run the same installer inside. |
| `QuestDock-update.bin` | Used by the automatic updater. No need to download or run it manually. |
| `SHA256SUMS.txt` | SHA-256 checksums for release files. |

### 2. Choose an installation directory

Both the EXE and ZIP downloads **let you choose where to install**. Enter a path or click **浏览** (Browse), then click **安装** (Install). Canceling or closing the installer does not install the application.

QuestDock installs for the current Windows user and does not require Python. Choose a directory your account can write to. After installation, launch it from the desktop or Start menu. It also appears in Windows **Installed apps**.

### 3. Build your own task loop

1. Click the floating orb and create your first task with a category, target, and reward.
2. Add it to **今日** (Today), or configure its category to join today's plan automatically.
3. Make progress, earn tokens, and redeem a reward from your shop.

> For multi-step tasks, the configured reward applies **to each step**. A target of 3 with a reward of 30 yields 90 tokens and 90 XP in total. Single-step tasks require a manual reward claim. Decreasing or undoing progress does not take back rewards already issued; repeating a previously rewarded step does not pay again.

### Current source improvements (not yet released in installers)

These changes are development work after V1.2. The existing V1.2 installers do not yet include these improvements.

| Action | How it works |
| --- | --- |
| **Pin a task** | **追踪** (Track) is renamed to **置顶** (Pin), with an **已置顶** (Pinned) marker. Click again to unpin. Within the current filtered list, unfinished pinned tasks appear first. Pinning does not add a task to Today or start a focus session. The separate **任务面板置顶** setting keeps the application window above other windows. |
| **Edit task rewards** | Click **编辑** (Edit), previously **详情** (Details), on a task card. The reward field is directly below the title and accepts nonnegative integers. Settled tasks also keep their Edit button. Click **保存任务** (Save task) to apply changes. Previously earned tokens and XP are unchanged; future unpaid steps use the new amount. |
| **Edit shop prices** | Click **编辑** (Edit) on a shop item to open **编辑商品与价格** (Edit item and price). Change its name and positive integer token price, then click **保存修改** (Save changes). The new price applies to future redemptions; existing inventory tickets remain unchanged. |

For example, if one step has already earned 20 tokens, changing the reward to 35 makes the next new step pay 35 tokens. The previous 20 tokens and corresponding XP remain unchanged.

## Your data and updates

Task data stays on your computer:

```text
%APPDATA%\QuestDock\
├── save.json     Current save
├── save.bak      Previous valid save backup
└── updates\     Update cache, created when downloading an update
```

- **Application files and user data are separate.** Reinstalling, upgrading, and normal uninstallation preserve your task data. To change the installation directory, uninstall first, then install again.
- **Automatic updates are off by default.** Enable them in **设置 → 版本与更新** (Settings → Version & updates), or check manually. Downloads run in the background. After verification, you confirm installation and restart.
- **Releases remain available separately.** The current published version is V1.2; V1.0 and V1.1 remain available. Users upgrading from V1.0/V1.1 to V1.2 need to run the new installer once.

See the [user guide (中文)](docs/USER_GUIDE.md) for backups, migration, shortcuts, and troubleshooting. Release history is in the [changelog (中文)](CHANGELOG.md).

## Source map

```text
QuestDock/
├── questdock/                 Application package: desktop, tasks, controls, updates
│   ├── __main__.py            Entry point for python -m questdock
│   ├── launcher.py            Single-instance lock and startup
│   ├── app.py                 Persistence, initial state, and basic task logic
│   ├── premium.py             Application composition and interactions
│   ├── compact_ui.py          Compact panel, lists, and settings rendering
│   ├── desktop_*.py           Window behavior and edge geometry
│   ├── activity.py            Completion records, date ranges, and calendar
│   ├── task_types.py          Categories and today's planning rules
│   ├── step_rewards.py        Per-step rewards and duplicate-payment protection
│   ├── focus_timer.py         Focus timer model
│   ├── updater.py             Version checks, downloads, and integrity checks
│   ├── update_ui.py           Update interface and background coordination
│   └── resources/             Runtime update installation script
├── installer/                 EXE installer UI and Windows installation scripts
├── tests/                     Automated tests, isolated fixtures, and path checks
├── tools/                     Builds, visual previews, and performance measurements
├── assets/                    Application icons and build resources
├── docs/                      User, developer, and architecture documentation
├── .github/workflows/         GitHub Actions release workflow
├── requirements-build.txt     Pinned build dependencies
└── CHANGELOG.md               Release history
```

Local `build/`, `dist/`, `releases/`, `test-output/`, and `private-builds/` directories contain generated artifacts or private backups and are excluded from the public source tree.

## Local development

On **Windows with Python 3.12**, run these commands from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m questdock
```

A normal launch reads the current user's real save. For UI development, use the isolated preview instead:

```powershell
.\.venv\Scripts\python.exe -m tools.preview_premium
```

The preview uses generic sample tasks and a separate save. See the [development guide (中文)](docs/DEVELOPMENT.md) for preview options, test groups, packaging, and release steps.

```powershell
# Full suite: GUI tests require an available Windows desktop session
python -m unittest discover -s tests -t . -v

# Installation path and PowerShell syntax checks
.\tests\test_install_paths.ps1

# Build a new version directory; existing versions are never overwritten
python -m tools.release
```

## Design choices

- **A quiet desktop:** the orb does not animate continuously. Scrolling renders visible rows, and drag events are coalesced.
- **Clear feedback:** today's progress, levels, tokens, and activity records have distinct meanings. Focus time does not automatically complete tasks.
- **Recoverable state:** a single-instance lock prevents competing saves. Saving and updating retain backups, and installing an update requires confirmation.
- **Editable rules:** users control category names, automatic daily planning, task targets, and shop rewards.

See the [architecture guide (中文)](docs/ARCHITECTURE.md) for module relationships and data flows.

## Scope and feedback

The current implementation targets Windows desktops. Edge docking uses the primary monitor's work area. Shop rewards are personal commitments, not payments or purchases. The completion calendar tracks daily tasks and does not invent history from before tracking was available.

Report problems or suggestions through [Issues](https://github.com/anayse/QuestDock/issues), including your application version, Windows display scaling, and steps to reproduce. Remove personal task content before sharing screenshots or logs. For code contributions, start with the [development guide (中文)](docs/DEVELOPMENT.md).

## License

QuestDock is licensed under the **[Apache License 2.0](LICENSE)**. See [NOTICE](NOTICE) for attribution. Third-party dependencies retain their respective licenses.

Copyright 2026 anayse and QuestDock contributors.
