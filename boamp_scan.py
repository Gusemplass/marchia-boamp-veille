import requests
from datetime import datetime, timedelta, timezone

BASES = {
    "boamp": "https://www.boamp.fr/api/explore/v2.1/catalog/datasets/boamp/records",
    "joue":  "https://www.boamp.fr/api/explore/v2.1/catalog/datasets/joue/records",
}
HEADERS = {"User-Agent": "lucidia-boamp-veille/1.0"}

DEFAULT_KW = ["menuiserie","volet","fenetre","fenêtre","porte","garde-corps","persienne","store","PVC","aluminium","bois"]
DEFAULT_ZONES = ["Marseille","Toulon","Aix-en-Provence","Avignon","Cannes","Saint-Étienne","Var","Bouches-du-Rhône","Vaucluse","Alpes-Maritimes","Rhône"]

def fetch(base_url, q, limit=100, offset=0):
    params = {"limit":limit,"offset":offset,"order_by":"-record_timestamp","q":q}
    r = requests.get(base_url, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def scan_source(source, days=1, keywords=None, zones=None, max_pages=5):
    keywords = keywords or DEFAULT_KW
    zones = zones or DEFAULT_ZONES
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    seen = set()
    out = []

    queries = []
    for kw in keywords: queries.append(kw)
    for kw in keywords:
        for z in zones:
            queries.append(f"{kw} {z}")

    for q in queries:
        offset=0; page=0
        while page < max_pages:
            data = fetch(BASES[source], q=q, limit=100, offset=offset)
            recs = data.get("results", [])
            if not recs: break
            for rec in recs:
                rid = rec.get("recordid") or rec.get("id")
                if not rid or rid in seen: continue
                ts = rec.get("record_timestamp")
                if ts:
                    try:
                        tsdt = datetime.fromisoformat(ts.replace("Z","+00:00"))
                        if tsdt < cutoff: continue
                    except: pass
                seen.add(rid)
                f = rec.get("fields", {})
                def pick(*names):
                    for n in names:
                        if n in f and f[n]: return f[n]
                out.append({
                    "source": source,
                    "recordid": rid,
                    "record_timestamp": ts,
                    "publication_date": pick("date_publication","dateparution","publication_date"),
                    "deadline": pick("date_limite","date_limite_reception_offres","date_reponse"),
                    "title": pick("intitule_avis","objet","titre","objet_du_marche","title"),
                    "buyer": pick("organisme","acheteur","maitre_ouvrage","acheteur_nom"),
                    "procedure": pick("procedure","type_procedure"),
                    "nature": pick("nature","type_avis"),
                    "cpv": pick("code_cpv","cpv","cpv_principal"),
                    "department_or_place": pick("code_departement","departement","lieu_execution","lieux_execution"),
                    "url": pick("url_avis","url","lien","link"),
                    "_q": q,
                })
            if len(recs) < 100: break
            offset += 100; page += 1
    return out
