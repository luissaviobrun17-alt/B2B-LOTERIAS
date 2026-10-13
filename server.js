// ================================================
// B2B Loterias - Servidor Local Automático
// Porta: 8777 | Sem dependências externas (Node puro)
// v2.1 — rota /salvar com detecção multi-desktop, anti-colisão e espelhamento
// ================================================
const http = require('http');
const fs   = require('fs');
const path = require('path');
const url  = require('url');
const os   = require('os');

const PORT = 8777;
const ROOT = __dirname;

// ══════════════════════════════════════════════
// Detecção da Área de Trabalho (Desktop) real e ativa do usuário
// ══════════════════════════════════════════════
function getActiveDesktopPath() {
    if (process.platform === 'win32') {
        try {
            const { execSync } = require('child_process');
            const regOut = execSync('reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\User Shell Folders" /v Desktop', { encoding: 'utf8' });
            const match = regOut.match(/Desktop\s+REG_(?:SZ|EXPAND_SZ)\s+([^\r\n]+)/i);
            if (match && match[1]) {
                let p = match[1].trim();
                p = p.replace(/%USERPROFILE%/i, os.homedir());
                if (fs.existsSync(p)) return p;
            }
        } catch (e) {}
    }
    const localDesktop = path.join(os.homedir(), 'Desktop');
    if (fs.existsSync(localDesktop)) return localDesktop;
    return path.join(os.homedir(), 'Desktop');
}

// Pastas de Desktop secundárias/antigas (usadas apenas para expurgo definitivo quando o usuário deletar)
function getLegacyDesktopPaths() {
    const candidates = [
        path.join(os.homedir(), 'OneDrive', 'Desktop'),
        path.join(os.homedir(), 'OneDrive', 'Área de Trabalho'),
        path.join(os.homedir(), 'Área de Trabalho'),
    ];
    const active = getActiveDesktopPath();
    const legacy = [];
    for (const c of candidates) {
        if (fs.existsSync(c) && c !== active && !legacy.includes(c)) {
            legacy.push(c);
        }
    }
    return legacy;
}

const DESKTOP = getActiveDesktopPath();
const JOGOS_DIR = path.join(DESKTOP, 'LOTERIAS JOGOS SALVOS L99');

// Mapeamento gameKey → nome EXATO da subpasta
const PASTA_POR_JOGO = {
    megasena:    'MEGASENA',
    lotofacil:   'LOTOFACIL',
    quina:       'QUINA',
    duplasena:   'DUPLASENA',
    lotomania:   'LOTOMANIA',
    timemania:   'TIMEMANIA',
    diadesorte:  'DIA DE SORTE',
    milionaria:  'MILIONARIA',
    maismilionaria: 'MILIONARIA',
    supersete:   'SUPERSETE',
    loteca:      'LOTECA',
};

// Obter lista de subpastas candidatas para uma loteria (suporta variações de nomes)
function getCandidateSubPastas(gameKey) {
    const key = (gameKey || '').toLowerCase().trim();
    if (key === 'milionaria' || key === 'maismilionaria' || key === '+milionaria') {
        return ['MILIONARIA', '+MILIONARIA', '+MILIONÁRIA'];
    }
    if (key === 'diadesorte' || key === 'dia de sorte') {
        return ['DIA DE SORTE', 'DIADESORTE'];
    }
    if (key === 'supersete' || key === 'super sete') {
        return ['SUPERSETE', 'SUPER SETE'];
    }
    const primary = PASTA_POR_JOGO[key] || (key ? key.toUpperCase() : '');
    return primary ? [primary] : [];
}

// Garantir que a pasta base e subpastas existem no Desktop ativo
function ensureDirs() {
    try {
        if (!fs.existsSync(JOGOS_DIR)) {
            fs.mkdirSync(JOGOS_DIR, { recursive: true });
        }
        for (const subPasta of Object.values(PASTA_POR_JOGO)) {
            const sp = path.join(JOGOS_DIR, subPasta);
            if (!fs.existsSync(sp)) {
                fs.mkdirSync(sp, { recursive: true });
            }
        }
    } catch (e) {}
}
ensureDirs();


