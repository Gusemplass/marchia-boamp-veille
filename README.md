# MARCHIA BOAMP VEILLE

## Objectif
Script Python pour récupérer les appels d'offres BOAMP quotidiennement, analyser avec ChatGPT selon mots clés, et envoyer un mail résumé sur ta boîte Orange.

---

## Variables d’environnement à définir sur Render (Settings > Environment)

- `OPENAI_API_KEY` : ta clé API OpenAI
- `GMAIL_EMAIL` : ton adresse Gmail utilisée pour l’envoi SMTP
- `GMAIL_APP_PASSWORD` : mot de passe d’application Gmail
- `TO_EMAIL` : ton adresse mail Orange (destination)

---

## Déploiement

1. Crée un dépôt GitHub `marchia-boamp-veille`
2. Pousse ce code dedans
3. Connecte le repo sur Render en créant un service de type **Worker**
4. Ajoute les variables d’environnement
5. Lance le service

---

Le script tourne en continu, envoie un mail chaque jour à 07:00.
