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
import time
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


# --- Chiffrement des jetons au repos (defense-in-depth) ---------------------
# Les jetons LinkedIn sont écrits dans la table `users`, lisible avec la clé
# anon (présente côté extension). On les chiffre avec une clé serveur SEULE
# (LINKEDIN_TOKEN_KEY, sur Render) : une fuite de la clé anon ne donne alors
# que du chiffré inutilisable. Rétro-compatible : sans clé → stockage en clair
# (comportement actuel), et la lecture passe les anciens jetons en clair tels
# quels (migration transparente au prochain refresh).
_ENC_PREFIX = "enc:"


def _fernet():
    key = os.getenv("LINKEDIN_TOKEN_KEY", "")
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        return None


def enc_token(s):
    if not s:
        return s
    f = _fernet()
    if not f:
        return s  # pas de clé → clair (aucune régression)
    try:
        return _ENC_PREFIX + f.encrypt(s.encode()).decode()
    except Exception:
        return s


def dec_token(s):
    if not s or not str(s).startswith(_ENC_PREFIX):
        return s  # ancien jeton en clair → tel quel
    f = _fernet()
    if not f:
        return None  # chiffré mais clé absente → inutilisable
    try:
        return f.decrypt(str(s)[len(_ENC_PREFIX):].encode()).decode()
    except Exception:
        return None


# --- state signé (anti-CSRF : lie le retour au bon user_id + horodatage) ---
# Format : <b64(user_id)>.<timestamp>.<sig>. La signature couvre user_id ET le
# timestamp, ce qui rend le state à usage limité dans le temps (pas rejouable
# indéfiniment). Le lien au compte connecté est en plus revérifié côté callback.
def _sign(user_id: str) -> str:
    _, secret, _ = _cfg()
    key = (secret or "gja").encode()
    raw = base64.urlsafe_b64encode(user_id.encode()).decode().rstrip("=")
    ts = str(int(time.time()))
    msg = f"{raw}.{ts}".encode()
    sig = hmac.new(key, msg, hashlib.sha256).hexdigest()[:32]
    return f"{raw}.{ts}.{sig}"


def verify_state(state: str, max_age: int = 900):
    """Vérifie la signature ET l'âge du state. Retourne user_id ou None."""
    try:
        raw, ts, sig = state.split(".", 2)
        _, secret, _ = _cfg()
        key = (secret or "gja").encode()
        good = hmac.new(key, f"{raw}.{ts}".encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good):
            return None
        age = int(time.time()) - int(ts)
        if age < -60 or age > max_age:   # expiré (ou horloge incohérente)
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
        "linkedin_oauth_token": enc_token(token.get("access_token")),
        "linkedin_oauth_expires": expires,
    }
    # Ne JAMAIS écraser le refresh_token / member_id par une valeur vide :
    # un refresh LinkedIn ne renvoie pas toujours de nouveau refresh_token,
    # et le perdrait sinon (reconnexion forcée plus tard).
    if token.get("refresh_token"):
        patch["linkedin_oauth_refresh"] = enc_token(token.get("refresh_token"))
    if member_id:
        patch["linkedin_member_id"] = member_id
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
    token = dec_token(row.get("linkedin_oauth_token"))
    member = row.get("linkedin_member_id")
    exp = row.get("linkedin_oauth_expires")
    if not token or not member:
        return None, None
    # Rafraîchir si expiré (marge 1 jour)
    try:
        if exp and datetime.fromisoformat(exp.replace("Z", "+00:00")) < datetime.now(timezone.utc) + timedelta(days=1):
            new = _refresh(db, user_id, dec_token(row.get("linkedin_oauth_refresh")))
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
    try:
        from test_mode import est_test
    except Exception:
        est_test = lambda: False
    if est_test():
        return True, "test-mode-simulé (aucun post réel)"
    author = f"urn:li:person:{member_id}"
    base_h = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": os.getenv("LINKEDIN_API_VERSION", "202506"),
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