const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js'  : 'application/javascript; charset=utf-8',
  '.css' : 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png' : 'image/png',
  '.jpg' : 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif' : 'image/gif',
  '.svg' : 'image/svg+xml',
  '.ico' : 'image/x-icon',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
  '.ttf' : 'font/ttf',
  '.txt' : 'text/plain; charset=utf-8',
  '.key' : 'text/plain; charset=utf-8',
};

// Função para extrair assinatura de jogos de um arquivo/conteúdo (para anti-duplicidade)
function getGameLinesSignature(text) {
    if (!text) return '';
    const lines = text.split(/\r?\n/);
    const games = [];
    for (const line of lines) {
        const trim = line.trim();
        const m = trim.match(/^Jogo\s+\d+:\s*(.+)$/);
        if (m) {
            games.push(m[1].trim());
        }
    }
    if (games.length > 0) return games.join('\n');
    return text.trim();
}

// ══════════════════════════════════════════════
// ROTA POST /salvar — Salva jogo em todos os desktops
// ══════════════════════════════════════════════
function handleSalvar(req, res) {
    let body = '';
    req.on('data', chunk => { body += chunk.toString(); });
    req.on('end', () => {
        try {
            const data = JSON.parse(body);
            const { gameKey, fileName, content, force } = data;

            if (!gameKey || !fileName || !content) {
                res.writeHead(400, {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                });
                res.end(JSON.stringify({ ok: false, error: 'Dados incompletos' }));
                return;
            }

            // Sanitizar nome do arquivo (remover caracteres inválidos)
            let safeFileName = fileName.replace(/[<>:"/\\|?*]/g, '_').trim();
            if (!safeFileName.endsWith('.txt')) safeFileName += '.txt';

            const subPasta = PASTA_POR_JOGO[gameKey] || gameKey.toUpperCase();
            ensureDirs();

            // ── ANTI-DUPLICIDADE: Se já existir arquivo com os mesmos jogos, não duplica (a menos que force=true) ──
            let existingDuplicate = null;
            const primaryGameDir = path.join(JOGOS_DIR, subPasta);
            const incomingLen = content ? Buffer.byteLength(content, 'utf8') : 0;

            if (!force && incomingLen > 0 && fs.existsSync(primaryGameDir)) {
                try {
                    const cutoff = Date.now() - (15 * 60 * 1000);
                    const incomingSig = getGameLinesSignature(content);
                    if (incomingSig) {
                        const files = fs.readdirSync(primaryGameDir)
                            .filter(f => f.endsWith('.txt') && !f.includes('CONFERIDO'))
                            .map(f => {
                                const full = path.join(primaryGameDir, f);
                                let mtime = 0;
                                let size = 0;
                                try {
                                    const st = fs.statSync(full);
                                    mtime = st.mtimeMs;
                                    size = st.size;
                                } catch (e) {}
                                return { name: f, fullPath: full, mtime, size };
                            })
                            .filter(f => f.mtime >= cutoff)
                            .sort((a, b) => b.mtime - a.mtime)
                            .slice(0, 3);

                        for (const fileObj of files) {
                            if (Math.abs(fileObj.size - incomingLen) > 400) continue;
                            try {
                                const fileText = fs.readFileSync(fileObj.fullPath, 'utf8');
                                const fileSig = getGameLinesSignature(fileText);
                                if (fileSig && fileSig === incomingSig) {
                                    existingDuplicate = fileObj;
                                    break;
                                }
                            } catch (err) {}
                        }
                    }
                } catch (err) {}
            }

            if (existingDuplicate) {
                const dupRelPath = `LOTERIAS JOGOS SALVOS L99\\${subPasta}\\${existingDuplicate.name}`;
                console.log(`[B2B] Anti-duplicidade ativada: jogos já salvos em ${existingDuplicate.fullPath}`);
                res.writeHead(200, {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                });
                res.end(JSON.stringify({
                    ok: true,
                    alreadyExists: true,
                    duplicate: true,
                    path: existingDuplicate.fullPath,
                    fileName: existingDuplicate.name,
                    relativePath: dupRelPath,
                    message: `Estes jogos já foram salvos anteriormente no arquivo ${existingDuplicate.name}`
                }));
                return;
            }

            // Anti-sobrescrita: se existir arquivo com mesmo nome e conteúdo diferente, adiciona sufixo _2, _3...
            let finalFileName = safeFileName;
            let counter = 2;
            const nameWithoutExt = safeFileName.replace(/\.txt$/i, '');

            while (true) {
                const testPath = path.join(JOGOS_DIR, subPasta, finalFileName);
                let collisionFound = false;
                if (fs.existsSync(testPath)) {
                    try {
                        const existing = fs.readFileSync(testPath, 'utf8');
                        if (existing.trim() !== content.trim()) {
                            collisionFound = true;
                        }
                    } catch (e) {}
                }
                if (collisionFound) {
                    finalFileName = `${nameWithoutExt}_${counter}.txt`;
                    counter++;
                } else {
                    break;
                }
            }

            // Grava no Desktop ativo
            const gameDir = path.join(JOGOS_DIR, subPasta);
            if (!fs.existsSync(gameDir)) {
                fs.mkdirSync(gameDir, { recursive: true });
            }
            const primaryFilePath = path.join(gameDir, finalFileName);
            fs.writeFileSync(primaryFilePath, content, 'utf8');

            console.log(`[B2B] ✅ Jogo salvo com sucesso: ${primaryFilePath}`);

            res.writeHead(200, {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            });
            res.end(JSON.stringify({
                ok: true,
                path: primaryFilePath,
                fileName: finalFileName,
                relativePath: `LOTERIAS JOGOS SALVOS L99\\${subPasta}\\${finalFileName}`,
            }));

        } catch (err) {
            console.error('[B2B] Erro ao salvar:', err.message);
            res.writeHead(500, {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            });
            res.end(JSON.stringify({ ok: false, error: err.message }));
        }
    });
}

// ══════════════════════════════════════════════
// ROTA GET /pasta-jogos — Retorna o caminho da pasta
// ══════════════════════════════════════════════
function handlePastaJogos(req, res) {
    res.writeHead(200, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    });
    res.end(JSON.stringify({ path: JOGOS_DIR, allPaths: [JOGOS_DIR] }));
}

// ══════════════════════════════════════════════
// SERVIDOR PRINCIPAL
// ══════════════════════════════════════════════
const server = http.createServer((req, res) => {
    // CORS para requisições locais
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        res.end();
        return;
    }

    // ── Rota de salvar jogo ──────────────────
    if (req.method === 'POST' && req.url === '/salvar') {
        handleSalvar(req, res);
        return;
    }

    // ── Rota de informação da pasta ──────────
    if (req.method === 'GET' && req.url === '/pasta-jogos') {
        handlePastaJogos(req, res);
        return;
    }

    // ── Rota GET /listar-jogos — Lista arquivos unificados da pasta de jogos salvos ──
    if (req.method === 'GET' && req.url.startsWith('/listar-jogos')) {
        const params = new URL(req.url, `http://localhost:${PORT}`).searchParams;
        const gameKey = params.get('gameKey') || '';
        const candidateSubPastas = getCandidateSubPastas(gameKey);
        const primarySubPasta = PASTA_POR_JOGO[gameKey] || candidateSubPastas[0] || (gameKey ? gameKey.toUpperCase() : '');
        try {
            const fileMap = new Map();
            const subPastasToScan = candidateSubPastas.length > 0 ? candidateSubPastas : [''];
            for (const subP of subPastasToScan) {
                const targetDir = subP ? path.join(JOGOS_DIR, subP) : JOGOS_DIR;
                if (fs.existsSync(targetDir)) {
                    const files = fs.readdirSync(targetDir);
                    for (const f of files) {
                        if (f.endsWith('.txt')) {
                            const fullP = path.join(targetDir, f);
                            try {
                                const stat = fs.statSync(fullP);
                                if (!fileMap.has(f) || stat.mtime > fileMap.get(f).modified) {
                                    fileMap.set(f, { name: f, size: stat.size, modified: stat.mtime });
                                }
                            } catch (e) {}
                        }
                    }
                }
            }

            const files = Array.from(fileMap.values())
                .sort((a, b) => new Date(b.modified) - new Date(a.modified));

            const targetDir = primarySubPasta ? path.join(JOGOS_DIR, primarySubPasta) : JOGOS_DIR;
            res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
            res.end(JSON.stringify({ ok: true, files, path: targetDir }));
        } catch (err) {
            res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
            res.end(JSON.stringify({ ok: false, error: err.message }));
        }
        return;
    }

    // ── Rota POST /ler-jogo — Lê conteúdo de um arquivo salvo ──
    if (req.method === 'POST' && req.url === '/ler-jogo') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const fileName = data.fileName || '';
                const safeFileName = path.basename(fileName);
                const candidateSubPastas = getCandidateSubPastas(gameKey);
                const subPastasToSearch = candidateSubPastas.length > 0 ? candidateSubPastas : [''];
                
                let content = null;
                for (const subP of subPastasToSearch) {
                    const targetDir = subP ? path.join(JOGOS_DIR, subP) : JOGOS_DIR;
                    const filePath = path.join(targetDir, safeFileName);
                    if (fs.existsSync(filePath)) {
                        content = fs.readFileSync(filePath, 'utf8');
                        break;
                    }
                }

                if (content === null) {
                    res.writeHead(404, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                    res.end(JSON.stringify({ ok: false, error: 'Arquivo não encontrado' }));
                    return;
                }

                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, content, fileName }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── Rota POST /salvar-conferencia — Salva relatório de conferência ──
    if (req.method === 'POST' && req.url === '/salvar-conferencia') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const content = data.content || '';
                const concurso = data.concurso || 'sem-concurso';
                const subPasta = PASTA_POR_JOGO[gameKey] || (gameKey ? gameKey.toUpperCase() : '');
                
                const now = new Date();
                const pad = n => String(n).padStart(2, '0');
                const dateStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
                const timeStr = `${pad(now.getHours())}-${pad(now.getMinutes())}-${pad(now.getSeconds())}`;
                const fileName = `CONFERIDO_${(subPasta || gameKey).toUpperCase()}_Concurso_${concurso}_${dateStr}_${timeStr}.txt`;
                
                const targetDir = subPasta ? path.join(JOGOS_DIR, subPasta) : JOGOS_DIR;
                if (!fs.existsSync(targetDir)) {
                    fs.mkdirSync(targetDir, { recursive: true });
                }
                const filePath = path.join(targetDir, fileName);
                fs.writeFileSync(filePath, content, 'utf8');
                
                console.log(`[B2B] ✅ Conferência salva: ${filePath}`);
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, path: filePath, fileName }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── Rota POST /marcar-conferido — Renomeia arquivo original com CONFERIDO_ ──
    if (req.method === 'POST' && req.url === '/marcar-conferido') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const fileName = data.fileName || '';
                const safeFileName = path.basename(fileName);
                const candidateSubPastas = getCandidateSubPastas(gameKey);
                const subPastasToSearch = candidateSubPastas.length > 0 ? candidateSubPastas : [''];
                
                if (/^(✅|âœ…|\[CONFERIDO\]|CONFERIDO_)/.test(safeFileName)) {
                    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                    res.end(JSON.stringify({ ok: true, already: true, fileName: safeFileName }));
                    return;
                }
                
                const newName = 'CONFERIDO_' + safeFileName;
                for (const subP of subPastasToSearch) {
                    const targetDir = subP ? path.join(JOGOS_DIR, subP) : JOGOS_DIR;
                    const oldPath = path.join(targetDir, safeFileName);
                    const newPath = path.join(targetDir, newName);
                    if (fs.existsSync(oldPath)) {
                        fs.renameSync(oldPath, newPath);
                    }
                }
                
                console.log(`[B2B] ✅ Arquivo marcado: ${fileName} → ${newName}`);
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, oldName: fileName, newName }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── Rota POST /desmarcar-conferido — Remove o prefixo CONFERIDO_ ──
    if (req.method === 'POST' && req.url === '/desmarcar-conferido') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const fileName = data.fileName || '';
                const safeFileName = path.basename(fileName);
                const candidateSubPastas = getCandidateSubPastas(gameKey);
                const subPastasToSearch = candidateSubPastas.length > 0 ? candidateSubPastas : [''];
                
                const newName = safeFileName.replace(/^(✅|âœ…|\[CONFERIDO\]|CONFERIDO_)+/, '');
                if (newName === safeFileName) {
                    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                    res.end(JSON.stringify({ ok: true, already: true, fileName: safeFileName }));
                    return;
                }
                
                for (const subP of subPastasToSearch) {
                    const targetDir = subP ? path.join(JOGOS_DIR, subP) : JOGOS_DIR;
                    const oldPath = path.join(targetDir, safeFileName);
                    const newPath = path.join(targetDir, newName);
                    if (fs.existsSync(oldPath)) {
                        fs.renameSync(oldPath, newPath);
                    }
                }
                
                console.log(`[B2B] ⏳ Arquivo desmarcado: ${fileName} → ${newName}`);
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, oldName: fileName, newName }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── Rota POST /excluir-arquivo — Exclui arquivo salvo no Desktop e purga em legados ──
    if (req.method === 'POST' && req.url === '/excluir-arquivo') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const fileName = data.fileName || '';
                const safeFileName = path.basename(fileName);
                const candidateSubPastas = getCandidateSubPastas(gameKey);
                const subPastasToSearch = candidateSubPastas.length > 0 ? candidateSubPastas : [''];
                
                const allCheckDirs = [JOGOS_DIR];
                for (const leg of getLegacyDesktopPaths()) {
                    allCheckDirs.push(path.join(leg, 'LOTERIAS JOGOS SALVOS L99'));
                }

                const namesToDelete = [safeFileName];
                if (!safeFileName.includes('CONFERIDO_')) {
                    namesToDelete.push('CONFERIDO_' + safeFileName);
                } else {
                    namesToDelete.push(safeFileName.replace(/^.*?CONFERIDO_/, ''));
                }

                let deletedCount = 0;
                for (const baseDir of allCheckDirs) {
                    for (const subP of subPastasToSearch) {
                        const targetDir = subP ? path.join(baseDir, subP) : baseDir;
                        for (const fn of namesToDelete) {
                            const filePath = path.join(targetDir, fn);
                            if (fs.existsSync(filePath)) {
                                try {
                                    fs.unlinkSync(filePath);
                                    deletedCount++;
                                } catch (e) {}
                            }
                        }
                    }
                }
                
                console.log(`[B2B] 🗑️ Arquivo excluído: ${safeFileName} (${deletedCount} cópias removidas)`);
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, deleted: safeFileName, count: deletedCount }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── Rota POST /excluir-todos — Exclui todos os arquivos da loteria especificada ──
    if (req.method === 'POST' && req.url === '/excluir-todos') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const tipo = data.tipo || 'all';
                const candidateSubPastas = getCandidateSubPastas(gameKey);
                const subPastasToSearch = candidateSubPastas.length > 0 ? candidateSubPastas : [''];
                
                const allCheckDirs = [JOGOS_DIR];
                for (const leg of getLegacyDesktopPaths()) {
                    allCheckDirs.push(path.join(leg, 'LOTERIAS JOGOS SALVOS L99'));
                }

                let deletedCount = 0;
                for (const baseDir of allCheckDirs) {
                    for (const subP of subPastasToSearch) {
                        const targetDir = subP ? path.join(baseDir, subP) : baseDir;
                        if (fs.existsSync(targetDir)) {
                            const files = fs.readdirSync(targetDir);
                            for (const f of files) {
                                if (f.endsWith('.txt')) {
                                    const isChecked = f.includes('CONFERIDO');
                                    const shouldDelete = (tipo === 'all') || (tipo === 'checked' && isChecked) || (tipo === 'pending' && !isChecked);
                                    if (shouldDelete) {
                                        const filePath = path.join(targetDir, f);
                                        try {
                                            fs.unlinkSync(filePath);
                                            deletedCount++;
                                        } catch (e) {}
                                    }
                                }
                            }
                        }
                    }
                }
                
                console.log(`[B2B] 🗑️ Exclusão em massa: ${deletedCount} arquivos de ${gameKey} removidos.`);
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, count: deletedCount }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── Rota POST /abrir-pasta — Abre a pasta física no Windows Explorer ──
    if (req.method === 'POST' && req.url === '/abrir-pasta') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const candidateSubPastas = getCandidateSubPastas(gameKey);
                const primarySubPasta = PASTA_POR_JOGO[gameKey] || candidateSubPastas[0] || '';
                const targetDir = primarySubPasta ? path.join(JOGOS_DIR, primarySubPasta) : JOGOS_DIR;
                
                if (!fs.existsSync(targetDir)) {
                    fs.mkdirSync(targetDir, { recursive: true });
                }
                if (process.platform === 'win32') {
                    const { exec } = require('child_process');
                    exec(`start "" "${targetDir}"`);
                }
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, path: targetDir }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── Rota POST /atualizar-arquivo — Regrava arquivo com jogos atualizados ──
    if (req.method === 'POST' && req.url === '/atualizar-arquivo') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
            try {
                const data = JSON.parse(body);
                const gameKey = data.gameKey || '';
                const fileName = data.fileName || '';
                const content = data.content || '';
                const safeFileName = path.basename(fileName);
                const candidateSubPastas = getCandidateSubPastas(gameKey);
                const subPastasToSearch = candidateSubPastas.length > 0 ? candidateSubPastas : [''];
                
                for (const subP of subPastasToSearch) {
                    const targetDir = subP ? path.join(JOGOS_DIR, subP) : JOGOS_DIR;
                    const filePath = path.join(targetDir, safeFileName);
                    if (fs.existsSync(filePath)) {
                        fs.writeFileSync(filePath, content, 'utf8');
                    }
                }
                
                console.log(`[B2B] 💾 Arquivo atualizado: ${safeFileName}`);
                res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: true, fileName: safeFileName }));
            } catch (err) {
                res.writeHead(500, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
                res.end(JSON.stringify({ ok: false, error: err.message }));
            }
        });
        return;
    }

    // ── /gerar-zip → redireciona para ZIP do GitHub ──────────────────────
    if (req.url === '/gerar-zip' || req.url.startsWith('/gerar-zip?')) {
        const zipUrl = 'https://github.com/luissaviobrun17-alt/loterias-caixa/archive/refs/heads/main.zip';
        res.writeHead(302, { 'Location': zipUrl });
        res.end();
        console.log('[B2B] 📦 Redirecionando download ZIP → GitHub');
        return;
    }

    // ── Arquivos estáticos ───────────────────
    let pathname = url.parse(req.url).pathname;
    pathname = path.normalize(pathname).replace(/^(\.\.[\\/])+/, '');
    if (pathname === '/' || pathname === '') pathname = '/index.html';

    const filePath = path.join(ROOT, pathname);
    if (!filePath.startsWith(ROOT)) {
        res.writeHead(403); res.end('Proibido'); return;
    }

    fs.stat(filePath, (err, stat) => {
        if (err || !stat.isFile()) {
            const fallback = path.join(ROOT, 'index.html');
            fs.readFile(fallback, (e2, data) => {
                if (e2) { res.writeHead(404); res.end('Não encontrado'); return; }
                res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
                res.end(data);
            });
            return;
        }

        const ext  = path.extname(filePath).toLowerCase();
        const mime = MIME[ext] || 'application/octet-stream';

        res.writeHead(200, {
            'Content-Type'  : mime,
            'Content-Length': stat.size,
            'Cache-Control' : 'no-cache, no-store, must-revalidate',
            'Pragma'        : 'no-cache',
            'Expires'       : '0',
        });

        fs.createReadStream(filePath).pipe(res);
    });
});

server.listen(PORT, '0.0.0.0', () => {
    const pastaMsg = `\n  📁 Jogos salvos em: ${JOGOS_DIR}\n`;
    console.log(`[B2B Loterias] Servidor rodando em http://localhost:${PORT}`);
    const nets = os.networkInterfaces();
    for (const name of Object.keys(nets)) {
        for (const net of nets[name]) {
            if (net.family === 'IPv4' && !net.internal) {
                console.log(`[B2B Loterias] 🌐 Acesso pela rede: http://${net.address}:${PORT}`);
            }
        }
    }
    console.log(pastaMsg);
});

server.on('error', (err) => {
    if (err.code === 'EADDRINUSE') {
        console.log(`[B2B Loterias] Porta ${PORT} já em uso - servidor ativo.`);
        process.exit(0);
    } else {
        console.error('[B2B Loterias] Erro no servidor:', err.message);
        process.exit(1);
    }
});

process.on('SIGTERM', () => { server.close(); process.exit(0); });
process.on('SIGINT',  () => { server.close(); process.exit(0); });
