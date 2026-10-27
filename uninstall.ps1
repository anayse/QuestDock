$ErrorActionPreference = 'Stop'
try {
    $destination = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\QuestDock'))
    if ([IO.Path]::GetFullPath($PSScriptRoot) -ne $destination) { throw 'Run the installed uninstaller only.' }
    if (Get-Process QuestDock -ErrorAction SilentlyContinue) { throw 'Please exit QuestDock and try uninstalling again.' }
    # Only remove known application files. User saves in APPDATA are retained.
    foreach ($name in @('QuestDock.exe','QuestDock.previous.exe','QuestDock.update.tmp')) {
        $file = Join-Path $destination $name
        if (Test-Path -LiteralPath $file) { Remove-Item -LiteralPath $file -Force }
    }
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in @('Desktop','Programs')) {
        $link = Join-Path ([Environment]::GetFolderPath($folder)) 'QuestDock.lnk'
        if ((Test-Path -LiteralPath $link) -and $shell.CreateShortcut($link).TargetPath -eq (Join-Path $destination 'QuestDock.exe')) { Remove-Item -LiteralPath $link -Force }
    }
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestDock'
    if (Test-Path -LiteralPath $key) { Remove-Item -LiteralPath $key }
    Remove-Item -LiteralPath (Join-Path $destination 'uninstall.ps1') -Force
    if (-not (Get-ChildItem -LiteralPath $destination -Force)) { Remove-Item -LiteralPath $destination }
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'QuestDock uninstall') | Out-Null
    exit 1
}
