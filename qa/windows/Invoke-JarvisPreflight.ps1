#Requires -Version 5.1
<#
.SYNOPSIS
    VEXEL Jarvis - JAR-SLICE-01C read-only Windows QA preflight.

.DESCRIPTION
    Collects the hardware and software facts needed before the first real Ollama + voice
    test on an authorised QA PC. READ-ONLY by design:

      * installs nothing, downloads nothing, changes no setting, service or registry key;
      * never records audio, never speaks, never opens the microphone;
      * needs no administrator rights (it does not request elevation);
      * the only network access is HTTP GET to the local Ollama port (127.0.0.1) to read
        its version and the names of installed models;
      * collects no tokens, user names, computer names, serial numbers, MAC/IP addresses
        or user files. Strings are passed through a redaction step before being written.

    Output (default .\evidence\jarvis-preflight-<UTC timestamp>\, git-ignored):
      report.txt       human-readable summary
      report.json      machine-readable facts
      transcript.txt   every probe executed, with its sanitised result or error
    Start-Transcript is deliberately NOT used: its header records user and machine names.

.PARAMETER OutputDirectory
    Parent folder for the report. Default: .\evidence (relative to the current folder).

.PARAMETER CopySummary
    Opt-in: copy the technical summary (report.txt content) to the clipboard.

.PARAMETER OllamaPort
    Local Ollama port. Default 11434.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\windows\Invoke-JarvisPreflight.ps1
    (-ExecutionPolicy Bypass applies to this one process only; it changes no policy.)

.NOTES
    Prepared in JAR-SLICE-01C-PRE for review. Not executed by the author.
