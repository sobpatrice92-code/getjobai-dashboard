"""
linkedin_oauth.py — Connexion LinkedIn via OAuth 2.0 (API officielle)
=====================================================================
Permet à un utilisateur de connecter son compte LinkedIn en 1 clic.
Le jeton (access + refresh) est stocké dans Supabase (table users) et
servira à publier ses posts AUTOMATIQUEMENT (planificateur), sans cookie
ni extension.

Secrets lus depuis l'environnement (Render) :
  LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, LINKEDIN_REDIRECT_URI
"""
import os
import hmac
import base64
import hashlib
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = "openid profile w_member_social"


def _cfg():
    return (
        os.getenv("LINKEDIN_CLIENT_ID", ""),
        os.getenv("LINKEDIN_CLIENT_SECRET", ""),
        os.getenv("LINKEDIN_REDIRECT_URI", "https://app.jobfacileai.com/"),
    )


def is_configured() -> bool:
    cid, secret, _ = _cfg()
    return bool(cid and secret)


# --- state signé (anti-CSRF / anti-forge : lie le retour au bon user_id) ---
def _sign(user_id: str) -> str:
    _, secret, _ = _cfg()
    key = (secret or "gja").encode()
    raw = base64.urlsafe_b64encode(user_id.encode()).decode().rstrip("=")
    sig = hmac.new(key, raw.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{raw}.{sig}"


def verify_state(state: str):
    try:
        raw, sig = state.split(".", 1)
        _, secret, _ = _cfg()
        key = (secret or "gja").encode()
        good = hmac.new(key, raw.encode(), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(sig, good):
            return None
        pad = "=" * (-len(raw) % 4)
        return base64.urlsafe_b64decode(raw + pad).decode()
    except Exception:
        return None


def build_authorize_url(user_id: str) -> str:
    cid, _, redirect = _cfg()
    q = urlencode({
        "response_type": "code",
        "client_id": cid,
        "redirect_uri": redirect,
        "state": _sign(user_id),
        "scope": SCOPES,
    })
    return f"{AUTH_URL}?{q}"


def exchange_code(code: str) -> dict:
    """Échange le code d'autorisation contre un access_token (+ refresh)."""
    cid, secret, redirect = _cfg()
    r = httpx.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect,
        "client_id": cid,
        "client_secret": secret,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=20)
    r.raise_for_status()
    return r.json()


def get_member_id(access_token: str) -> str:
    """Récupère l'identifiant membre LinkedIn (sub) via OpenID userinfo."""
    r = httpx.get(USERINFO_URL,
                  headers={"Authorization": f"Bearer {access_token}"}, timeout=15)
    r.raise_for_status()
    return r.json().get("sub", "")


def store_token(db, user_id: str, token: dict, member_id: str, member_name: str = ""):
    """Enregistre le jeton dans users (colonnes linkedin_oauth_*)."""
    expires = (datetime.now(timezone.utc)
               + timedelta(seconds=int(token.get("expires_in", 0)))).isoformat()
    patch = {
        "linkedin_oauth_token": token.get("access_token"),
        "linkedin_oauth_refresh": token.get("refresh_token"),
        "linkedin_oauth_expires": expires,
        "linkedin_member_id": member_id,
    }
    url = f"{db.url}/rest/v1/users?id=eq.{user_id}"
    h = {**db.headers, "Content-Type": "application/json", "Prefer": "return=minimal"}
    r = httpx.patch(url, headers=h, json=patch, timeout=15)
    return r.status_code in (200, 204)


def get_status(db, user_id: str) -> dict:
    """Retourne l'état de connexion LinkedIn de l'utilisateur."""
    url = (f"{db.url}/rest/v1/users?id=eq.{user_id}"
           "&select=linkedin_member_id,linkedin_oauth_expires")
    try:
        r = httpx.get(url, headers=db.headers, timeout=10)
        if r.status_code == 200 and r.json():
            row = r.json()[0]
            connected = bool(row.get("linkedin_member_id"))
            return {"connected": connected, "expires": row.get("linkedin_oauth_expires")}
    except Exception:
        pass
    return {"connected": False, "expires": None}


def _valid_token(db, user_id: str):
    """Retourne un access_token valide (rafraîchit si expiré), ou None."""
    url = (f"{db.url}/rest/v1/users?id=eq.{user_id}"
           "&select=linkedin_oauth_token,linkedin_oauth_refresh,linkedin_oauth_expires,linkedin_member_id")
    r = httpx.get(url, headers=db.headers, timeout=10)
    if r.status_code != 200 or not r.json():
        return None, None
    row = r.json()[0]
    token = row.get("linkedin_oauth_token")
    member = row.get("linkedin_member_id")
    exp = row.get("linkedin_oauth_expires")
    if not token or not member:
        return None, None
    # Rafraîchir si expiré (marge 1 jour)
    try:
        if exp and datetime.fromisoformat(exp.replace("Z", "+00:00")) < datetime.now(timezone.utc) + timedelta(days=1):
            new = _refresh(db, user_id, row.get("linkedin_oauth_refresh"))
            if new:
                token = new
    except Exception:
        pass
    return token, member


def _refresh(db, user_id: str, refresh_token: str):
    if not refresh_token:
        return None
    cid, secret, _ = _cfg()
    try:
        r = httpx.post(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cid,
            "client_secret": secret,
        }, headers={"Content-Type": "application/x-www-form-urlencoded"}, timeout=20)
        if r.status_code != 200:
            return None
        tok = r.json()
        store_token(db, user_id, tok,
                    _safe_member(db, user_id), "")
        return tok.get("access_token")
    except Exception:
        return None


