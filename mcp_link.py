"""
mcp_link.py — Accès IA (MCP) côté dashboard.
============================================
Active/affiche la clé MCP de l'utilisateur (via le backend) et donne les
instructions pour brancher GetJobAI dans Claude / ChatGPT. Aucune clé secrète
ici : jeton court HMAC signé (APP_HMAC_SECRET), comme billing.py.
"""
import hashlib
import hmac
import os
import time

import httpx
import streamlit as st


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


def _status(user_id: str) -> dict:
    try:
        r = httpx.get(f"{_backend_url()}/mcp/status",
                      params={"user_id": user_id, "token": _sign(user_id)}, timeout=15)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def _post(path: str, user_id: str) -> dict:
    try:
        r = httpx.post(f"{_backend_url()}{path}",
                       json={"user_id": user_id, "token": _sign(user_id)}, timeout=15)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def render_panel(user_id: str) -> None:
    if not enabled():
        st.info("L'accès IA (MCP) n'est pas encore activé sur ce compte.")
        return

    st.markdown(
        "Connectez vos données GetJobAI à une **IA** (Claude, ChatGPT…). Vous "
        "pourrez lui demander en langage naturel : *« mes candidatures en attente ? »*, "
        "*« résume mon réseau chez EXP »*, *« quelles relances faire ? »*. "
        "L'IA lit vos données en **lecture seule**.")

    info = _status(user_id)
    if not info.get("enabled"):
        if st.button("🔌 Activer l'accès IA", type="primary", use_container_width=True):
            if _post("/mcp/enable", user_id).get("key"):
                st.rerun()
            else:
                st.error("Activation impossible pour le moment.")
        return

    key = info.get("key", "")
    url = f"{_backend_url()}/mcp"

    st.success("✅ Accès IA activé.")
    st.markdown("**Adresse du serveur MCP :**")
    st.code(url, language=None)
    st.markdown("**Votre clé personnelle (secrète) :**")
    st.code(key, language=None)

    st.markdown("### Brancher dans Claude Code (terminal)")
    st.code(f'claude mcp add --transport http getjobai {url} '
            f'--header "Authorization: Bearer {key}"', language="bash")

    st.markdown("### Brancher dans Claude Desktop / claude.ai (connecteur)")
    st.markdown(
        "- **URL du serveur** : l'adresse ci-dessus\n"
        "- **En-tête d'authentification** : `Authorization: Bearer <votre clé>`\n"
        "- Si le client demande seulement une URL, utilisez la forme avec clé intégrée :")
    st.code(f"{url}?key={key}", language=None)

    st.caption("Outils exposés : statistiques · lister_candidatures · lister_contacts "
               "(lecture seule, limités à VOS données).")

    c1, c2 = st.columns(2)
    if c1.button("🔄 Régénérer la clé", use_container_width=True):
        if _post("/mcp/regenerate", user_id).get("key"):
            st.toast("Nouvelle clé générée — reconnectez vos clients.")
            st.rerun()
    if c2.button("🛑 Désactiver l'accès IA", use_container_width=True):
        _post("/mcp/disable", user_id)
        st.rerun()
