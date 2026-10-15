$ErrorActionPreference = 'Stop'
$unityData = 'C:\Program Files\Unity\Hub\Editor\6000.3.9f1\Editor\Data'
$runtime = Join-Path $unityData 'NetCoreRuntime\dotnet.exe'
$runtimeFolder = Join-Path $unityData 'NetCoreRuntime\shared\Microsoft.NETCore.App\6.0.21'
$outputFolder = Join-Path $PSScriptRoot '_verification'
[void][IO.Directory]::CreateDirectory($outputFolder)
$utf8 = New-Object Text.UTF8Encoding($false)
$options = @('-nologo', '-target:exe', '-nostdlib+', '-langversion:9.0')
$options += '-out:"' + (Join-Path $outputFolder 'RuleChecks.dll') + '"'
foreach ($name in @('System.Private.CoreLib.dll', 'System.Runtime.dll', 'System.Console.dll')) {
    $options += '-r:"' + (Join-Path $runtimeFolder $name) + '"'
}
$options += '"' + (Join-Path $PSScriptRoot 'Code\PowerCalibrationRule.cs') + '"'
$options += '"' + (Join-Path $PSScriptRoot 'Checks\PowerChecks.cs') + '"'
$response = Join-Path $outputFolder 'Rules.rsp'
[IO.File]::WriteAllLines($response, $options, $utf8)
& $runtime (Join-Path $unityData 'DotNetSdkRoslyn\csc.dll') ('@' + $response)
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
[IO.File]::WriteAllText((Join-Path $outputFolder 'RuleChecks.runtimeconfig.json'), '{"runtimeOptions":{"tfm":"net6.0","framework":{"name":"Microsoft.NETCore.App","version":"6.0.21"}}}', $utf8)
$result = @(& $runtime (Join-Path $outputFolder 'RuleChecks.dll') 2>&1)
$resultCode = $LASTEXITCODE
[IO.File]::WriteAllText((Join-Path $outputFolder 'Rules.log'), ($result -join [Environment]::NewLine), $utf8)
$result
exit $resultCode