# --- Publication VIDÉO (Videos API) -----------------------------------------
_LI_CHUNK = 4 * 1024 * 1024  # taille de partie indicative (LinkedIn ~4 Mo)


def publish_video(access_token: str, member_id: str, texte: str, video_bytes: bytes) -> tuple:
    """Publie un post avec VIDÉO via la Videos API LinkedIn.
    Flux : initializeUpload -> PUT des parties (collecte des ETags) -> finalizeUpload
    -> rest/posts. Retourne (ok, message/urn)."""
    try:
        from test_mode import est_test
    except Exception:
        est_test = lambda: False
    if est_test():
        return True, "test-mode-simulé (aucune vidéo réelle publiée)"
    if not video_bytes:
        return False, "Vidéo vide."
    author = f"urn:li:person:{member_id}"
    base_h = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": os.getenv("LINKEDIN_API_VERSION", "202506"),
    }
    try:
        # 1) initializeUpload
        init = httpx.post(
            "https://api.linkedin.com/rest/videos?action=initializeUpload",
            headers={**base_h, "Content-Type": "application/json"},
            json={"initializeUploadRequest": {
                "owner": author, "fileSizeBytes": len(video_bytes),
                "uploadCaptions": False, "uploadThumbnail": False}}, timeout=30)
        if init.status_code not in (200, 201):
            return False, f"initializeUpload HTTP {init.status_code}: {init.text[:200]}"
        val = init.json()["value"]
        video_urn = val["video"]
        upload_token = val.get("uploadToken", "")
        instructions = val.get("uploadInstructions", [])
        # 2) PUT de chaque partie -> collecte des ETags
        etags = []
        for ins in instructions:
            first, last = int(ins["firstByte"]), int(ins["lastByte"])
            part = video_bytes[first:last + 1]
            up = httpx.put(ins["uploadUrl"], content=part,
                           headers={"Authorization": f"Bearer {access_token}"}, timeout=120)
            if up.status_code not in (200, 201):
                return False, f"upload partie HTTP {up.status_code}: {up.text[:150]}"
            etags.append(up.headers.get("etag") or up.headers.get("ETag") or "")
        # 3) finalizeUpload
        fin = httpx.post(
            "https://api.linkedin.com/rest/videos?action=finalizeUpload",
            headers={**base_h, "Content-Type": "application/json"},
            json={"finalizeUploadRequest": {
                "video": video_urn, "uploadToken": upload_token,
                "uploadedPartIds": etags}}, timeout=30)
        if fin.status_code not in (200, 201):
            return False, f"finalizeUpload HTTP {fin.status_code}: {fin.text[:200]}"
        # 3b) attendre que LinkedIn ait TRAITÉ la vidéo (sinon rest/posts refuse)
        statut = _attendre_video_prete(base_h, video_urn)
        if statut == "PROCESSING_FAILED":
            return False, "LinkedIn n'a pas pu traiter la vidéo (format/codec refusé)."
        # 4) création du post référençant la vidéo (avec ré-essais si encore en traitement)
        body = {
            "author": author, "commentary": texte, "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED",
                             "targetEntities": [], "thirdPartyDistributionChannels": []},
            "content": {"media": {"title": "Vidéo", "id": video_urn}},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False,
        }
        derniere = ""
        for tentative in range(4):
            r = httpx.post("https://api.linkedin.com/rest/posts",
                           headers={**base_h, "Content-Type": "application/json"},
                           json=body, timeout=30)
            if r.status_code in (200, 201):
                return True, r.headers.get("x-restli-id", video_urn)
            derniere = f"rest/posts HTTP {r.status_code}: {r.text[:200]}"
            # média peut-être pas encore prêt -> on patiente puis on réessaie
            time.sleep(6)
        return False, derniere
    except Exception as e:
        return False, str(e)[:200]


