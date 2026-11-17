import sys
sys.path.insert(0, r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS")
import api
routes = [r.path for r in api.app.routes if "lotofacil" in getattr(r, "path", "")]
print("Rotas Lotofacil registradas no código atual:")
for r in routes:
    print(" -", r)
