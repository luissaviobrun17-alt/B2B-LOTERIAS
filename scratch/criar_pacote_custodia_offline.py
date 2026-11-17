import os
import shutil
import zipfile
import hashlib
from pathlib import Path

def criar_pacote_custodia():
    raiz_bkp = Path(r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_1000")
    caminho_zip = raiz_bkp / "pacote_custodia_offline_lotofacil_1000.zip"
    dir_catalogo = Path(r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS\catalogo_lotofacil_10000")
    scratch_repo = Path(r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS\scratch")
    
    arquivos_incluir = [
        ("lotofacil_carteira_1000.json", dir_catalogo / "lotofacil_carteira_1000.json"),
        ("lotofacil_carteira_1000.json.sha256", dir_catalogo / "lotofacil_carteira_1000.json.sha256"),
        ("PARECER_HOMOLOGACAO_J1000.md", dir_catalogo / "PARECER_HOMOLOGACAO_J1000.md"),
        ("resultado_calibracao_budget_b.json", scratch_repo / "resultado_calibracao_budget_b.json"),
        ("resultado_simulacao_comparativa.json", scratch_repo / "resultado_simulacao_comparativa.json"),
        ("restaurar_catalogo.py", raiz_bkp / "restaurar_catalogo.py"),
    ]
    
    leiame_texto = (
        "PACOTE DE CUSTODIA OFFLINE E INDEPENDENTE: LOTOFACIL MODO 4 (J=1.000)\n"
        "=====================================================================\n"
        "Data de Empacotamento: 16/11/2026\n"
        "Identificador: LOTOFACIL_MODO4_J1000_CANONICA\n"
        "Hash SHA-256 Oficial do Arquivo JSON: 9a835a98a2f5a56d806b07683b12dd1ed393d54d6d0ba291ed2084443b2ee595\n"
        "Hash SHA-256 Jogos Canonicos: 891c598a23399d0efad1d8f84e44e89559603f1f15a5481206e9be417b86d153\n"
        "\n"
        "Instrucoes para Armazenamento Externo:\n"
        "1. Copie este arquivo compactado (.zip) para uma unidade flash USB ou disco externo.\n"
        "2. Para restaurar o catalogo em caso de perda ou corrupcao:\n"
        "   Execute: python restaurar_catalogo.py\n"
    )
    
    with zipfile.ZipFile(caminho_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("LEIAME_CUSTODIA_EXTERNA.txt", leiame_texto)
        for arcname, filepath in arquivos_incluir:
            if not filepath.is_file():
                raise FileNotFoundError(f"Arquivo ausente: {filepath}")
            zf.write(filepath, arcname=arcname)
            
    with open(caminho_zip, "rb") as f:
        hash_zip = hashlib.sha256(f.read()).hexdigest()
        
    caminho_zip_sig = raiz_bkp / "pacote_custodia_offline_lotofacil_1000.zip.sha256"
    with open(caminho_zip_sig, "w", encoding="utf-8") as f:
        f.write(f"{hash_zip}  pacote_custodia_offline_lotofacil_1000.zip\n")
        
    # Copia o pacote tambem para a pasta de auditoria do repositorio
    dir_auditoria = Path(r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS\auditoria\lotofacil_carteira_1000")
    dir_auditoria.mkdir(parents=True, exist_ok=True)
    shutil.copy2(caminho_zip, dir_auditoria / "pacote_custodia_offline_lotofacil_1000.zip")
    shutil.copy2(caminho_zip_sig, dir_auditoria / "pacote_custodia_offline_lotofacil_1000.zip.sha256")
    
    print(f"Pacote de custodia offline criado com sucesso:")
    print(f"  Arquivo: {caminho_zip}")
    print(f"  Tamanho: {caminho_zip.stat().st_size:,} bytes")
    print(f"  SHA-256: {hash_zip}")
    print(f"  Espelhado em: {dir_auditoria / 'pacote_custodia_offline_lotofacil_1000.zip'}")

if __name__ == "__main__":
    criar_pacote_custodia()
