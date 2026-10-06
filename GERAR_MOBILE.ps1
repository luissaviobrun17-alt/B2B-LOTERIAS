# ============================================
# GERAR VERSÃO MOBILE - B2B Loterias
# V10 — Compatível com iOS Safari + Android
# ============================================
$ErrorActionPreference = "Stop"
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputFile = Join-Path $baseDir "B2B_Loterias_Mobile.html"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  B2B Loterias - Gerador Versao Mobile  " -ForegroundColor Cyan
Write-Host "  V10 - iOS + Android                   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Ler o HTML original
Write-Host "[1/7] Lendo HTML original..." -ForegroundColor Yellow
$htmlContent = Get-Content -Path (Join-Path $baseDir "index.html") -Raw -Encoding UTF8

# 2. Converter logo para Base64
Write-Host "[2/7] Convertendo logo para Base64..." -ForegroundColor Yellow
$logoPath = Join-Path $baseDir "img\logo_atom.png"
if (Test-Path $logoPath) {
    $logoBytes = [System.IO.File]::ReadAllBytes($logoPath)
    $logoBase64 = [System.Convert]::ToBase64String($logoBytes)
    $logoDataUri = "data:image/png;base64,$logoBase64"
    $htmlContent = $htmlContent -replace 'src="img/logo_atom\.png"', "src=`"$logoDataUri`""
    Write-Host "   Logo convertido ($(($logoBytes.Length / 1024).ToString('N0')) KB)" -ForegroundColor Green
} else {
    Write-Host "   Logo nao encontrado, pulando..." -ForegroundColor Red
}

# 3. NOVO: Substituir Google Fonts por fontes inline (iOS offline fix)
Write-Host "[3/7] Removendo dependencias externas (Google Fonts)..." -ForegroundColor Yellow
$fontFallback = @"
<style>
/* Google Fonts fallback — funciona offline no iOS */
@font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: local('Inter'), local('Inter-Regular'), local('-apple-system'), local('BlinkMacSystemFont');
}
@font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: local('Inter SemiBold'), local('Inter-SemiBold'), local('-apple-system'), local('BlinkMacSystemFont');
}
@font-face {
    font-family: 'Inter';
    font-style: normal;
    font-weight: 800;
    font-display: swap;
    src: local('Inter ExtraBold'), local('Inter-ExtraBold'), local('-apple-system'), local('BlinkMacSystemFont');
}
</style>
"@
$htmlContent = $htmlContent -replace '<link[^>]*fonts\.googleapis\.com[^>]*>', $fontFallback
Write-Host "   Google Fonts substituido por fontes locais" -ForegroundColor Green

# 4. Substituir CSS externos por inline
Write-Host "[4/7] Embutindo CSS..." -ForegroundColor Yellow
$cssFiles = @(
    "styles/main.css",
    "styles/components.css",
    "styles/lottery.css",
    "styles/responsive.css"
)

foreach ($cssFile in $cssFiles) {
    $cssPath = Join-Path $baseDir $cssFile
    if (Test-Path $cssPath) {
        $cssContent = Get-Content -Path $cssPath -Raw -Encoding UTF8
        # Remover referências a imagens externas
        $cssContent = $cssContent -replace "url\('\.\./img/header-studio-bg\.png'\)", "url('')"
        $cssContent = $cssContent -replace 'url\("\.\./img/header-studio-bg\.png"\)', "url('')"
        
        $styleBlock = "<style>/* $cssFile */`n$cssContent</style>"
        $basename = [System.IO.Path]::GetFileName($cssFile)
        $htmlContent = $htmlContent -replace "<link[^>]*$basename[^>]*>", $styleBlock
        
        Write-Host "   Embutido: $cssFile" -ForegroundColor Green
    } else {
        Write-Host "   Nao encontrado: $cssFile" -ForegroundColor Red
    }
}

