$ErrorActionPreference = 'Stop'
$installerRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'installer'
. (Join-Path $installerRoot 'install_paths.ps1')
if ((Get-QuestDockDirectory 'D:\Apps') -ne 'D:\Apps\QuestDock') { throw 'Parent selection failed' }
if ((Get-QuestDockDirectory 'D:\Apps\QuestDock\') -ne 'D:\Apps\QuestDock') { throw 'Repeated subfolder' }
if ((Get-QuestDockDirectory 'D:\') -ne 'D:\QuestDock') { throw 'Drive selection failed' }
$custom = Resolve-QuestDockDirectory 'D:\My Apps\QuestDock' 'C:\Package' 'C:\Profile\Roaming'
if ($custom -ne 'D:\My Apps\QuestDock') { throw 'Custom path changed' }
foreach ($bad in @('D:\','D:relative','relative','C:\Package','C:\Profile\Roaming\QuestDock','C:\Profile\Roaming\QuestDock\bin','C:\Profile')) {
    $rejected = $false
    try { Resolve-QuestDockDirectory $bad 'C:\Package' 'C:\Profile\Roaming' | Out-Null } catch { $rejected = $true }
    if (-not $rejected) { throw "Unsafe directory accepted: $bad" }
}
foreach ($name in @('install.ps1','uninstall.ps1','install_paths.ps1')) {
    $tokens = $null; $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $installerRoot $name), [ref]$tokens, [ref]$errors) | Out-Null
    if ($errors.Count) { throw ($errors | Out-String) }
}
Write-Output 'Installation path tests passed.'
