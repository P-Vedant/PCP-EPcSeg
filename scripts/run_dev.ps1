$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$index = 'data/prepared-24/index.json'
function Run-Checked([string[]]$Arguments) {
    & $python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python failed: $Arguments" }
}
Run-Checked @('-m','pcp','baseline','--index',$index,'--run','runs/dev24-baseline-s17')
Run-Checked @('-m','pcp','profile','--index',$index)
foreach ($mode in @('regional','auxiliary','pocket')) {
    Run-Checked @('-m','pcp','train','--index',$index,'--run',"runs/dev24-$mode-s17",'--config',"configs/dev-$mode.json")
}
