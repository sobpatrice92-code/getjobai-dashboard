"""
Abonnement Stripe — intégration côté dashboard (appelle le backend FastAPI).

ACTIVÉ uniquement si BILLING_ENABLED=1 ET BACKEND_URL défini : tant que ce n'est
pas le cas, `enabled()` renvoie False et le dashboard se comporte EXACTEMENT comme
avant (aucun gating). Les clés secrètes restent côté backend ; ici on ne signe que
des jetons courts (HMAC) avec APP_HMAC_SECRET partagé.
"""
import hashlib
import hmac
import os
import time

import httpx
import streamlit as st


def enabled() -> bool:
    return os.getenv("BILLING_ENABLED") == "1" and bool(os.getenv("BACKEND_URL"))


def _backend_url() -> str:
    return os.getenv("BACKEND_URL", "").rstrip("/")


def _sign(user_id: str, ttl: int = 600) -> str:
    secret = os.getenv("APP_HMAC_SECRET", "")
    exp = int(time.time()) + ttl
    sig = hmac.new(secret.encode(), f"{user_id}.{exp}".encode(),
                   hashlib.sha256).hexdigest()[:32]
    return f"{exp}.{sig}"


def _sub_status(user_id: str) -> str:
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY") or ""
    try:
        r = httpx.get(f"{url}/rest/v1/users?id=eq.{user_id}&select=subscription_status",
                      headers={"apikey": key, "Authorization": "Bearer " + key}, timeout=10)
        rows = r.json() if r.status_code == 200 else []
        return (rows[0].get("subscription_status") if rows else "none") or "none"
    except Exception:
        return "none"


def is_active(user_id: str) -> bool:
    return _sub_status(user_id) in ("active", "trialing")


def _backend(path: str, user_id: str):
    r = httpx.post(f"{_backend_url()}{path}",
                   json={"user_id": user_id, "token": _sign(user_id)}, timeout=25)
    r.raise_for_status()
    return r.json().get("url")


def gate_or_subscribe(user_id: str, email: str) -> bool:
    """Renvoie True si l'utilisateur est abonné (on le laisse passer).
    Sinon affiche l'écran d'abonnement et appelle st.stop() (ne revient pas)."""
    if is_active(user_id):
        return True
    st.markdown("## 🔓 Abonnez-vous pour accéder à GetJobAI")
    st.write("Votre compte est créé. Activez votre **abonnement mensuel** pour "
             "utiliser tous les agents (recherche d'offres, candidatures, suivi…).")
    if st.button("💳 S'abonner maintenant", type="primary"):
        try:
            link = _backend("/billing/checkout", user_id)
            if link:
                st.link_button("Continuer vers le paiement sécurisé Stripe →", link,
                               type="primary")
                st.caption("Vous serez redirigé vers Stripe, puis de retour ici.")
            else:
                st.error("Lien de paiement indisponible. Réessayez dans un instant.")
        except Exception:
            st.error("Paiement momentanément indisponible. Réessayez bientôt.")
    st.stop()


def manage_button(user_id: str) -> None:
    """Bouton « Gérer mon abonnement » (portail Stripe : facture, annulation)."""
    if st.button("💳 Gérer mon abonnement", use_container_width=True):
        try:
            link = _backend("/billing/portal", user_id)
            if link:
                st.link_button("Ouvrir le portail Stripe →", link)
            else:
                st.error("Portail indisponible pour le moment.")
        except Exception:
            st.error("Portail momentanément indisponible.")
