Get-ChildItem "C:\VTuneResults" -Recurse -File |
Where-Object { $_.Extension -ne ".py" } |
Remove-Item -Force
Get-ChildItem "C:\VTuneResults" -Recurse -Directory |
Where-Object { (Get-ChildItem $_.FullName).Count -eq 0 } |
Remove-Item -Force

# Paths
$socwatchExe = "C:\Program Files (x86)\Intel\oneAPI\vtune\2025.9\socwatch\64\socwatch.exe"
$vtuneExe = "C:\Program Files (x86)\Intel\oneAPI\vtune\2025.9\bin64\vtune.exe"
$appExe = "C:\Users\User\source\repos\LLamaTest\LLamaTest\bin\Release\net10.0\LLamaTest.exe"
$powerScript = "C:\VTuneResults\powerdraw.py"

# Output dirs
$powerOut = "C:\VTuneResults\power_run1"
$hotspotOut = "C:\VTuneResults\hotspots_test"

Write-Host "Starting socwatch..."

$socwatch = Start-Process `
    -FilePath $socwatchExe `
    -ArgumentList "-f sys -m -t 65 -r vtune -o $powerOut" `
    -Verb RunAs `
    -PassThru

Write-Host "Starting GPU power monitor..."

$powerMonitor = Start-Process `
    -FilePath "python" `
    -ArgumentList "`"$powerScript`" 65 --quiet" `
    -PassThru

Start-Sleep -Seconds 2

Write-Host "Starting VTune hotspots collection..."

& $vtuneExe `
    -collect hotspots `
    -result-dir $hotspotOut `
    -- $appExe

Write-Host "Waiting for socwatch to finish..."
$socwatch.WaitForExit()

Write-Host "Waiting for GPU power monitor..."
$powerMonitor.WaitForExit()

Write-Host "Generating SoC Watch timeline..."

& "C:\Program Files (x86)\Intel\oneAPI\vtune\2025.9\socwatch\64\socwatch.exe" `
    -i "C:\VTuneResults\power_run1" `
    -r int `
    -o "C:\VTuneResults\power_run1_timeline"

Write-Host "Done"