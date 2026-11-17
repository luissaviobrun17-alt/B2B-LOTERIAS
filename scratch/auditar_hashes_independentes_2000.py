# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path

dir_cat = Path("catalogo_lotofacil_10000")
caminho_2000 = dir_cat / "lotofacil_carteira_2000.json"
caminho_man_2000 = dir_cat / "lotofacil_carteira_2000.json.sha256"
caminho_1000 = dir_cat / "lotofacil_carteira_1000.json"
caminho_bkp = Path(r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_2000\lotofacil_carteira_2000.json")

# Leitura física direta de bytes
with open(caminho_2000, "rb") as f:
    raw_2000 = f.read()
sha_fisico_2000 = hashlib.sha256(raw_2000).hexdigest()

doc_2000 = json.loads(raw_2000.decode("utf-8"))
jogos_2000 = doc_2000["jogos"]
sha_jogos_2000 = hashlib.sha256(json.dumps(jogos_2000, separators=(",", ":")).encode("utf-8")).hexdigest()

doc_sem_hash = {k: v for k, v in doc_2000.items() if k != "sha256_documento_catalogo"}
sha_doc_2000 = hashlib.sha256(json.dumps(doc_sem_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

with open(caminho_man_2000, "r", encoding="utf-8") as f:
    manifesto_2000 = f.read().strip()

with open(caminho_bkp, "rb") as f:
    sha_backup_2000 = hashlib.sha256(f.read()).hexdigest()

with open(caminho_1000, "rb") as f:
    sha_fisico_1000 = hashlib.sha256(f.read()).hexdigest()

print("=" * 80)
print("AUDITORIA INDEPENDENTE DE HASHES E INTEGRIDADE FISICA")
print("=" * 80)
print(f"SHA-256 Jogos Canonicos:    {sha_jogos_2000}")
print(f"SHA-256 Estrutural Doc:     {sha_doc_2000}")
print(f"SHA-256 Arquivo Fisico:     {sha_fisico_2000}")
print(f"SHA-256 Backup Isolado:     {sha_backup_2000}")
print(f"Manifesto Gravado:          {manifesto_2000}")
print(f"SHA-256 J=1.000 Preservado: {sha_fisico_1000}")
print("-" * 80)
print(f"Backup == Fisico:           {sha_backup_2000 == sha_fisico_2000}")
print(f"Manifesto == Fisico:        {manifesto_2000.startswith(sha_fisico_2000)}")
print(f"Hash Jogos == Esperado:     {sha_jogos_2000 == 'baf528336b7d935d91262705560c9d7410c8c76987f8a0eddbde82bf5aa93048'}")
print(f"Hash J=1.000 == Esperado:   {sha_fisico_1000 == '9a835a98a2f5a56d806b07683b12dd1ed393d54d6d0ba291ed2084443b2ee595'}")
print(f"Hash Doc == No Documento:   {sha_doc_2000 == doc_2000['sha256_documento_catalogo']}")
print(f"Total de Jogos Lidos:       {len(jogos_2000)}")
print(f"Tamanho do Arquivo:         {len(raw_2000):,} bytes")
print("=" * 80)