def _safe_member(db, user_id):
    url = f"{db.url}/rest/v1/users?id=eq.{user_id}&select=linkedin_member_id"
    try:
        r = httpx.get(url, headers=db.headers, timeout=8)
        return r.json()[0].get("linkedin_member_id", "")
    except Exception:
        return ""


def publish(access_token: str, member_id: str, texte: str, image_b64: str = "") -> tuple:
    """Publie un post (texte + image optionnelle) via l'API REST LinkedIn.
    Retourne (ok, message/urn)."""
    author = f"urn:li:person:{member_id}"
    base_h = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202405",
    }
    image_urn = None
    if image_b64:
        try:
            init = httpx.post(
                "https://api.linkedin.com/rest/images?action=initializeUpload",
                headers={**base_h, "Content-Type": "application/json"},
                json={"initializeUploadRequest": {"owner": author}}, timeout=20)
            init.raise_for_status()
            val = init.json()["value"]
            upload_url = val["uploadUrl"]
            image_urn = val["image"]
            img_bytes = base64.b64decode(image_b64)
            up = httpx.put(upload_url, content=img_bytes,
                           headers={"Authorization": f"Bearer {access_token}"}, timeout=60)
            if up.status_code not in (200, 201):
                image_urn = None  # on publie en texte seul plutôt qu'échouer
        except Exception:
            image_urn = None

    body = {
        "author": author,
        "commentary": texte,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED",
                         "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    if image_urn:
        body["content"] = {"media": {"title": "Image", "id": image_urn}}
    try:
        r = httpx.post("https://api.linkedin.com/rest/posts",
                       headers={**base_h, "Content-Type": "application/json"},
                       json=body, timeout=30)
        if r.status_code in (200, 201):
            return True, r.headers.get("x-restli-id", "ok")
        return False, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return False, str(e)[:200]


def publish_for_user(db, user_id: str, texte: str, image_b64: str = "") -> tuple:
    """Helper haut niveau : récupère le jeton de l'utilisateur et publie."""
    token, member = _valid_token(db, user_id)
    if not token:
        return False, "LinkedIn non connecté (ou jeton expiré). Reconnectez LinkedIn."
    return publish(token, member, texte, image_b64)


def handle_callback(db):
    """À appeler au chargement de l'app. Si on revient de LinkedIn (?code&state),
    échange le code et stocke le jeton. Retourne (ok, message) ou None si pas un retour OAuth."""
    import streamlit as st
    qp = st.query_params
    # LinkedIn a renvoyé une erreur (ex: scope/produit non activé) ?
    err = qp.get("error")
    if err:
        desc = qp.get("error_description", "")
        st.query_params.clear()
        return (False, f"LinkedIn a refusé l'autorisation : {err} — {desc}")
    code = qp.get("code")
    state = qp.get("state")
    if not code or not state:
        return None
    user_id = verify_state(state)
    if not user_id:
        return (False, "État OAuth invalide (lien expiré ou falsifié). Réessayez.")
    try:
        token = exchange_code(code)
    except httpx.HTTPStatusError as e:
        st.query_params.clear()
        return (False, f"Échec échange du code (HTTP {e.response.status_code}) : {e.response.text[:200]}")
    except Exception as e:
        st.query_params.clear()
        return (False, f"Échec échange du code : {str(e)[:200]}")
    access = token.get("access_token")
    if not access:
        st.query_params.clear()
        return (False, f"Pas d'access_token reçu : {token}")
    try:
        member_id = get_member_id(access)
    except httpx.HTTPStatusError as e:
        st.query_params.clear()
        return (False, f"userinfo refusé (HTTP {e.response.status_code}) — produit « Sign In with LinkedIn using OpenID Connect » manquant ? {e.response.text[:150]}")
    except Exception as e:
        st.query_params.clear()
        return (False, f"userinfo erreur : {str(e)[:150]}")
    if not member_id:
        st.query_params.clear()
        return (False, "Identifiant LinkedIn (sub) vide — scope openid/profile manquant.")
    store_token(db, user_id, token, member_id)
    st.query_params.clear()
    return (True, "✅ LinkedIn connecté ! Vos posts pourront être publiés automatiquement.")
