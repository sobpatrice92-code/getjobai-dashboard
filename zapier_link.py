"""
zapier_link.py — Automatisations Zapier (côté dashboard).
=========================================================
Appelle le backend (gestion des webhooks Zapier). Aucune clé secrète ici : on
signe un jeton court HMAC (APP_HMAC_SECRET partagé), comme billing.py / notion_link.py.
"""
import hashlib
import hmac
import os
import time

import httpx
import streamlit as st

# Familles affichées -> types d'événements backend
FAMILLES = {
    "📤 Candidatures (création + changement de statut)":
        ["candidature.created", "candidature.status_changed"],
    "🤝 Réseau / contacts (nouveau contact + statut)":
        ["contact.created", "contact.statut_changed"],
    "🎤 Entretiens (entretien planifié)":
        ["entretien.planifie"],
    "📨 Réponses RH (refus / convocation / accusé)":
        ["rh.reponse"],
}


def enabled() -> bool:
    return bool(os.getenv("BACKEND_URL"))


def _backend_url() -> str:
    return os.getenv("BACKEND_URL", "").rstrip("/")


def _sign(user_id: str, ttl: int = 600) -> str:
    secret = os.getenv("APP_HMAC_SECRET", "")
    exp = int(time.time()) + ttl
    sig = hmac.new(secret.encode(), f"{user_id}.{exp}".encode(),
                   hashlib.sha256).hexdigest()[:32]
    return f"{exp}.{sig}"


def list_hooks(user_id: str) -> list:
    try:
        r = httpx.get(f"{_backend_url()}/zapier/hooks",
                      params={"user_id": user_id, "token": _sign(user_id)}, timeout=15)
        return r.json().get("hooks", []) if r.status_code == 200 else []
    except Exception:
        return []


def add_hook(user_id: str, url: str, events: list) -> bool:
    try:
        r = httpx.post(f"{_backend_url()}/zapier/hooks",
                       json={"user_id": user_id, "token": _sign(user_id),
                             "target_url": url, "events": events}, timeout=15)
        return r.status_code == 200
    except Exception:
        return False


def _post(path: str, user_id: str, hook_id: str) -> bool:
    try:
        r = httpx.post(f"{_backend_url()}{path}",
                       json={"user_id": user_id, "token": _sign(user_id), "id": hook_id},
                       timeout=15)
        return r.status_code == 200
    except Exception:
        return False


def render_panel(user_id: str) -> None:
    if not enabled():
        st.info("Les automatisations Zapier ne sont pas encore activées sur ce compte.")
        return

    st.markdown(
        "Connectez GetJobAI à **9000+ applications** (Slack, Gmail, Google "
        "Calendar, Sheets, Notion, Trello…) via Zapier. À chaque événement "
        "(candidature, entretien, réponse RH, contact), GetJobAI prévient votre Zap.")

    with st.expander("① Comment obtenir l'URL Zapier (1 fois)", expanded=False):
        st.markdown(
            "1. Sur **zapier.com**, créez un Zap.\n"
            "2. Trigger = **« Webhooks by Zapier »** → événement **« Catch Hook »**.\n"
            "3. Zapier affiche une **Custom Webhook URL** "
            "(`https://hooks.zapier.com/...`) → **copiez-la**.\n"
            "4. Collez-la ci-dessous et choisissez vos événements.\n"
            "5. Ajoutez ensuite l'action voulue dans Zapier (envoyer un Slack, "
            "créer un événement Google Calendar, ajouter une ligne Sheets…).")

    st.markdown("### ➕ Ajouter une automatisation")
    url = st.text_input("URL du webhook Zapier", placeholder="https://hooks.zapier.com/hooks/catch/...",
                        key="zap_url")
    st.caption("Événements à envoyer vers ce webhook :")
    chosen = []
    for label, evs in FAMILLES.items():
        if st.checkbox(label, key=f"zap_{evs[0]}"):
            chosen.extend(evs)
    if st.button("Enregistrer l'automatisation", type="primary", use_container_width=True):
        if not url.startswith("https://hooks.zapier.com") and ".zapier.com" not in url:
            st.error("L'URL doit être un webhook Zapier (https://hooks.zapier.com/...).")
        elif not chosen:
            st.error("Cochez au moins un type d'événement.")
        elif add_hook(user_id, url, chosen):
            st.success("✅ Automatisation enregistrée. Déclenchez un événement (ou "
                       "« Tester » ci-dessous) pour valider côté Zapier.")
            st.rerun()
        else:
            st.error("Échec de l'enregistrement (URL Zapier invalide ?).")

    hooks = list_hooks(user_id)
    if hooks:
        st.markdown("### 🔌 Mes automatisations actives")
        for h in hooks:
            with st.container(border=True):
                st.markdown(f"**…{h['target_url'][-28:]}**")
                st.caption("Événements : " + ", ".join(h.get("events", [])))
                c1, c2 = st.columns(2)
                if c1.button("🧪 Tester", key=f"zt_{h['id']}", use_container_width=True):
                    if _post("/zapier/test", user_id, h["id"]):
                        st.toast("Événement de test envoyé à Zapier ✅")
                    else:
                        st.error("Envoi de test échoué.")
                if c2.button("🗑️ Supprimer", key=f"zd_{h['id']}", use_container_width=True):
                    if _post("/zapier/hooks/delete", user_id, h["id"]):
                        st.rerun()
    else:
        st.caption("Aucune automatisation pour l'instant.")
