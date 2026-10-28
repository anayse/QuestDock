# 开发与发布

[返回首页](../README.md) · [架构说明](ARCHITECTURE.md)

## 环境与入口

项目面向 Windows，构建使用 Python 3.12，依赖固定在根目录的 `requirements-build.txt`。以下命令均在仓库根目录执行。

```powershell
python -m pip install -r requirements-build.txt
python -m questdock
```

应用入口经由 `questdock.launcher` 获取单实例锁，再启动 `questdock.premium.App`。正常运行读取真实存档；不要用个人存档做自动测试。

## 隔离预览与性能测量

```powershell
python -m tools.preview_premium
python -m tools.preview_premium --calendar
python -m tools.preview_premium --form
python -m tools.benchmark_ui
```

预览还支持 `--picker`、`--types`、`--focus`，以及用于截图检查的 `--framed-qa`、`--review`。它使用 `tests/test_fixtures.py` 中的通用数据，预览存档位于 `test-output/premium-preview.json`。测试样例不能被生产应用导入。

性能脚本创建 2,000 个临时任务，测量悬停、滚动绘制等行为，结果写入 `test-output/performance.json`。结果取决于本机环境，不能直接当作产品性能承诺。

## 测试

```powershell
# 模型、更新及安装器组件
python -m unittest tests.test_desktop_geometry tests.test_focus_timer tests.test_updater tests.test_setup tests.test_release -v

# 全量回归，包括真实 Tk 窗口
python -m unittest discover -s tests -t . -v

# 安装路径规则与 PowerShell 语法
.\tests\test_install_paths.ps1
```

GUI 测试需要可用的 Windows 桌面会话。测试临时重定向存档路径，真实用户数据不应被读写。`test_clean_release.py` 验证空任务和旧存档；`test_updater.py` 验证版本、来源、完整性和更新备份；`test_setup.py` 验证安装载荷及目录传递。

## 构建

```powershell
python -m tools.release
```

构建两次 PyInstaller：先生成应用，再生成内嵌应用载荷的安装器。运行时更新脚本打包到 `questdock/resources/`；安装脚本保存在安装器的压缩载荷中。生成的 spec、缓存均放在 `build/`。

```text
releases/v1.2.0/
├── QuestDock-Setup.exe
├── QuestDock-v1.2.0-Windows.zip
├── QuestDock-update.bin
├── SHA256SUMS.txt
├── README.md
├── README.en.md
├── LICENSE
├── NOTICE
├── docs/
└── CHANGELOG.md
```

已有版本目录会拒绝覆盖。验证目录调整时可使用独立输出位置：

```powershell
python -m tools.release --output-dir test-output/build-check
```

EXE 与 ZIP 必须使用同一个安装器。ZIP 只包含安装器和说明，不能再放可直接运行的应用本体。公开应用的 `initial()` 必须保持空任务列表。

根目录 `LICENSE` 为 Apache 2.0 官方完整文本，`NOTICE` 记录项目版权信息。ZIP 同时包含两种语言的 README、许可证与说明文档；EXE 的安装载荷也包含 LICENSE/NOTICE，安装后保留在程序目录。修改 README 时应同步 `README.md` 与 `README.en.md`，保持顶部语言链接有效。

## 版本与发布流程

`questdock/version.py` 是唯一版本号来源，当前正式版为 `1.2.0`。V1.0 保留为最初的稳定基线。

1. 在独立开发分支修改代码，补充有意义的回归测试。
2. 发布前递增版本号，更新根目录 `CHANGELOG.md`，不重写历史 Release。
3. 运行相关测试并构建，核对安装入口、载荷与存档兼容性。
4. 发布后检查 Actions 完成状态和下载资产的 SHA-256 信息。

`.github/workflows/release.yml` 支持版本标签、手动触发，以及 main 分支的 `questdock/version.py` 变更。先运行校验与测试，再检查对应 Release 是否存在；已存在则跳过构建和发布，保持原安装包不变。发布新版本必须递增版本号。

V1.2 起，客户端只接受 `QuestDock-update.bin` 作为新版本应用组件，不能把 `QuestDock-Setup.exe` 当作应用本体替换。V1.0/V1.1 用户需手动安装一次 V1.2。

## 源码与私有数据边界

- 不提交用户存档、令牌、安装缓存、测试输出和打包产物。
- `private-builds/` 是本机私有备份目录，已加入忽略规则。
- 早期本地 Git 历史含个人预置任务；公开历史应从已清理的远端基线继续，不能直接推送旧本地基线和旧标签。
- 文档的功能描述应与实现一致，不把未验证能力写成正式特性。

## 功能变更的发布要求

涉及程序功能或逻辑的修改，提交 GitHub 时必须同步递增版本号、更新文档与更新日志，并发布对应 EXE 安装器、ZIP、自动更新组件和校验清单。确认发布成功后才视为完成；旧版发布产物不得覆盖。