# 5. Substituir JS externos por inline (INCLUI smart_bets.js!)
Write-Host "[5/7] Embutindo JavaScript..." -ForegroundColor Yellow
$jsFiles = @(
    @{ path = "js/engines/games.js"; pattern = 'games\.js' },
    @{ path = "js/data/history_db.js"; pattern = 'history_db\.js' },
    @{ path = "js/stats.js"; pattern = 'stats\.js' },
    @{ path = "js/engines/combinations.js"; pattern = 'combinations\.js' },
    @{ path = "js/engines/quantum.js"; pattern = 'quantum\.js"' },
    @{ path = "js/engines/quantum_god_mode.js"; pattern = 'quantum_god_mode\.js' },
    @{ path = "js/engines/smart_bets.js"; pattern = 'smart_bets\.js' },
    @{ path = "js/engines/motor_megasena_engine.js"; pattern = 'motor_megasena_engine\.js' },
    @{ path = "js/engines/motor_supersete_engine.js"; pattern = 'motor_supersete_engine\.js' },
    @{ path = "js/engines/motor_duplasena_engine.js"; pattern = 'motor_duplasena_engine\.js' },
@{ path = "js/engines/motor_quina_engine.js"; pattern = 'motor_quina_engine\.js' },
    @{ path = "js/engines/motor_lotofacil_engine.js"; pattern = 'motor_lotofacil_engine\.js' },
    @{ path = "js/engines/motor_lotomania_engine.js"; pattern = 'motor_lotomania_engine\.js' },
    @{ path = "js/engines/motor_diadesorte_engine.js"; pattern = 'motor_diadesorte_engine\.js' },
    @{ path = "js/engines/motor_timemania_engine.js"; pattern = 'motor_timemania_engine\.js' },
    @{ path = "js/engines/motor_milionaria_engine.js"; pattern = 'motor_milionaria_engine\.js' },
    @{ path = "js/engines/motor_loteca_engine.js"; pattern = 'motor_loteca_engine\.js' },
    @{ path = "js/ui.js"; pattern = 'ui\.js' },
    @{ path = "js/main.js"; pattern = 'main\.js' },
    @{ path = "js/license.js"; pattern = 'license\.js' }
)

foreach ($jsInfo in $jsFiles) {
    $jsPath = Join-Path $baseDir $jsInfo.path
    if (Test-Path $jsPath) {
        $jsContent = Get-Content -Path $jsPath -Raw -Encoding UTF8
        $scriptBlock = "<script>/* $($jsInfo.path) */`n$jsContent</script>"
        
        $htmlContent = $htmlContent -replace "<script[^>]*$($jsInfo.pattern)[^>]*></script>", $scriptBlock
        
        Write-Host "   Embutido: $($jsInfo.path)" -ForegroundColor Green
    } else {
        Write-Host "   Nao encontrado: $($jsInfo.path)" -ForegroundColor Red
    }
}

