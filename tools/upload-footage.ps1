# Compresses every video from a local folder and pushes it to the fish repo,
# so the cloud session can edit it. Run in PowerShell:
#   irm https://raw.githubusercontent.com/akezzuo-lgtm/fish/claude/100-bucks-credits-9ya5g5/tools/upload-footage.ps1 | iex

$ErrorActionPreference = "Stop"
$Source = Join-Path $env:USERPROFILE "Downloads\агропродмаш\агропродмаш"
$Repo = Join-Path $env:USERPROFILE "fish"
$RepoUrl = "https://github.com/akezzuo-lgtm/fish.git"
$Branch = "claude/100-bucks-credits-9ya5g5"
$BatchLimitMB = 400

$VideoExt = ".mp4", ".mov", ".avi", ".mkv", ".m4v", ".3gp", ".mts", ".webm", ".wmv"
$ImageExt = ".jpg", ".jpeg", ".png", ".webp", ".heic"

function Fail($msg) { Write-Host $msg -ForegroundColor Red; throw $msg }

foreach ($tool in "git", "ffmpeg") {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
    Fail "Не найден $tool. Установите: winget install Git.Git Gyan.FFmpeg  — затем откройте новое окно PowerShell и запустите команду снова."
  }
}

while (-not (Test-Path -LiteralPath $Source)) {
  $Source = Read-Host "Папка не найдена. Вставьте полный путь к папке с видео"
}

# Footage of real people should not sit in a public repo.
try {
  $info = Invoke-RestMethod "https://api.github.com/repos/akezzuo-lgtm/fish"
  if (-not $info.private) {
    Write-Host ""
    Write-Host "ВНИМАНИЕ: репозиторий fish сейчас ПУБЛИЧНЫЙ — видео увидит любой." -ForegroundColor Yellow
    Write-Host "Сделайте его приватным: https://github.com/akezzuo-lgtm/fish/settings -> Danger Zone -> Change visibility -> Private" -ForegroundColor Yellow
    Read-Host "Когда сделаете (или если вас это устраивает), нажмите Enter"
  }
} catch { }

if (-not (Test-Path (Join-Path $Repo ".git"))) {
  git clone --branch $Branch $RepoUrl $Repo
  if ($LASTEXITCODE) { Fail "git clone не удался" }
}
git -C $Repo checkout $Branch
git -C $Repo pull origin $Branch
if ($LASTEXITCODE) { Fail "git pull не удался" }

$Dest = Join-Path $Repo "footage\agroprodmash"
New-Item -ItemType Directory -Force $Dest | Out-Null

function Push-Batch($n) {
  git -C $Repo add footage
  git -C $Repo diff --cached --quiet
  if ($LASTEXITCODE -eq 0) { return }
  git -C $Repo commit -m "Add Agroprodmash footage (batch $n)"
  for ($try = 1; $try -le 4; $try++) {
    git -C $Repo push origin $Branch
    if ($LASTEXITCODE -eq 0) { return }
    Start-Sleep -Seconds ([math]::Pow(2, $try))
  }
  Fail "git push не удался"
}

$files = @(Get-ChildItem -LiteralPath $Source -Recurse -File)
$batch = 1
$batchBytes = 0
$i = 0
foreach ($f in $files) {
  $i++
  $rel = $f.FullName.Substring($Source.TrimEnd('\').Length).TrimStart('\')
  $ext = $f.Extension.ToLower()

  if ($VideoExt -contains $ext) {
    $out = Join-Path $Dest ([IO.Path]::ChangeExtension($rel, ".mp4"))
    New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
    if (Test-Path -LiteralPath $out) { continue }
    Write-Host "[$i/$($files.Count)] видео: $rel"
    # Long side up to 1920, H.264 — small enough for git, good enough for a 1080x1920 edit.
    ffmpeg -hide_banner -loglevel error -y -i $f.FullName `
      -vf "scale=1920:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=30" `
      -c:v libx264 -preset fast -crf 26 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart $out
    if ($LASTEXITCODE) { Write-Host "  пропущено: ffmpeg не смог прочитать файл" -ForegroundColor Yellow; Remove-Item -LiteralPath $out -ErrorAction SilentlyContinue; continue }
    if ((Get-Item -LiteralPath $out).Length -gt 95MB) {
      Write-Host "  файл большой, пережимаю сильнее"
      ffmpeg -hide_banner -loglevel error -y -i $f.FullName `
        -vf "scale=1280:1280:force_original_aspect_ratio=decrease:force_divisible_by=2,fps=30" `
        -c:v libx264 -preset fast -crf 30 -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart $out
    }
    if ((Get-Item -LiteralPath $out).Length -gt 95MB) {
      Write-Host "  пропущено: слишком длинное видео (>95 МБ даже после сжатия)" -ForegroundColor Yellow
      Remove-Item -LiteralPath $out
      continue
    }
  } elseif ($ImageExt -contains $ext -and $f.Length -lt 50MB) {
    $out = Join-Path $Dest $rel
    New-Item -ItemType Directory -Force (Split-Path $out) | Out-Null
    if (Test-Path -LiteralPath $out) { continue }
    Write-Host "[$i/$($files.Count)] фото: $rel"
    Copy-Item -LiteralPath $f.FullName $out
  } else {
    continue
  }

  $batchBytes += (Get-Item -LiteralPath $out).Length
  if ($batchBytes -gt $BatchLimitMB * 1MB) {
    Push-Batch $batch
    $batch++
    $batchBytes = 0
  }
}
Push-Batch $batch

Write-Host ""
Write-Host "Готово! Все файлы загружены в репозиторий. Напишите в чат, что можно начинать." -ForegroundColor Green
