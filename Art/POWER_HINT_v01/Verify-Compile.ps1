$ErrorActionPreference = 'Stop'
$project = 'C:\Users\gonut\School_p2'
$unityData = 'C:\Program Files\Unity\Hub\Editor\6000.3.9f1\Editor\Data'
$verificationRoot = Join-Path $PSScriptRoot '_verification'
[void][System.IO.Directory]::CreateDirectory($verificationRoot)
$utf8 = New-Object System.Text.UTF8Encoding($false)

$projectSources = @(Get-ChildItem -LiteralPath (Join-Path $project 'Assets\RELAY\Scripts') -Filter '*.cs' -File | Sort-Object Name)
$scenes = @(Get-ChildItem -LiteralPath (Join-Path $project 'Assets\Scenes') -Filter '*.unity' -File)
$observed = @($projectSources) + @($scenes)
$before = @{}
foreach ($file in $observed) {
    $before[$file.FullName] = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
}

$references = @((Join-Path $unityData 'NetStandard\ref\2.1.0\netstandard.dll'))
$references += @(Get-ChildItem -LiteralPath (Join-Path $unityData 'Managed\UnityEngine') -Filter 'UnityEngine*.dll' -File | ForEach-Object { $_.FullName })
foreach ($assembly in @('Unity.InputSystem.dll', 'UnityEngine.UI.dll', 'Unity.TextMeshPro.dll')) {
    $references += Join-Path $project ('Library\ScriptAssemblies\' + $assembly)
}
$stagedSources = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'Code') -Filter '*.cs' -File)
$stagedNames = @($stagedSources | ForEach-Object { $_.Name })
$sourcePaths = @($projectSources | Where-Object { $_.Name -notin $stagedNames } | ForEach-Object { $_.FullName })
$sourcePaths += @($stagedSources | ForEach-Object { $_.FullName })
$results = @()

foreach ($target in @('Player', 'Editor')) {
    $targetReferences = @($references)
    $options = @('-nologo', '-target:library', '-nostdlib+', '-langversion:9.0', '-nowarn:0649')
    if ($target -eq 'Editor') {
        $options += '-define:UNITY_EDITOR'
        $targetReferences += @(Get-ChildItem -LiteralPath (Join-Path $unityData 'Managed\UnityEngine') -Filter 'UnityEditor*.dll' -File | ForEach-Object { $_.FullName })
    }
    $assemblyPath = Join-Path $verificationRoot ('PowerHintCheck.' + $target + '.dll')
    $options += '-out:"' + $assemblyPath + '"'
    $options += @($targetReferences | Select-Object -Unique | ForEach-Object { '-r:"' + $_ + '"' })
    $options += @($sourcePaths | ForEach-Object { '"' + $_ + '"' })
    $responsePath = Join-Path $verificationRoot ($target + '.rsp')
    [System.IO.File]::WriteAllLines($responsePath, $options, $utf8)
    $compiler = Join-Path $unityData 'DotNetSdkRoslyn\csc.dll'
    $runtime = Join-Path $unityData 'NetCoreRuntime\dotnet.exe'
    $compilerOutput = @(& $runtime $compiler ('@' + $responsePath) 2>&1)
    $compilerExit = $LASTEXITCODE
    [System.IO.File]::WriteAllText((Join-Path $verificationRoot ($target + '.log')), ($compilerOutput -join [Environment]::NewLine), $utf8)
    $results += [pscustomobject]@{
        Target = $target
        ExitCode = $compilerExit
        SourceCount = $sourcePaths.Count
        Output = ($compilerOutput -join [Environment]::NewLine)
    }
}

$changed = @($observed | Where-Object { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash -ne $before[$_.FullName] } | ForEach-Object { $_.FullName })
$report = [pscustomobject]@{
    Timestamp = (Get-Date).ToString('o')
    UnityVersion = '6000.3.9f1'
    Compiles = $results
    InspectedProjectFilesUnchanged = ($changed.Count -eq 0)
    ChangedFiles = $changed
    UnityLaunched = $false
    PlayModeTested = $false
}
$json = $report | ConvertTo-Json -Depth 6
[System.IO.File]::WriteAllText((Join-Path $verificationRoot 'verification.json'), $json, $utf8)
$json
if (($results | Where-Object { $_.ExitCode -ne 0 }).Count -gt 0 -or $changed.Count -gt 0) { exit 1 }
