# 版本与发布约定

- `version.py` 是唯一版本号来源：当前 `VERSION = '1.1.0'`、界面 `V1.1`。
- Git 稳定基线标签：`v1.0.0`。后续功能在单独分支开发；修复升级补丁号，新增功能升级次版本号。
- 发布前更新 `version.py` 和 `CHANGELOG.md`，运行测试，然后执行 `python release.py`。
- 发布脚本只创建新的 `releases/v版本号/` 目录，已有版本拒绝覆盖。
- 每个 GitHub 正式 Release 的 tag 必须为 `vX.Y.Z`。上传 `QuestDock.exe`、版本 ZIP 和 `SHA256SUMS.txt`。
- 更新程序使用 GitHub API 资产的 SHA-256 digest；无校验信息不执行更新。测试版和低版本不会被自动安装。
- 目前支持公开 GitHub 仓库。不要把 PAT、用户存档、测试输出或打包缓存提交到仓库。
- 安装更新不修改 `%APPDATA%/QuestDock/save.json`；替换前保存旧 EXE 为 `QuestDock.previous.exe`。
- 如果更新替换失败，旧 EXE 保留，错误写入更新缓存目录的 `update-error.log`。

默认发布仓库：`anayse/QuestDock`。可以在应用设置中修改；公开的正式 Release 发布后才可联网更新。

GitHub Actions 在 main 分支的 version.py 更新时自动构建并创建对应版本的标签和 Release；也支持推送版本标签或在 Actions 手动运行。已存在的 Release 不覆盖，发布新版本必须递增版本号。

公开版的 initial() 必须保持空任务列表；测试样例仅放在 test_fixtures.py，不能被应用导入。私人存档和旧个人构建只保存在被忽略的 private-builds/，不得上传。早期本地 Git 历史含个人预置任务，公开源码从清理后的当前文件创建提交，不能直接推送旧本地历史或旧 v1.0.0 标签。
