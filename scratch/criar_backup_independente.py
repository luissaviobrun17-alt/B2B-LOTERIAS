import os
import shutil
import hashlib
from pathlib import Path

def main():
    src_dir = Path(r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS\catalogo_lotofacil_10000")
    dst_dir = Path(r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_1000")
    scratch_dir = Path(r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS\scratch")
    
    dst_dir.mkdir(parents=True, exist_ok=True)
    
    arquivos_copiar = [
        (src_dir / "lotofacil_carteira_1000.json", dst_dir / "lotofacil_carteira_1000.json"),
        (src_dir / "lotofacil_carteira_1000.json.sha256", dst_dir / "lotofacil_carteira_1000.json.sha256"),
        (scratch_dir / "resultado_calibracao_budget_b.json", dst_dir / "resultado_calibracao_budget_b.json"),
        (scratch_dir / "resultado_simulacao_comparativa.json", dst_dir / "resultado_simulacao_comparativa.json"),
    ]
    
    print("Iniciando cópia de segurança independente...")
    for orig, dest in arquivos_copiar:
        if not orig.is_file():
            raise FileNotFoundError(f"Arquivo de origem nao encontrado: {orig}")
        shutil.copy2(orig, dest)
        tamanho = dest.stat().st_size
        with open(dest, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        print(f"  Copiado: {dest.name} ({tamanho:,} bytes) | SHA-256: {h}")
        
    print("\nBackup independente concluído com sucesso em:")
    print(f"  {dst_dir}")

if __name__ == "__main__":
    main()
