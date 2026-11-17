import os
import sys
import shutil
import hashlib
from pathlib import Path

HASH_ESPERADO_J1000 = "9a835a98a2f5a56d806b07683b12dd1ed393d54d6d0ba291ed2084443b2ee595"

def verificar_hash(arquivo: Path) -> str:
    with open(arquivo, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def restaurar(forcar: bool = False) -> bool:
    backup_dir = Path(r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_1000")
    origem_json = backup_dir / "lotofacil_carteira_1000.json"
    origem_sig = backup_dir / "lotofacil_carteira_1000.json.sha256"
    
    if not origem_json.is_file():
        raise FileNotFoundError(f"Arquivo de backup independente ausente em: {origem_json}")
        
    hash_bkp = verificar_hash(origem_json)
    if hash_bkp != HASH_ESPERADO_J1000:
        raise ValueError(
            f"FALHA DE INTEGRIDADE NO BACKUP: Hash {hash_bkp} diverge do oficial {HASH_ESPERADO_J1000}!"
        )
        
    destino_dir = Path("catalogo_lotofacil_10000").resolve()
    destino_dir.mkdir(parents=True, exist_ok=True)
    destino_json = destino_dir / "lotofacil_carteira_1000.json"
    destino_sig = destino_dir / "lotofacil_carteira_1000.json.sha256"
    
    if destino_json.is_file() and not forcar:
        hash_dest = verificar_hash(destino_json)
        if hash_dest == HASH_ESPERADO_J1000:
            print(f"[OK] Catálogo em {destino_json} já está 100% íntegro (SHA-256: {hash_dest}).")
            return True
        else:
            print(f"[ALERTA] Catálogo em {destino_json} divergente (Hash: {hash_dest}). Restaurando a partir do backup independente...")
            
    shutil.copy2(origem_json, destino_json)
    if origem_sig.is_file():
        shutil.copy2(origem_sig, destino_sig)
        
    hash_restaurado = verificar_hash(destino_json)
    if hash_restaurado != HASH_ESPERADO_J1000:
        raise RuntimeError(f"FALHA NA RESTAURAÇÃO: Hash pós-cópia {hash_restaurado} inválido!")
        
    print(f"[SUCESSO] Catálogo restaurado com integridade comprovada em: {destino_json}")
    print(f"  SHA-256 verificado: {hash_restaurado}")
    return True

if __name__ == "__main__":
    forcar_arg = "--forcar" in sys.argv
    restaurar(forcar=forcar_arg)
