"""
Module d'authentification — login / signup / mot de passe
=========================================================
Hash sécurisé via pbkdf2 (stdlib, aucune dépendance externe).
S'appuie sur la table `users` de Supabase (colonne password_hash).
"""
import os
import hashlib
import secrets
import httpx
import streamlit as st
from typing import Optional, Dict


def _supabase():
    """Récupère url + headers Supabase (mêmes credentials que database.py)."""
    url = os.getenv("SUPABASE_URL")
    # Clé SERVICE en priorité (repli anon) — voir database.py.
    key = (os.getenv("SUPABASE_SERVICE_KEY")
           or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
           or os.getenv("SUPABASE_KEY"))
    if not url or not key:
        try:
            url = url or st.secrets.get("SUPABASE_URL")
            key = (key or st.secrets.get("SUPABASE_SERVICE_KEY")
                   or st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
                   or st.secrets.get("SUPABASE_KEY"))
        except Exception:
            pass
    url = "".join((url or "").split())
    key = "".join((key or "").split())
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    return url, headers


# ----------------------------------------------------------------------
# Hashing
# ----------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Retourne 'salt$hash' (hex). pbkdf2-hmac-sha256, 200k itérations."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Vérifie un mot de passe contre 'salt$hash'."""
    if not stored or "$" not in stored:
        return False
    salt, expected = stored.split("$", 1)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
    return secrets.compare_digest(dk.hex(), expected)


# ----------------------------------------------------------------------
# Opérations Supabase
# ----------------------------------------------------------------------
def get_user_auth(email: str) -> Optional[Dict]:
    """Récupère un utilisateur (avec password_hash, is_admin, is_whitelisted)."""
    url, headers = _supabase()
    email = email.strip().lower()
    q = (f"{url}/rest/v1/users?email=eq.{email}"
         "&select=id,email,full_name,password_hash,is_admin,is_whitelisted,is_active")
    try:
        r = httpx.get(q, headers=headers, timeout=10)
        if r.status_code == 200 and r.json():
            return r.json()[0]
    except Exception as e:
        st.error(f"Erreur connexion: {e}")
    return None


def email_exists(email: str) -> bool:
    url, headers = _supabase()
    email = email.strip().lower()
    try:
        r = httpx.get(f"{url}/rest/v1/users?email=eq.{email}&select=id",
                      headers=headers, timeout=10)
        return r.status_code == 200 and bool(r.json())
    except Exception:
        return False


def create_user(email: str, password: str, full_name: str) -> bool:
    """Crée un utilisateur en attente d'approbation (is_whitelisted=False)."""
    url, headers = _supabase()
    data = {
        "email": email.strip().lower(),
        "password_hash": hash_password(password),
        "full_name": full_name.strip(),
        "is_admin": False,
        "is_active": True,
        "is_whitelisted": False,  # en attente d'approbation admin
    }
    try:
        r = httpx.post(f"{url}/rest/v1/users", headers=headers, json=data, timeout=10)
        return r.status_code in (200, 201)
    except Exception as e:
        st.error(f"Erreur création compte: {e}")
        return False


def set_password(user_id: str, new_password: str) -> bool:
    """Change le mot de passe d'un utilisateur."""
    url, headers = _supabase()
    h = {**headers, "Prefer": "return=minimal"}
    try:
        r = httpx.patch(f"{url}/rest/v1/users?id=eq.{user_id}",
                        headers=h, json={"password_hash": hash_password(new_password)},
                        timeout=10)
        return r.status_code in (200, 204)
    except Exception as e:
        st.error(f"Erreur changement mot de passe: {e}")
        return False


# ----------------------------------------------------------------------
# UI — écran de connexion / inscription
# ----------------------------------------------------------------------
def login_screen():
    """Affiche login + signup (page premium). Met à jour st.session_state si succès."""
    st.markdown("""
    <style>
    .gja-login-hero{ text-align:center; margin:1.4rem 0 1.1rem; }
    .gja-login-logo{ font-family:'Poppins','Inter',sans-serif; font-weight:700; font-size:2.7rem;
      line-height:1.1; letter-spacing:-1px;
      background:linear-gradient(95deg,#7da2ff 0%, #9b8bff 45%, #2dd4bf 110%);
      -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
    .gja-login-tag{ color:#eaf2ff; font-size:1.18rem; font-weight:600; margin-top:.5rem; }
    .gja-login-sub{ color:#93a4c8; font-size:.96rem; margin-top:.35rem; }
    .gja-login-feats{ display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:1.15rem auto .2rem; }
    .gja-login-feats span{ background:rgba(91,124,255,.10); border:1px solid rgba(120,160,255,.18);
      color:#cfe0ff; padding:6px 13px; border-radius:999px; font-size:.82rem; font-weight:500; }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.35, 1])
    with c2:
        st.markdown("""
        <div class="gja-login-hero">
            <div class="gja-login-logo">🚀 GetJobAI</div>
            <div class="gja-login-tag">Votre recherche d'emploi en pilote automatique</div>
            <div class="gja-login-sub">12 agents IA qui cherchent, postulent et relancent pour vous.</div>
            <div class="gja-login-feats">
                <span>🔎 Veille multi‑sources</span><span>📤 Candidatures auto</span>
                <span>🎤 Coaching entretien</span><span>🤝 Réseautage</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            tab_login, tab_signup = st.tabs(["🔐  Se connecter", "✨  Créer un compte"])

            with tab_login:
                email = st.text_input("Email", key="login_email", placeholder="vous@email.com")
                pwd = st.text_input("Mot de passe", type="password", key="login_pwd",
                                    placeholder="••••••••")
                if st.button("Se connecter", type="primary", key="btn_login",
                             use_container_width=True):
                    user = get_user_auth(email)
                    if not user:
                        st.error("Email inconnu.")
                    elif not user.get("password_hash"):
                        st.error("Aucun mot de passe défini pour ce compte. Contactez l'administrateur.")
                    elif not verify_password(pwd, user["password_hash"]):
                        st.error("Mot de passe incorrect.")
                    else:
                        # Connexion réussie
                        st.session_state.auth_ok = True
                        st.session_state.logged_out = False  # réautorise la persistance cookie
                        st.session_state.user_email = user["email"]
                        st.session_state.user_id = user["id"]
                        st.session_state.is_admin = bool(user.get("is_admin"))
                        st.session_state.is_whitelisted = bool(user.get("is_whitelisted"))
                        if st.session_state.is_admin:
                            st.session_state.real_admin_email = user["email"]
                        st.rerun()

            with tab_signup:
                st.caption("Votre compte devra être approuvé par un administrateur avant accès.")
                s_name = st.text_input("Nom complet", key="signup_name")
                s_email = st.text_input("Email", key="signup_email")
                s_pwd = st.text_input("Mot de passe (min. 6 caractères)", type="password", key="signup_pwd")
                s_pwd2 = st.text_input("Confirmer le mot de passe", type="password", key="signup_pwd2")
                if st.button("Créer mon compte", type="primary", key="btn_signup",
                             use_container_width=True):
                    if not s_name or not s_email or not s_pwd:
                        st.error("Tous les champs sont requis.")
                    elif len(s_pwd) < 6:
                        st.error("Le mot de passe doit faire au moins 6 caractères.")
                    elif s_pwd != s_pwd2:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif email_exists(s_email):
                        st.error("Un compte existe déjà avec cet email.")
                    elif create_user(s_email, s_pwd, s_name):
                        st.success("✅ Compte créé ! Il sera actif dès qu'un administrateur l'aura approuvé.")
                    else:
                        st.error("Erreur lors de la création du compte.")
