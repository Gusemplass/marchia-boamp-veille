import os, base64, json, msal, requests

GRAPH_SCOPE    = [\"https://graph.microsoft.com/.default\"]
GRAPH_ENDPOINT = \"https://graph.microsoft.com/v1.0\"

def _get_token():
    app = msal.ConfidentialClientApplication(
        os.environ[\"AZURE_CLIENT_ID\"],
        authority=f\"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}\",
        client_credential=os.environ[\"AZURE_CLIENT_SECRET\"],
    )
    result = app.acquire_token_silent(GRAPH_SCOPE, account=None) or app.acquire_token_for_client(scopes=GRAPH_SCOPE)
    if \"access_token\" not in result:
        raise RuntimeError(f\"Graph auth failed: {result}\")
    return result[\"access_token\"]

def send_mail_html(subject, html_body, attachments=None):
    token = _get_token()
    to_list = [x.strip() for x in os.environ[\"TO_EMAILS\"].split(\",\") if x.strip()]
    from_addr = os.environ[\"FROM_ADDRESS\"]
    graph_attachments = []
    for att in (attachments or []):
        graph_attachments.append({
            \"@odata.type\": \"#microsoft.graph.fileAttachment\",
            \"name\": att[\"filename\"],
            \"contentType\": att.get(\"mime\",\"text/plain\"),
            \"contentBytes\": base64.b64encode(att[\"content_bytes\"]).decode(\"utf-8\"),
        })
    payload = {
        \"message\": {
            \"subject\": subject,
            \"body\": { \"contentType\": \"HTML\", \"content\": html_body },
            \"toRecipients\": [{\"emailAddress\": {\"address\": addr}} for addr in to_list],
            \"from\": {\"emailAddress\": {\"address\": from_addr}},
            \"attachments\": graph_attachments
        },
        \"saveToSentItems\": True
    }
    r = requests.post(
        f\"{GRAPH_ENDPOINT}/users/{from_addr}/sendMail\",
        headers={\"Authorization\": f\"Bearer {token}\",\"Content-Type\":\"application/json\"},
        data=json.dumps(payload), timeout=30
    )
    if r.status_code not in (202,200):
        raise RuntimeError(f\"Graph sendMail error: {r.status_code} {r.text}\")
