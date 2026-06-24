"""
notion_link.py — Connexion Notion (côté dashboard).
===================================================
Appelle le backend FastAPI (OAuth Notion + synchro de l'espace). Aucune clé
secrète ici : on signe seulement un jeton court HMAC (APP_HMAC_SECRET partagé),
exactement comme billing.py. L'espace Notion vit chez l'utilisateur (OAuth).
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


def connect_url(user_id: str) -> str:
    """Lien d'autorisation (le backend redirige vers Notion)."""
    return f"{_backend_url()}/notion/connect?user_id={user_id}&token={_sign(user_id)}"


def status(user_id: str) -> dict:
    try:
        r = httpx.get(f"{_backend_url()}/notion/status",
                      params={"user_id": user_id, "token": _sign(user_id)}, timeout=15)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}


def sync_now(user_id: str) -> bool:
    try:
        r = httpx.post(f"{_backend_url()}/notion/sync",
                       json={"user_id": user_id, "token": _sign(user_id)}, timeout=20)
        return r.status_code == 200
    except Exception:
        return False


def disconnect(user_id: str) -> bool:
    try:
        r = httpx.post(f"{_backend_url()}/notion/disconnect",
                       json={"user_id": user_id, "token": _sign(user_id)}, timeout=20)
        return r.status_code == 200
    except Exception:
        return False


def render_panel(user_id: str) -> None:
    """Panneau complet : connexion / état / rafraîchir / déconnexion."""
    # Retour OAuth (?notion=ok|err)
    _ret = st.query_params.get("notion")
    if _ret == "ok":
        st.success("✅ Notion connecté ! Votre espace est en cours de création "
                   "(candidatures + réseau). Rafraîchissez dans une minute.")
        try:
            del st.query_params["notion"]
        except Exception:
            pass
    elif _ret == "err":
        st.error("La connexion Notion a échoué. Réessayez, et pensez à **partager "
                 "une page** avec l'intégration GetJobAI au moment de l'autorisation.")
        try:
            del st.query_params["notion"]
        except Exception:
            pass

    if not enabled():
        st.info("La synchronisation Notion n'est pas encore activée sur ce compte.")
        return

    info = status(user_id)
    if not info.get("configured"):
        st.warning("L'intégration Notion n'est pas configurée côté serveur "
                   "(en attente des identifiants OAuth Notion).")
        return

    st.markdown("Synchronisez automatiquement vos **candidatures** et votre "
                "**réseau** dans votre propre espace Notion. Tout reste chez vous.")

    if not info.get("connected"):
        st.link_button("🔗 Connecter mon Notion", connect_url(user_id), type="primary",
                       use_container_width=True)
        st.caption("Vous choisirez la page Notion où créer votre espace GetJobAI.")
        return

    # Connecté
    hub = info.get("hub_url")
    synced = info.get("synced_at")
    cols = st.columns([2, 1])
    with cols[0]:
        if hub:
            st.link_button("📂 Ouvrir mon espace Notion", hub, use_container_width=True)
        else:
            st.caption("Espace en cours de création…")
        if synced:
            st.caption(f"Dernière synchro : {str(synced).replace('T', ' ')[:16]}")
    with cols[1]:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            if sync_now(user_id):
                st.toast("Synchro lancée — vos données arrivent dans Notion.")
            else:
                st.error("Synchro indisponible pour le moment.")

    with st.expander("Déconnecter Notion"):
        st.caption("Cela efface le jeton d'accès côté GetJobAI. Vos pages Notion "
                   "déjà créées ne sont pas supprimées.")
        if st.button("Déconnecter Notion", type="secondary"):
            if disconnect(user_id):
                st.success("Notion déconnecté.")
                st.rerun()
