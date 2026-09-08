"""Módulo de download e atualização dos dados oficiais da Caixa para Super Sete."""
import urllib.request
import json
import os

URL_OFICIAL_GITHUB = "https://raw.githubusercontent.com/guilhermeasn/loteria.json/master/data/supersete.json"

def atualizar_dados_supersete(destino=None):
    if destino is None:
        destino = os.path.join(os.path.dirname(__file__), "supersete.json")
    req = urllib.request.Request(URL_OFICIAL_GITHUB, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return len(data)

if __name__ == "__main__":
    n = atualizar_dados_supersete()
    print(f"Dados atualizados com sucesso: {n} concursos.")