# 6. NOVO: Injetar fix de compatibilidade iOS/Android
Write-Host "[6/7] Injetando fix de compatibilidade iOS..." -ForegroundColor Yellow
$iosFix = @"
<script>
/* Mobile Touch Fix — B2B Loterias V10 */
(function() {
    'use strict';
    
    // Fix 1: iOS Safari viewport height (100vh bug)
    function fixVH() {
        var vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', vh + 'px');
    }
    fixVH();
    window.addEventListener('resize', fixVH);
    
    // Fix 2: Garantir meta viewport
    if (!document.querySelector('meta[name="viewport"]')) {
        var meta = document.createElement('meta');
        meta.name = 'viewport';
        meta.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
        document.head.appendChild(meta);
    }
    
    // Fix 3: FASTCLICK — Eliminar delay de 300ms no iOS
    // Converte touch em click imediato para todos os elementos interativos
    var touchStartX = 0, touchStartY = 0, touchMoved = false;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
        touchMoved = false;
    }, { passive: true });
    
    document.addEventListener('touchmove', function(e) {
        if (Math.abs(e.touches[0].clientX - touchStartX) > 10 || 
            Math.abs(e.touches[0].clientY - touchStartY) > 10) {
            touchMoved = true;
        }
    }, { passive: true });
    
    document.addEventListener('touchend', function(e) {
        if (touchMoved) return; // Foi scroll, não click
        
        var target = e.target;
        // Subir até encontrar um elemento clicável
        while (target && target !== document.body) {
            if (target.tagName === 'BUTTON' || target.tagName === 'A' || target.tagName === 'SELECT' || target.tagName === 'INPUT' ||
                target.classList.contains('nav-btn') || target.classList.contains('grid-num') || 
                target.classList.contains('stat-toggle') || target.classList.contains('action-btn') ||
                target.classList.contains('secondary-btn') || target.classList.contains('smart-ia-btn') ||
                target.classList.contains('quantum-btn') || target.classList.contains('sm-btn') ||
                target.classList.contains('sidebar-modern-btn') || target.classList.contains('share-menu-item') ||
                target.classList.contains('copy-single-btn') || target.classList.contains('ball') ||
                target.onclick || target.getAttribute('data-game') || target.getAttribute('data-range') ||
                target.getAttribute('data-number')) {
                // Disparar click imediatamente
                e.preventDefault();
                target.click();
                return;
            }
            target = target.parentElement;
        }
    }, { passive: false });
    
    // Fix 4: CSS touch-action para elementos interativos
    var style = document.createElement('style');
    style.textContent = 'button,a,.nav-btn,.grid-num,.stat-toggle,.action-btn,.secondary-btn,.sm-btn,.ball,.sidebar-modern-btn,.quantum-btn,.smart-ia-btn,.copy-single-btn,.share-menu-item,select,input{touch-action:manipulation;-webkit-tap-highlight-color:rgba(0,0,0,0);cursor:pointer;}nav{overflow-x:auto;-webkit-overflow-scrolling:touch;}';
    document.head.appendChild(style);
    
    // Fix 5: Console polyfill
    if (typeof console === 'undefined') {
        window.console = { log: function(){}, warn: function(){}, error: function(){} };
    }
    
    console.log('[B2B Mobile] Touch fix + FastClick loaded');
})();
</script>
"@
# Inserir logo após <body>
$htmlContent = $htmlContent -replace '<body>', "<body>`n$iosFix"
Write-Host "   Fix iOS/Android injetado" -ForegroundColor Green

# 7. Salvar e criar ZIP
Write-Host "[7/7] Salvando arquivo mobile..." -ForegroundColor Yellow
[System.IO.File]::WriteAllText($outputFile, $htmlContent, [System.Text.Encoding]::UTF8)

$fileSize = (Get-Item $outputFile).Length
$fileSizeKB = [math]::Round($fileSize / 1024, 1)
$fileSizeMB = [math]::Round($fileSize / 1048576, 2)

# Criar ZIP
$zipFile = Join-Path $baseDir "B2B_Loterias_Mobile.zip"
if (Test-Path $zipFile) { Remove-Item $zipFile -Force }
$filesToZip = @($outputFile)
$leiaMe = Join-Path $baseDir "LEIA-ME_MOBILE.txt"
if (Test-Path $leiaMe) { $filesToZip += $leiaMe }
Compress-Archive -Path $filesToZip -DestinationPath $zipFile -Force
$zipSize = (Get-Item $zipFile).Length
$zipSizeKB = [math]::Round($zipSize / 1024, 1)

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Arquivos gerados:" -ForegroundColor White
Write-Host "  HTML: B2B_Loterias_Mobile.html (${fileSizeMB} MB)" -ForegroundColor Cyan
Write-Host "  ZIP:  B2B_Loterias_Mobile.zip  (${zipSizeKB} KB)" -ForegroundColor Cyan
Write-Host ""
Write-Host "  COMO ENVIAR PARA O CELULAR:" -ForegroundColor Yellow
Write-Host "  1. Envie o arquivo ZIP (nao o HTML!)" -ForegroundColor White
Write-Host "     via WhatsApp, Email, Google Drive, etc." -ForegroundColor White
Write-Host "  2. No celular, descompacte o ZIP" -ForegroundColor White
Write-Host "  3. Abra o HTML no navegador (Safari/Chrome)" -ForegroundColor White
Write-Host ""
Write-Host "  IMPORTANTE: Envie o .ZIP, nao o .HTML!" -ForegroundColor Red
Write-Host "  O WhatsApp e iMessage corrompem arquivos HTML." -ForegroundColor Red
Write-Host ""
Write-Host "========================================" -ForegroundColor Green

if ($host.Name -eq "ConsoleHost" -and [Environment]::UserInteractive -and ($args -notcontains "-NoWait")) {
    Start-Process explorer.exe -ArgumentList "/select, `"$zipFile`""
}
