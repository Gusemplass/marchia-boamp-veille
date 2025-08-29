import os
from openai import OpenAI

SYSTEM = (
  "Tu es un assistant marchés publics menuiseries extérieures. "
  "Résume des avis BOAMP/JOUE en puces actionnables (objet, MOA, deadline, lieu, lot menuiseries, CPV si présent)."
)

def summarize_items(items):
    if not items:
        return "Aucun avis sur les dernières 24h."
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    bullets = []
    for it in items[:20]:
        bullets.append(
            f"- {it.get('title') or '(Sans titre)'} | "
            f"{it.get('buyer') or '?'} | "
            f"DL: {it.get('deadline') or '?'} | "
            f"Lieu: {it.get('department_or_place') or '?'} | "
            f"<a href='{it.get('url') or '#'}'>Lien</a>"
        )
    content = "\n".join(bullets)
    prompt = ("Voici une liste d'avis:\n" + content +
              "\n\nProduis un résumé en 8-12 puces max, puis une section '⚠ À traiter en priorité' (3 items max).")
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
