import feedparser
import openai
import smtplib
from email.mime.text import MIMEText
import schedule
import time
import os
from fastapi import FastAPI
import threading
import uvicorn

# --- CONFIG ENVIRONNEMENT ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

openai.api_key = OPENAI_API_KEY

KEYWORDS = ["menuiserie", "volet", "réhabilitation", "PVC"]

# --- RÉCUPÉRATION DU FLUX BOAMP ---
def fetch_boamp_rss():
    url = "https://www.boamp.fr/flux-rss"
    feed = feedparser.parse(url)
    offers = []
    for entry in feed.entries:
        offers.append({
            "title": entry.title,
            "link": entry.link,
            "summary": entry.summary,
            "published": entry.published
        })
    return offers

# --- ANALYSE GPT AVEC FORMAT JSON ---
def analyze_offer_with_gpt(offer_text, keywords):
    prompt = f"""
Tu es un assistant expert en appels d'offres de menuiseries extérieures.

Ta mission :
1. Indique si OUI ou NON ce texte concerne un lot menuiseries extérieures (avec mots-clés : {', '.join(keywords)}).
2. Si OUI, génère un petit JSON structuré avec les champs suivants :
{{
  "pertinent": true/false,
  "chantier": "...",
  "lot": "...",
  "descriptif": "...",
  "localisation": "...",
  "date_limite": "si précisée"
}}

Voici le texte à analyser :
{offer_text}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()

# --- ENVOI D’EMAIL HTML ---
def send_email(subject, body, to_email, from_email, app_password):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, app_password)
        server.sendmail(from_email, to_email, msg.as_string())

# --- TÂCHE PRINCIPALE : VEILLE + MAIL ---
def daily_boamp_mail():
    print("📡 Récupération du flux BOAMP...")
    offers = fetch_boamp_rss()
    analyses = []

    for offer in offers:
        analysis = analyze_offer_with_gpt(offer["summary"], KEYWORDS)
        html_block = f"""
        <h3>📌 {offer['title']}</h3>
        <p><b>📅 Date :</b> {offer['published']}</p>
        <p><b>🔗 Lien :</b> <a href="{offer['link']}">{offer['link']}</a></p>
        <p><b>📝 Résumé :</b> {offer['summary']}</p>
        <p><b>🧠 Analyse IA :</b><br><pre>{analysis}</pre></p>
        <hr>
        """
        analyses.append(html_block)

    mail_body = "".join(analyses) if analyses else "<p>Aucune offre détectée aujourd’hui.</p>"
    send_email(
        subject="🗂️ Rapport BOAMP quotidien",
        body=mail_body,
        to_email=TO_EMAIL,
        from_email=GMAIL_EMAIL,
        app_password=GMAIL_APP_PASSWORD
    )
    print("✅ Mail envoyé avec succès.")

# --- API + SCHEDULER ---
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "MARCHIA BOAMP veille opérationnelle"}

def run_scheduler():
    print("⏰ Scheduler lancé – tâche planifiée à 07:00")
    schedule.every().day.at("07:00").do(daily_boamp_mail)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Lancer le scheduler dans un thread parallèle
threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    print("🚀 Lancement serveur FastAPI + BOAMP Watchdog")
    uvicorn.run(app, host="0.0.0.0", port=10000)
