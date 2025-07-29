import feedparser
import openai
import smtplib
from email.mime.text import MIMEText
import schedule
import time
import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")

openai.api_key = OPENAI_API_KEY

KEYWORDS = ["menuiserie", "volet", "réhabilitation", "PVC"]

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

def analyze_offer_with_gpt(offer_text, keywords):
    prompt = f"""
    Tu es un expert en appels d'offres menuiserie extérieure.
    Analyse ce texte et dis-moi :
    - Si l'offre concerne les mots clés suivants : {', '.join(keywords)}
    - Résume les points importants.
    Réponds clairement.
    Texte :
    {offer_text}
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

def daily_boamp_mail():
    print("Début de la récupération et analyse BOAMP...")
    offers = fetch_boamp_rss()
    analyses = []
    for offer in offers:
        analysis = analyze_offer_with_gpt(offer["summary"], KEYWORDS)
        analyses.append(
            f"Offre: {offer['title']}\n"
            f"Lien: {offer['link']}\n"
            f"Date: {offer['published']}\n"
            f"Résumé: {offer['summary']}\n"
            f"Analyse: {analysis}"
        )

    mail_body = "\n\n".join(analyses) if analyses else "Aucune offre trouvée."
    send_email(
        subject="Rapport BOAMP quotidien",
        body=mail_body,
        to_email=TO_EMAIL,
        from_email=GMAIL_EMAIL,
        app_password=GMAIL_APP_PASSWORD
    )
    print("Mail envoyé avec succès.")

schedule.every().day.at("07:00").do(daily_boamp_mail)

if __name__ == "__main__":
    print("Agent BOAMP veille démarré...")
    while True:
        schedule.run_pending()
        time.sleep(60)
from fastapi import FastAPI
import threading

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "MARCH.IA tourne en tâche de fond"}

def run_scheduler():
    print("Agent BOAMP veille démarré...")
    schedule.every().day.at("07:00").do(daily_boamp_mail)
    while True:
        schedule.run_pending()
        time.sleep(60)

# Lancer le scheduler dans un thread séparé
threading.Thread(target=run_scheduler, daemon=True).start()
import uvicorn

if __name__ == "__main__":
    print("Lancement serveur FastAPI + tâche BOAMP")
    threading.Thread(target=run_scheduler, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=10000)
