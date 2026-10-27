param([Parameter(Mandatory=$true)][string]$Source,
      [Parameter(Mandatory=$true)][string]$Target,
      [Parameter(Mandatory=$true)][string]$Sha256,
      [Parameter(Mandatory=$true)][int]$AppProcessId,
      [string]$Version = '',
      [switch]$SkipLaunch)
$ErrorActionPreference = 'Stop'
try {
    $sourcePath = [IO.Path]::GetFullPath($Source)
    $targetPath = [IO.Path]::GetFullPath($Target)
    if ([IO.Path]::GetFileName($targetPath) -ne 'QuestDock.exe' -or $sourcePath -eq $targetPath) { throw 'Invalid update target.' }
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($sourcePath)
    try { $actualHash = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') } finally { $stream.Dispose(); $sha.Dispose() }
    if ($actualHash -ne $Sha256) { throw 'Update checksum mismatch.' }
    $appProcess = $null
    try { $appProcess = [Diagnostics.Process]::GetProcessById($AppProcessId) } catch { }
    if ($null -ne $appProcess) {
        try { if (-not $appProcess.WaitForExit(120000)) { throw 'Application did not exit in time.' } } finally { $appProcess.Dispose() }
    }
    $pendingPath = [IO.Path]::Combine([IO.Path]::GetDirectoryName($targetPath), 'QuestDock.update.tmp')
    $backupPath = [IO.Path]::Combine([IO.Path]::GetDirectoryName($targetPath), 'QuestDock.previous.exe')
    [IO.File]::Copy($sourcePath, $pendingPath, $true)
    $installed = $false
    for ($attempt=0; $attempt -lt 60; $attempt++) {
        try {
            [IO.File]::Replace($pendingPath, $targetPath, $backupPath)
            $installed = $true
            break
        } catch { [Threading.Thread]::Sleep(500) }
    }
    if (-not $installed) { throw 'Could not replace application. The existing version was preserved.' }
    # Portable copies must not change the registered installed application's version.
    if ($Version -match '^\d+\.\d+(\.\d+)?$') {
        $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Microsoft\Windows\CurrentVersion\Uninstall\QuestDock', $true)
        if ($null -ne $key) {
            try {
                if ($key.GetValue('InstallLocation') -eq [IO.Path]::GetDirectoryName($targetPath)) { $key.SetValue('DisplayVersion', $Version) }
            } finally { $key.Dispose() }
        }
    }
    if (-not $SkipLaunch) {
        $startInfo = New-Object Diagnostics.ProcessStartInfo
        $startInfo.FileName = $targetPath
        $startInfo.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
        [Diagnostics.Process]::Start($startInfo) | Out-Null
    }
} catch {
    [IO.File]::WriteAllText([IO.Path]::Combine([IO.Path]::GetDirectoryName($Source), 'update-error.log'), $_.Exception.ToString())
    exit 1
}