#>
[CmdletBinding()]
param(
    [string]$OutputDirectory = (Join-Path -Path (Get-Location) -ChildPath 'evidence'),
    [switch]$CopySummary,
    [ValidateRange(1, 65535)][int]$OllamaPort = 11434
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$ScriptVersion = '0.1.0'

# ------------------------------------------------------------------ redaction

# Paths are replaced anywhere; names only as whole words (so "Ana" does not hit "Analog").
$RedactionPairs = @()
foreach ($pair in @(
        @($env:USERPROFILE, '%USERPROFILE%', $false),
        @($env:LOCALAPPDATA, '%LOCALAPPDATA%', $false),
        @($env:APPDATA, '%APPDATA%', $false),
        @($env:USERNAME, '<user>', $true),
        @($env:COMPUTERNAME, '<computer>', $true),
        @($env:USERDOMAIN, '<domain>', $true))) {
    if ($pair[0] -and $pair[0].Length -ge 2) { $RedactionPairs += , $pair }
}

function Protect-Text {
    param([AllowNull()][object]$Value)
    if ($null -eq $Value) { return $null }
    $text = [string]$Value
    foreach ($pair in $RedactionPairs) {
        $pattern = [regex]::Escape($pair[0])
        if ($pair[2]) { $pattern = '(?<![\p{L}\p{N}])' + $pattern + '(?![\p{L}\p{N}])' }
        $text = $text -ireplace $pattern, $pair[1]
    }
    # Device names such as "Ana's AirPods" or "AirPods de Ana" may contain a person's name.
    $text = $text -replace "\b[\p{L}][\p{L}\-]*'s\b", "<name>'s"
    $text = $text -replace '(?i)\b(de|do|da)\s+[\p{Lu}][\p{L}\-]+$', '$1 <name>'
    # Serial-like tokens and network identifiers.
    $text = $text -replace '\b([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b', '<mac>'
    $text = $text -replace '\b(\d{1,3}\.){3}\d{1,3}\b', '<ip>'
    return $text
}

# ------------------------------------------------------------------ transcript

$Transcript = New-Object System.Collections.Generic.List[string]
function Write-Step {
    param([string]$Probe, [string]$Status, [string]$Detail)
    $line = '{0:u} [{1}] {2}: {3}' -f (Get-Date).ToUniversalTime(), $Status, $Probe, (Protect-Text $Detail)
    $Transcript.Add($line)
    Write-Verbose $line
}

function Get-Prop {
    <# StrictMode-safe property read: $null when the property does not exist. #>
    param([AllowNull()][object]$Object, [string]$Name)
    if ($null -eq $Object) { return $null }
    if ($Object -is [System.Collections.IDictionary]) {
        if ($Object.Contains($Name)) { return $Object[$Name] }
        return $null
    }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Invoke-Probe {
    <# Runs one read-only probe; failures are recorded, never fatal. Arrays stay arrays. #>
    param([string]$Name, [scriptblock]$Body)
    try {
        $result = & $Body
        Write-Step -Probe $Name -Status 'OK' -Detail 'collected'
        Write-Output -NoEnumerate $result
        return
    }
    catch {
        $errorType = $_.Exception.GetType().Name
        Write-Step -Probe $Name -Status 'ERROR' -Detail $errorType
        return @{ error = $errorType }
    }
}

# ------------------------------------------------------------------ probes

$Facts = [ordered]@{}
$Facts.preflight = [ordered]@{
    version     = $ScriptVersion
    generated   = (Get-Date).ToUniversalTime().ToString('o')
    elevated    = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    powershell  = $PSVersionTable.PSVersion.ToString()
}

$Facts.windows = Invoke-Probe 'windows' {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    [ordered]@{
        caption      = $os.Caption
        version      = $os.Version
        build        = $os.BuildNumber
        architecture = $os.OSArchitecture
        locale       = (Get-Culture).Name
        ui_language  = (Get-UICulture).Name
    }
}

$Facts.cpu = Invoke-Probe 'cpu' {
    @(Get-CimInstance -ClassName Win32_Processor | ForEach-Object {
            [ordered]@{
                name              = ($_.Name -replace '\s+', ' ').Trim()
                cores             = $_.NumberOfCores
                logical_processors = $_.NumberOfLogicalProcessors
                max_clock_mhz     = $_.MaxClockSpeed
            }
        })
}

$Facts.memory = Invoke-Probe 'memory' {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem
    [ordered]@{
        total_gb = [math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
        free_gb  = [math]::Round($os.FreePhysicalMemory / 1MB, 1)
    }
}

$Facts.gpu = Invoke-Probe 'gpu' {
    # Win32_VideoController.AdapterRAM is capped at 4 GB; the display-class registry key
    # HardwareInformation.qwMemorySize holds the real dedicated memory (read-only access).
    $vram = @{}
    $classKey = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
    Get-ChildItem -Path $classKey -ErrorAction SilentlyContinue | ForEach-Object {
        $props = Get-ItemProperty -Path $_.PSPath -ErrorAction SilentlyContinue
        $desc = Get-Prop $props 'DriverDesc'
        $size = Get-Prop $props 'HardwareInformation.qwMemorySize'
        if ($desc -and $size) {
            $vram[[string]$desc] = [math]::Round([double]$size / 1GB, 1)
        }
    }
    @(Get-CimInstance -ClassName Win32_VideoController | ForEach-Object {
            $name = [string]$_.Name
            [ordered]@{
                name           = $name
                driver_version = $_.DriverVersion
                vram_gb        = $(if ($vram.ContainsKey($name)) { $vram[$name] } else { [math]::Round([double]$_.AdapterRAM / 1GB, 1) })
                vram_source    = $(if ($vram.ContainsKey($name)) { 'registry' } else { 'wmi_capped_4gb' })
            }
        })
}

$Facts.disk = Invoke-Probe 'disk' {
    $drives = @($env:SystemDrive, (Split-Path -Qualifier (Get-Location).Path)) | Select-Object -Unique
    @($drives | ForEach-Object {
            $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter ("DeviceID='{0}'" -f $_)
            [ordered]@{
                drive   = $_
                free_gb = [math]::Round($disk.FreeSpace / 1GB, 1)
                size_gb = [math]::Round($disk.Size / 1GB, 1)
            }
        })
}

$Facts.python = Invoke-Probe 'python' {
    # Native tools may write to stderr; with 'Stop' Windows PowerShell 5.1 would turn that
    # into a terminating error, so native calls in this probe use 'Continue'.
    $ErrorActionPreference = 'Continue'
    $launcher = Get-Command -Name 'py' -CommandType Application -ErrorAction SilentlyContinue
    $installs = @()
    if ($launcher) {
        # "py -0p" only lists registered interpreters; it runs no user code.
        $installs = @(& $launcher.Source -0p 2>$null | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_ })
    }
    $python = Get-Command -Name 'python' -CommandType Application -ErrorAction SilentlyContinue
    $pythonPath = $null
    if ($python) { $pythonPath = $python.Source }
    [ordered]@{
        py_launcher        = [bool]$launcher
        registered         = @($installs | ForEach-Object { Protect-Text $_ })
        has_311            = [bool]($installs | Where-Object { $_ -match '3\.11' })
        python_on_path     = Protect-Text $pythonPath
        store_alias_only   = [bool]($pythonPath -and $pythonPath -match 'WindowsApps')
    }
}

$Facts.ollama = Invoke-Probe 'ollama' {
    $ErrorActionPreference = 'Continue'  # "ollama --version" warns on stderr when no server runs
    $exe = Get-Command -Name 'ollama' -CommandType Application -ErrorAction SilentlyContinue
    $version = $null
    if ($exe) {
        # "ollama --version" prints the client version; it does not start the server.
        $version = ((& $exe.Source --version 2>&1) | Out-String).Trim()
    }
    [ordered]@{
        installed = [bool]$exe
        path      = $(if ($exe) { Protect-Text $exe.Source } else { $null })
        version   = Protect-Text $version
    }
}

$Facts.ollama_port = Invoke-Probe 'ollama_port' {
    $client = New-Object System.Net.Sockets.TcpClient
    $open = $false
    try {
        $async = $client.BeginConnect('127.0.0.1', $OllamaPort, $null, $null)
        $open = $async.AsyncWaitHandle.WaitOne(1500) -and $client.Connected
    }
    finally { $client.Close() }
    $server = $null
    $models = @()
    if ($open) {
        $base = 'http://127.0.0.1:{0}' -f $OllamaPort
        $server = Get-Prop (Invoke-RestMethod -Method Get -Uri "$base/api/version" -TimeoutSec 5) 'version'
        $tags = Invoke-RestMethod -Method Get -Uri "$base/api/tags" -TimeoutSec 5
        $models = @(@(Get-Prop $tags 'models') | Where-Object { $_ } | ForEach-Object {
                [ordered]@{ name = (Get-Prop $_ 'name'); size_gb = [math]::Round([double](Get-Prop $_ 'size') / 1GB, 2) }
            })
    }
    [ordered]@{
        port            = $OllamaPort
        listening       = [bool]$open
        server_version  = $server
        models          = $models
        has_qwen35_4b   = [bool]($models | Where-Object { $_.name -eq 'qwen3.5:4b' })
        has_qwen35_2b   = [bool]($models | Where-Object { $_.name -eq 'qwen3.5:2b' })
    }
}

$Facts.sapi_voices = Invoke-Probe 'sapi_voices' {
    Add-Type -AssemblyName System.Speech
    $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        @($speaker.GetInstalledVoices() | ForEach-Object {
                [ordered]@{
                    name    = $_.VoiceInfo.Name
                    culture = $_.VoiceInfo.Culture.Name
                    gender  = [string]$_.VoiceInfo.Gender
                    age     = [string]$_.VoiceInfo.Age
                    enabled = [bool]$_.Enabled
                }
            })
    }
    finally { $speaker.Dispose() }
}

$Facts.onecore_voices = Invoke-Probe 'onecore_voices' {
    # Voices installed via Settings > Time & Language > Speech (not always visible to SAPI 5).
    $key = 'HKLM:\SOFTWARE\Microsoft\Speech_OneCore\Voices\Tokens'
    @(Get-ChildItem -Path $key -ErrorAction SilentlyContinue | ForEach-Object {
            $props = Get-ItemProperty -Path $_.PSPath -ErrorAction SilentlyContinue
            $attributes = Get-ItemProperty -Path (Join-Path $_.PSPath 'Attributes') -ErrorAction SilentlyContinue
            $display = Get-Prop $props '(default)'
            if (-not $display) { $display = $_.PSChildName }
            [ordered]@{
                name     = [string]$display
                language = Get-Prop $attributes 'Language'
            }
        })
}

$Facts.speech_recognizers = Invoke-Probe 'speech_recognizers' {
    Add-Type -AssemblyName System.Speech
    @([System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() | ForEach-Object { $_.Culture.Name })
}

$Facts.audio = Invoke-Probe 'audio' {
    # Endpoint list from the MMDevices registry (read-only). DeviceState 1 = active.
    $propName = '{a45c254e-df1c-4efd-8020-67d146a850e0},2'
    $propIface = '{b3f8fa53-0004-438e-9003-51a46e139bfc},6'
    $root = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio'
    $endpoints = @()
    foreach ($flow in @('Capture', 'Render')) {
        Get-ChildItem -Path (Join-Path $root $flow) -ErrorAction SilentlyContinue | ForEach-Object {
            $state = Get-Prop (Get-ItemProperty -Path $_.PSPath -ErrorAction SilentlyContinue) 'DeviceState'
            $props = Get-ItemProperty -Path (Join-Path $_.PSPath 'Properties') -ErrorAction SilentlyContinue
            $parts = @()
            foreach ($key in @($propName, $propIface)) {
                $value = Get-Prop $props $key
                if ($value) { $parts += [string]$value }
            }
            $label = ($parts -join ' - ')
            $endpoints += [ordered]@{
                flow   = $(if ($flow -eq 'Capture') { 'input' } else { 'output' })
                name   = Protect-Text $label
                active = ($state -eq 1)
            }
        }
    }
    [ordered]@{
        endpoints      = $endpoints
        active_inputs  = @($endpoints | Where-Object { $_.flow -eq 'input' -and $_.active }).Count
        active_outputs = @($endpoints | Where-Object { $_.flow -eq 'output' -and $_.active }).Count
    }
}

# ------------------------------------------------------------------ evaluation

function Get-Value {
    param([AllowNull()][object]$Object, [string]$Name)
    return (Get-Prop $Object $Name)
}

$gates = New-Object System.Collections.Generic.List[object]
function Add-Gate {
    param([string]$Gate, [string]$Status, [string]$Detail)
    $gates.Add([ordered]@{ gate = $Gate; status = $Status; detail = (Protect-Text $Detail) })
}

$memTotal = Get-Value $Facts.memory 'total_gb'
if ($null -eq $memTotal) { Add-Gate 'RAM' 'UNKNOWN' 'memory probe failed' }
elseif ($memTotal -ge 16) { Add-Gate 'RAM' 'PASS' "$memTotal GB (qwen3.5:4b comfortable)" }
elseif ($memTotal -ge 8) { Add-Gate 'RAM' 'WARN' "$memTotal GB (qwen3.5:4b tight; consider qwen3.5:2b)" }
else { Add-Gate 'RAM' 'FAIL' "$memTotal GB (below 8 GB)" }

$freeSystem = @(@($Facts.disk) | Where-Object { $_ -is [System.Collections.IDictionary] -and -not $_.Contains('error') } | Select-Object -First 1)
if ($freeSystem.Count -gt 0 -and $freeSystem[0].free_gb -ge 15) { Add-Gate 'DISK' 'PASS' ("{0} GB free on {1}" -f $freeSystem[0].free_gb, $freeSystem[0].drive) }
elseif ($freeSystem.Count -gt 0) { Add-Gate 'DISK' 'WARN' ("{0} GB free on {1} (15 GB recommended)" -f $freeSystem[0].free_gb, $freeSystem[0].drive) }
else { Add-Gate 'DISK' 'UNKNOWN' 'disk probe failed' }

if (Get-Value $Facts.python 'has_311') { Add-Gate 'PYTHON_311' 'PASS' 'Python 3.11 registered with py launcher' }
else { Add-Gate 'PYTHON_311' 'FAIL' 'Python 3.11 not found (py -0p)' }

$voices = @(@($Facts.sapi_voices) | Where-Object { $_ -is [System.Collections.IDictionary] -and -not $_.Contains('error') })
$ptVoices = @($voices | Where-Object { $_.enabled -and ([string]$_.culture) -like 'pt-*' })
if ($ptVoices.Count -gt 0) { Add-Gate 'PT_VOICE' 'PASS' (($ptVoices | ForEach-Object { '{0} ({1})' -f $_.name, $_.culture }) -join '; ') }
else {
    $onecorePt = @(@($Facts.onecore_voices) | Where-Object {
            $_ -is [System.Collections.IDictionary] -and -not $_.Contains('error') -and
            (([string](Get-Prop $_ 'name')) -match 'Portug' -or ([string](Get-Prop $_ 'language')) -match '^(816|416)$')
        })
    if ($onecorePt.Count -gt 0) { Add-Gate 'PT_VOICE' 'WARN' 'Portuguese voice only in OneCore (not visible to System.Speech)' }
    else { Add-Gate 'PT_VOICE' 'FAIL' 'no enabled Portuguese SAPI voice' }
}

$inputs = Get-Value $Facts.audio 'active_inputs'
if ($null -eq $inputs) { Add-Gate 'MICROPHONE' 'UNKNOWN' 'audio probe failed' }
elseif ($inputs -gt 0) { Add-Gate 'MICROPHONE' 'PASS' "$inputs active input endpoint(s)" }
else { Add-Gate 'MICROPHONE' 'FAIL' 'no active input endpoint' }

if (Get-Value $Facts.ollama 'installed') { Add-Gate 'OLLAMA_INSTALLED' 'PASS' ([string](Get-Value $Facts.ollama 'version')) }
else { Add-Gate 'OLLAMA_INSTALLED' 'INFO' 'not installed (installation needs authorisation, G3)' }
if (Get-Value $Facts.ollama_port 'listening') {
    if (Get-Value $Facts.ollama_port 'has_qwen35_4b') { Add-Gate 'OLLAMA_MODEL' 'PASS' 'qwen3.5:4b present' }
    else { Add-Gate 'OLLAMA_MODEL' 'INFO' 'server up, qwen3.5:4b not installed' }
}
else { Add-Gate 'OLLAMA_MODEL' 'INFO' "port $OllamaPort not listening" }

if ($Facts.preflight.elevated) { Add-Gate 'PRIVILEGES' 'WARN' 'running elevated; not required - prefer a normal user session' }
else { Add-Gate 'PRIVILEGES' 'PASS' 'standard user' }

$Facts.gates = $gates

# ------------------------------------------------------------------ output

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$target = Join-Path -Path $OutputDirectory -ChildPath ("jarvis-preflight-$stamp")
New-Item -ItemType Directory -Path $target -Force | Out-Null

$summary = New-Object System.Collections.Generic.List[string]
$summary.Add("VEXEL Jarvis - Windows QA preflight $ScriptVersion ($($Facts.preflight.generated))")
$summary.Add(('Windows : {0} {1} build {2} {3}' -f (Get-Value $Facts.windows 'caption'), (Get-Value $Facts.windows 'version'), (Get-Value $Facts.windows 'build'), (Get-Value $Facts.windows 'architecture')))
$summary.Add(('CPU     : {0}' -f ((@($Facts.cpu) | ForEach-Object { Get-Value $_ 'name' }) -join ' | ')))
$summary.Add(('RAM     : {0} GB total, {1} GB free' -f (Get-Value $Facts.memory 'total_gb'), (Get-Value $Facts.memory 'free_gb')))
$summary.Add(('GPU     : {0}' -f ((@($Facts.gpu) | ForEach-Object { '{0} ({1} GB, {2})' -f (Get-Value $_ 'name'), (Get-Value $_ 'vram_gb'), (Get-Value $_ 'vram_source') }) -join ' | ')))
$summary.Add('')
foreach ($gate in $gates) { $summary.Add(('[{0,-7}] {1,-17} {2}' -f $gate.status, $gate.gate, $gate.detail)) }
$summary.Add('')
$summary.Add('Read-only: nothing was installed, downloaded, recorded or changed.')

$summaryText = ($summary | ForEach-Object { Protect-Text $_ }) -join [Environment]::NewLine
Set-Content -Path (Join-Path $target 'report.txt') -Value $summaryText -Encoding UTF8
$json = $Facts | ConvertTo-Json -Depth 8
Set-Content -Path (Join-Path $target 'report.json') -Value (Protect-Text $json) -Encoding UTF8
Set-Content -Path (Join-Path $target 'transcript.txt') -Value ($Transcript -join [Environment]::NewLine) -Encoding UTF8

if ($CopySummary) {
    Set-Clipboard -Value $summaryText
    Write-Host 'Summary copied to the clipboard.'
}

Write-Host $summaryText
Write-Host ''
Write-Host ('Report written to: {0}' -f (Protect-Text $target))
