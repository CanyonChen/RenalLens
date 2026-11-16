# Build the poster and one-page report

Run these PowerShell commands from the repository root. The source tables must
already exist in `docs/reanalysis/tables/`, including `eligibility_rules.csv`.
The project build generates that table before drawing the figures.

The figures are vector PDFs drawn by the project's Python environment. The final
poster and report are compiled directly from their LaTeX sources.

## Local Tectonic setup

The verified Windows build used Tectonic 0.17.0. Its official release archive is
`https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-pc-windows-msvc.zip`.
Extract `tectonic.exe` into `.tools/tectonic/`.

Keep the cache and temporary files on the repository drive. This avoids the
Windows cross-drive rename error observed with the default cache location.

```powershell
$env:TECTONIC_CACHE_DIR = Join-Path (Get-Location) '.tools\tectonic-cache'
$env:TEMP = Join-Path (Get-Location) '.tools\tectonic-temp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path `
    $env:TECTONIC_CACHE_DIR, $env:TEMP, `
    '.tools\tex-poster', '.tools\tex-report' | Out-Null
```

Tectonic downloads TeX resources on the first build and reuses its cache later.
The poster uses the Gemini theme's Raleway and Lato font families. If those fonts
are not installed, the following repository-local setup supplies the official
static fonts without changing the system font installation:

```powershell
$fontdir = Join-Path (Get-Location) '.tools\fonts'
New-Item -ItemType Directory -Force -Path $fontdir | Out-Null
foreach ($name in @('Light', 'LightItalic', 'Regular', 'Italic', 'Bold', 'BoldItalic')) {
    Invoke-WebRequest -Uri (
        'https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-' + $name + '.ttf'
    ) -OutFile (Join-Path $fontdir ('Lato-' + $name + '.ttf'))
}
foreach ($name in @('Regular', 'Italic', 'Bold', 'BoldItalic')) {
    Invoke-WebRequest -Uri (
        'https://raw.githubusercontent.com/googlefonts/Raleway/master/fonts/TTF/Raleway-' + $name + '.ttf'
    ) -OutFile (Join-Path $fontdir ('Raleway-' + $name + '.ttf'))
}
$fontpath = $fontdir.Replace('\', '/')
$fontcache = (Join-Path (Get-Location) '.tools\fontconfig-cache').Replace('\', '/')
$config = '<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">' +
    '<fontconfig><dir>' + $fontpath + '</dir><cachedir>' + $fontcache +
    '</cachedir></fontconfig>'
Set-Content -LiteralPath '.tools\fonts.conf' -Value $config -Encoding utf8
$env:FONTCONFIG_FILE = Join-Path (Get-Location) '.tools\fonts.conf'
```

## Generate and compile

```powershell
& '.\.venv\Scripts\python.exe' 'docs\poster\poster_figures.py'
& '.\.venv\Scripts\python.exe' 'docs\report\report_figures.py'
& '.\.tools\tectonic\tectonic.exe' --keep-logs `
    --outdir '.tools\tex-poster' 'docs\poster\main.tex'
if ($LASTEXITCODE -ne 0) { throw 'Poster compilation failed' }
& '.\.tools\tectonic\tectonic.exe' --keep-logs `
    --outdir '.tools\tex-report' 'docs\report\main.tex'
if ($LASTEXITCODE -ne 0) { throw 'Report compilation failed' }
Copy-Item -LiteralPath '.tools\tex-poster\main.pdf' `
    -Destination 'docs\poster\RenalLens_Poster.pdf' -Force
Copy-Item -LiteralPath '.tools\tex-report\main.pdf' `
    -Destination 'docs\report\RenalLens_Report.pdf' -Force
```

Inspect the generated PDFs after changing figures or text. Both deliverables
should remain one page: the poster at 132 x 80 cm and the report at A4.
