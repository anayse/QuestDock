function Get-QuestDockDirectory([string]$ParentDirectory) {
    $path = $ParentDirectory.TrimEnd('\','/')
    if ([IO.Path]::GetFileName($path) -eq 'QuestDock') { return $path }
    return [IO.Path]::Combine($path + '\', 'QuestDock')
}

function Resolve-QuestDockDirectory([string]$Directory, [string]$PackageDirectory, [string]$AppDataDirectory) {
    if ($Directory -notmatch '^[A-Za-z]:[\\/]') { throw 'Select an absolute local drive path.' }
    $path = [IO.Path]::GetFullPath($Directory).TrimEnd('\','/')
    if ($path.Length -le 3) { throw 'Do not install directly into a drive root.' }
    $package = [IO.Path]::GetFullPath($PackageDirectory).TrimEnd('\','/')
    if ($path -eq $package) { throw 'Choose a folder different from the extracted installation package.' }
    $data = [IO.Path]::GetFullPath((Join-Path $AppDataDirectory 'QuestDock')).TrimEnd('\','/')
    if ($path -eq $data -or $path.StartsWith($data + '\', [StringComparison]::OrdinalIgnoreCase) -or $data.StartsWith($path + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'The installation folder must be separate from the task data folder.'
    }
    return $path
}
