$ErrorActionPreference = 'Stop'
try {
    $key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestDock'
    $registration = Get-ItemProperty -LiteralPath $key -ErrorAction Stop
    if (-not $registration.InstallLocation) { throw 'Installation location is missing.' }
    $destination = [IO.Path]::GetFullPath($registration.InstallLocation).TrimEnd('\')
    if ($destination.Length -le 3 -or [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') -ne $destination) { throw 'Run the registered installed uninstaller only.' }
    if (Get-Process QuestDock -ErrorAction SilentlyContinue) { throw 'Please exit QuestDock and try uninstalling again.' }
    # Only remove known application files. User saves in APPDATA are retained.
    foreach ($name in @('QuestDock.exe','QuestDock.previous.exe','QuestDock.update.tmp','LICENSE','NOTICE')) {
        $file = Join-Path $destination $name
        if (Test-Path -LiteralPath $file) { Remove-Item -LiteralPath $file -Force }
    }
    $shell = New-Object -ComObject WScript.Shell
    foreach ($folder in @('Desktop','Programs')) {
        $link = Join-Path ([Environment]::GetFolderPath($folder)) 'QuestDock.lnk'
        if ((Test-Path -LiteralPath $link) -and $shell.CreateShortcut($link).TargetPath -eq (Join-Path $destination 'QuestDock.exe')) { Remove-Item -LiteralPath $link -Force }
    }
    if (Test-Path -LiteralPath $key) { Remove-Item -LiteralPath $key }
    Remove-Item -LiteralPath (Join-Path $destination 'uninstall.ps1') -Force
    if (-not (Get-ChildItem -LiteralPath $destination -Force)) { Remove-Item -LiteralPath $destination }
} catch {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'QuestDock uninstall') | Out-Null
    exit 1
}