def _attendre_video_prete(base_h: dict, video_urn: str, timeout_s: int = 45) -> str:
    """Sonde le statut de la vidéo jusqu'à AVAILABLE (ou échec/timeout).
    Best-effort : si l'endpoint ne répond pas, retourne '' (on tentera quand même)."""
    from urllib.parse import quote
    url = f"https://api.linkedin.com/rest/videos/{quote(video_urn, safe='')}"
    fin = time.time() + timeout_s
    dernier = ""
    while time.time() < fin:
        try:
            r = httpx.get(url, headers=base_h, timeout=15)
            if r.status_code == 200:
                dernier = (r.json().get("status") or "").upper()
                if dernier in ("AVAILABLE", "PROCESSING_FAILED"):
                    return dernier
            else:
                return dernier  # endpoint indispo -> on ne bloque pas
        except Exception:
            return dernier
        time.sleep(5)
    return dernier


def simuler_publication_video(db, user_id: str, texte: str, video_bytes: bytes) -> tuple:
    """SIMULATION (dry-run) de la publication vidéo : vérifie la connexion réelle et
    déroule les étapes SANS aucun appel d'écriture à LinkedIn. Retourne (ok, rapport)."""
    token, member = _valid_token(db, user_id)
    if not token:
        return False, "LinkedIn non connecté (ou jeton expiré). Reconnectez LinkedIn d'abord."
    if not video_bytes:
        return False, "Aucune vidéo à publier (génère d'abord la vidéo)."
    taille = len(video_bytes)
    nb_parties = max(1, -(-taille // _LI_CHUNK))  # ceil
    version = os.getenv("LINKEDIN_API_VERSION", "202506")
    apercu = (texte or "").strip().replace("\n", " ")[:120]
    rapport = (
        "🧪 SIMULATION — aucune publication réelle effectuée\n\n"
        f"• Compte LinkedIn : connecté ✅ (urn:li:person:{member})\n"
        f"• Jeton d'accès : valide ✅ (LinkedIn-Version {version})\n"
        f"• Vidéo : {taille/1024/1024:.2f} Mo → {nb_parties} partie(s) d'upload\n"
        f"• Texte du post : « {apercu}{'…' if len(texte or '') > 120 else ''} »\n\n"
        "Étapes qui SERAIENT exécutées en réel :\n"
        f"  1. POST /rest/videos?action=initializeUpload (owner, fileSizeBytes={taille})\n"
        f"  2. PUT de {nb_parties} partie(s) + collecte des ETags\n"
        "  3. POST /rest/videos?action=finalizeUpload (video urn + uploadedPartIds)\n"
        "  4. POST /rest/posts (commentary + content.media = video urn)\n\n"
        "Tout est prêt. Décoche « Simulation » pour publier réellement."
    )
    return True, rapport


def publish_video_for_user(db, user_id: str, texte: str, video_bytes: bytes,
                           simuler: bool = False) -> tuple:
    """Helper haut niveau : simule OU publie réellement la vidéo de l'utilisateur."""
    if simuler:
        return simuler_publication_video(db, user_id, texte, video_bytes)
    token, member = _valid_token(db, user_id)
    if not token:
        return False, "LinkedIn non connecté (ou jeton expiré). Reconnectez LinkedIn."
    return publish_video(token, member, texte, video_bytes)


def handle_callback(db, session_user_id: str = None):
    """À appeler au chargement de l'app. Si on revient de LinkedIn (?code&state),
    échange le code et stocke le jeton. Retourne (ok, message) ou None si pas un retour OAuth.

    `session_user_id` = l'utilisateur ACTUELLEMENT connecté au dashboard. Le jeton
    n'est stocké que si le state (signé) désigne bien ce même utilisateur : sans ce
    contrôle, un attaquant pourrait faire lier le LinkedIn d'une victime à son propre
    compte (account-linking CSRF) et publier en son nom."""
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
        st.query_params.clear()
        return (False, "État OAuth invalide (lien expiré ou falsifié). Réessayez.")
    # Liaison à la session : le state doit désigner l'utilisateur connecté.
    if not session_user_id or str(user_id) != str(session_user_id):
        st.query_params.clear()
        return (False, "Connexion LinkedIn refusée : reconnectez-vous au dashboard, "
                       "puis relancez « Connecter LinkedIn ».")
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
