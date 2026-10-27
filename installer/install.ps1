param([string]$InstallDirectory)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'install_paths.ps1')
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestDock'
$existing = Get-ItemProperty -LiteralPath $key -ErrorAction SilentlyContinue
if (-not $InstallDirectory) {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.FolderBrowserDialog
    $picker.Description = 'Choose where to install QuestDock. A QuestDock subfolder will be used. Your task data stays in your user profile.'
    $picker.ShowNewFolderButton = $true
    $picker.SelectedPath = if ($existing.InstallLocation) { $existing.InstallLocation } else { Join-Path $env:LOCALAPPDATA 'Programs' }
    try {
        if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return }
        $InstallDirectory = Get-QuestDockDirectory $picker.SelectedPath
    } finally { $picker.Dispose() }
    $answer = [System.Windows.Forms.MessageBox]::Show("Install QuestDock to:`n$InstallDirectory", 'QuestDock Setup', 'OKCancel', 'Information')
    if ($answer -ne [System.Windows.Forms.DialogResult]::OK) { return }
}
$destination = Resolve-QuestDockDirectory $InstallDirectory $PSScriptRoot $env:APPDATA
if ($existing.InstallLocation -and [IO.Path]::GetFullPath($existing.InstallLocation).TrimEnd('\') -ne $destination) {
    throw 'QuestDock is installed in another folder. Uninstall it first (your tasks will be retained), then choose the new folder.'
}
$version = (Get-Content -Raw -LiteralPath (Join-Path $PSScriptRoot 'version.json') | ConvertFrom-Json).version
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid package version.' }
if (Get-Process QuestDock -ErrorAction SilentlyContinue) { throw 'Please exit QuestDock before installing.' }
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'QuestDock.exe') -Destination (Join-Path $destination 'QuestDock.exe') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'uninstall.ps1') -Destination (Join-Path $destination 'uninstall.ps1') -Force
foreach ($name in @('LICENSE','NOTICE')) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path $destination $name) -Force }
$shell = New-Object -ComObject WScript.Shell
$desktop = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'QuestDock.lnk'))
$desktop.TargetPath = Join-Path $destination 'QuestDock.exe'
$desktop.Save()
$menu = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Programs')) 'QuestDock.lnk'))
$menu.TargetPath = Join-Path $destination 'QuestDock.exe'
$menu.Save()
New-Item -Path $key -Force | Out-Null
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$values = @{
    DisplayName = 'QuestDock'
    DisplayVersion = $version
    Publisher = 'anayse'
    DisplayIcon = (Join-Path $destination 'QuestDock.exe')
    InstallLocation = $destination
    InstallDate = (Get-Date -Format 'yyyyMMdd')
    URLInfoAbout = 'https://github.com/anayse/QuestDock'
    UninstallString = ('"{0}" -NoProfile -ExecutionPolicy Bypass -File "{1}"' -f $powershell,(Join-Path $destination 'uninstall.ps1'))
}
foreach ($name in $values.Keys) { New-ItemProperty -Path $key -Name $name -Value $values[$name] -PropertyType String -Force | Out-Null }
foreach ($name in @('NoModify','NoRepair')) { New-ItemProperty -Path $key -Name $name -Value 1 -PropertyType DWord -Force | Out-Null }
New-ItemProperty -Path $key -Name EstimatedSize -Value ([int][Math]::Ceiling((Get-Item -LiteralPath (Join-Path $destination 'QuestDock.exe')).Length / 1KB)) -PropertyType DWord -Force | Out-Null
Write-Host 'QuestDock installed. Open the desktop shortcut.'
