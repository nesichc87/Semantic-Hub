<#
.SYNOPSIS
    Start the Semantic Hub with local source copies and warm up all sources.

.DESCRIPTION
    Points the source URLs to local copies via file:// URLs, starts uvicorn
    in a separate window, waits until the API responds and resolves one
    identifier per source. This way the sources are loaded and parsed
    before the first visitor arrives. Finally opens the demo page.

.PARAMETER SourceDir
       Folder containing kbl2.5-sr1.xsd, vec-2.2.0-ontology.ttl, qudt-unit.ttl
    and the DPPO modules dpp-odp.ttl, dpp-core.ttl, dpp-info.ttl,
    dpp-comp.ttl and dpp-prov.ttl.

.PARAMETER Port
    Port for uvicorn (default: 8000).

.EXAMPLE
    .\scripts\start-demo.ps1 -SourceDir <folder with local copies>
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceDir,

    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$repoDir = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoDir ".venv\Scripts\python.exe"
$baseUrl = "http://127.0.0.1:$Port"

$sources = [ordered]@{
    SEMANTIC_HUB_KBL_XSD_URL       = "kbl2.5-sr1.xsd"
    SEMANTIC_HUB_VEC_TTL_URL       = "vec-2.2.0-ontology.ttl"
    SEMANTIC_HUB_QUDT_UNIT_TTL_URL = "qudt-unit.ttl"
}

$dppoModules = @("dpp-odp", "dpp-core", "dpp-info", "dpp-comp", "dpp-prov")

$warmUpPaths = @(
    "/api/resolve/kbl:Component",
    "/api/resolve/vec:PartVersion",
        "/api/resolve/qudt:unit:M",
    "/api/resolve/dppo:dpp-core:ComponentDPP",
    "/api/suggest?query=metre"
)

if (-not (Test-Path $python -PathType Leaf)) {
    throw "Python not found: $python. Create the virtual environment first."
}

foreach ($name in $sources.Keys) {
    $file = Join-Path $SourceDir $sources[$name]
    if (-not (Test-Path $file -PathType Leaf)) {
        throw "Source file not found: $file"
    }
    $url = ([System.Uri](Resolve-Path $file).Path).AbsoluteUri
    Set-Item -Path "env:$name" -Value $url
    Write-Host "$name = $url"
}


# DPPO consists of several modules. Its URL is a template in which the
# application replaces {module} with the module name.
foreach ($module in $dppoModules) {
    $file = Join-Path $SourceDir "$module.ttl"
    if (-not (Test-Path $file -PathType Leaf)) {
        throw "Source file not found: $file"
    }
}
$dppoDir = ([System.Uri](Resolve-Path $SourceDir).Path).AbsoluteUri.TrimEnd("/")
$env:SEMANTIC_HUB_DPPO_TTL_URL = "$dppoDir/{module}.ttl"
Write-Host "SEMANTIC_HUB_DPPO_TTL_URL = $env:SEMANTIC_HUB_DPPO_TTL_URL"

# Refuse to start if another server already uses the port, because the
# warm-up would otherwise hit that server and its source configuration.
try {
    Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/health" -TimeoutSec 2 | Out-Null
    throw "A server is already running on port $Port. Stop it first."
} catch [System.Net.WebException] {
    # Nothing is listening on the port: continue.
}

# The child process inherits the environment variables set above.
Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--port", "$Port" `
    -WorkingDirectory $repoDir

$deadline = (Get-Date).AddSeconds(30)
while ($true) {
    try {
        Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/health" -TimeoutSec 2 | Out-Null
        break
    } catch [System.Net.WebException] {
        if ((Get-Date) -gt $deadline) {
            throw "API did not respond within 30 seconds."
        }
        Start-Sleep -Milliseconds 500
    }
}

Write-Host "Warming up sources:"
foreach ($path in $warmUpPaths) {
    $elapsed = Measure-Command {
        Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl$path" -TimeoutSec 60 | Out-Null
    }
        Write-Host ("  {0,-40} {1,6} ms" -f $path, [int]$elapsed.TotalMilliseconds)
}

Start-Process "$baseUrl/ui/"