"""
GetJobAI Dashboard - Production
================================
Dashboard professionnel avec UI UX PRO MAX intégré
"""
import streamlit as st
import streamlit.components.v1 as components
import os
import json
import base64
from datetime import datetime

# Import UI UX PRO MAX
from ui_ux_pro_max import (
    inject_animations,
    inject_neo_glass,
    inject_premium_polish,
    empty_state,
    section_header,
    hero_holographic,
    holo_loader_3d,
    stats_grid,
    job_card_pro,
    alert,
    card,
    progress_bar,
    COLOR_SCHEMES
)

# Import Database
from database import get_supabase_client

# Import Authentification + Assistant IA
from auth import login_screen, set_password
import billing
from simulation_entretien import simulation_entretien_page
from chatbot import (chatbot_page, generer_message_linkedin, generer_post_linkedin,
                     generer_image_post, prioriser_contacts)

# Configuration
st.set_page_config(
    page_title="GetJobAI - Votre Assistant IA de Recherche d'Emploi",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "GetJobAI - Automatisez votre recherche d'emploi avec l'IA"
    }
)

# Injecter animations CSS + surcouche visuelle Neo-Glass (CSS uniquement)
inject_animations()
inject_neo_glass()
inject_premium_polish()  # couche de finition premium (tabs, champs, typo, métriques)

# ── Fond NOIR PUR (OLED) : override du dégradé bleu-nuit + grille d'inject_animations ──
st.markdown("""
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
section.main, [data-testid="stMain"]{ background:#000000 !important; background-image:none !important; }
[data-testid="stSidebar"]{ background:#050507 !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# GÉNÉRATION PDF (lettre / CV) pour postuler manuellement
# ============================================================
@st.cache_data(show_spinner=False)
def texte_vers_pdf(texte: str, titre: str = "") -> bytes:
    """Convertit un texte (lettre ou CV) en PDF propre, exportable. Mis en cache
    par contenu → ne régénère pas à chaque rerun."""
    from io import BytesIO
    from reportlab.lib.pagesizes import letter as _letter
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from xml.sax.saxutils import escape as _xesc
    import re as _re

    # Nettoyage markdown léger (guides/rapports peuvent contenir ** ou #)
    texte = _re.sub(r"\*\*|`", "", texte or "")
    texte = _re.sub(r"^#{1,6}\s*", "", texte, flags=_re.M)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=_letter, topMargin=1.6 * cm,
                            bottomMargin=1.6 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Heading2"], textColor="#0f5ea8", fontSize=12,
                       spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("b", parent=styles["Normal"], fontSize=10.5, leading=15)
    story = []
    if titre:
        story.append(Paragraph(_xesc(titre), styles["Heading1"]))
        story.append(Spacer(1, 8))
    for ligne in (texte or "").split("\n"):
        l = ligne.rstrip()
        if not l.strip():
            story.append(Spacer(1, 6))
        elif l.isupper() and 3 < len(l) < 60:
            story.append(Paragraph(_xesc(l), h))
        else:
            story.append(Paragraph(_xesc(l), body))
    doc.build(story)
    return buf.getvalue()


def _nom_fichier(s: str) -> str:
    import re as _re
    return _re.sub(r"[^A-Za-z0-9_-]", "_", (s or "doc").replace(" ", "_"))[:40].strip("_") or "doc"

_MOIS_FR = ["", "janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.",
            "août", "sept.", "oct.", "nov.", "déc."]

def _fmt_dt(iso: str) -> str:
    """Date+heure lisible (heure de l'Est) à partir d'un timestamp ISO Supabase (UTC)."""
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        try:
            from zoneinfo import ZoneInfo
            dt = dt.astimezone(ZoneInfo("America/Toronto"))
        except Exception:
            pass
        return f"{dt.day} {_MOIS_FR[dt.month]} {dt.year} à {dt:%H:%M}"
    except Exception:
        return str(iso)[:16].replace("T", " ")

# action_type (Supabase) -> (icône, nom lisible de l'agent)
AGENT_LABELS = {
    "job_hunter": ("📋", "Job Hunter"),
    "indeed_agent": ("🔎", "Indeed Agent"),
    "coop_hunter": ("🎓", "COOP Hunter"),
    "chercheur_offres": ("🧭", "Orchestrateur"),
    "networking_agent": ("🤝", "Networking Agent"),
    "followup_engine": ("📧", "Follow-up Engine"),
    "candidature_prep": ("📝", "Préparer Candidatures"),
    "entretien_prep": ("🎙️", "Préparer mon Entretien"),
    "mail_tracker": ("📬", "Suivi Boîte Mail"),
    "candidature_send": ("🚀", "Postuler (Copilote)"),
    "immigration_advisor": ("🍁", "Immigration Advisor"),
    "linkedin_agent": ("📝", "Post LinkedIn"),
    "publish_linkedin": ("🚀", "Publier LinkedIn (auto)"),
    "profile_optimizer": ("⭐", "Profil LinkedIn 10/10"),
    "ats_optimizer": ("🤖", "ATS Optimizer"),
    "career_strategy_agent": ("🧭", "Stratégie Carrière"),
}

def _agent_label(action: dict):
    """(icône, nom) lisible d'une action — jamais 'Unknown'."""
    at = (action.get("action_type") or action.get("agent_name") or "").strip()
    if at in AGENT_LABELS:
        return AGENT_LABELS[at]
    return ("🤖", at.replace("_", " ").title() if at else "Agent")

# statut Supabase -> (libellé FR, progression 0..1)
_STATUT_INFO = {
    "pending":    ("⏳ En file d'attente", 0.10),
    "queued":     ("⏳ En file d'attente", 0.10),
    "processing": ("🔄 En cours d'exécution", 0.55),
    "running":    ("🔄 En cours d'exécution", 0.55),
    "completed":  ("✅ Terminé", 1.0),
    "failed":     ("❌ Échec", 1.0),
}

# ============================================================
# PERSISTANCE DE SESSION VIA COOKIE
# (évite de redemander la connexion à chaque rechargement de page)
# ============================================================
import hashlib

try:
    import extra_streamlit_components as stx
    _cookies = stx.CookieManager(key="gja_cm")
    _cookie_jar = _cookies.get_all(key="gja_getall") or {}
except Exception:
    _cookies = None
    _cookie_jar = {}


def _auth_token(email):
    """Jeton signé (email + secret serveur) pour valider le cookie."""
    secret = (os.getenv("SUPABASE_KEY") or "gja_secret_2026")[:24]
    return hashlib.sha256((email + secret).encode()).hexdigest()[:40]


# Initialiser session state
if 'auth_ok' not in st.session_state:
    st.session_state.auth_ok = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'real_admin_email' not in st.session_state:
    st.session_state.real_admin_email = None  # Pour revenir après impersonation
if 'is_whitelisted' not in st.session_state:
    st.session_state.is_whitelisted = False

# Restaurer la connexion depuis le cookie (persistance entre rechargements)
# Sauf juste après une déconnexion : la suppression du cookie côté navigateur
# n'est effective qu'au rerun suivant, le drapeau évite une reconnexion fantôme.
if not st.session_state.auth_ok and _cookie_jar and not st.session_state.get("logged_out"):
    try:
        tok = _cookie_jar.get("gja_auth")
        if tok and "|" in tok:
            em, sig = tok.split("|", 1)
            if sig == _auth_token(em):
                st.session_state.auth_ok = True
                st.session_state.user_email = em
    except Exception:
        pass

# ============================================================
# RETOUR OAUTH LINKEDIN (?code&state) — traité avant la porte d'auth
# ============================================================
try:
    import linkedin_oauth
    _qp_code = st.query_params.get("code")
    _qp_err = st.query_params.get("error")
    # VERROU anti-double-échange : un code OAuth ne doit être échangé qu'UNE fois.
    # Streamlit ré-exécute le script ; sans ce verrou, le 2e échange réutilise le
    # code → LinkedIn renvoie 400 ET RÉVOQUE le jeton émis au 1er échange.
    if _qp_err or (_qp_code and st.session_state.get("_li_done_code") != _qp_code):
        # Identité de la session courante (restaurée du cookie) — sert à lier le
        # retour OAuth au bon compte. user_id n'est résolu qu'ensuite : on le
        # récupère ici depuis l'email connecté si besoin.
        _sess_uid = st.session_state.get("user_id")
        if not _sess_uid and st.session_state.get("user_email"):
            try:
                _u = get_supabase_client().get_user_by_email(st.session_state.user_email)
                _sess_uid = _u["id"] if _u else None
            except Exception:
                _sess_uid = None
        # Le composant cookies est ASYNCHRONE : au 1er run après le retour LinkedIn,
        # la session peut ne pas être encore restaurée (_sess_uid inconnu). Dans ce
        # cas on NE consomme PAS le code (pas de verrou, pas d'échange) : on réessaie
        # au rerun suivant, une fois la session prête. Sinon la liaison C1 rejetterait
        # à tort une reconnexion légitime. (Le cas d'erreur LinkedIn n'a pas besoin
        # de session : on le traite tout de suite.)
        if _qp_err or _sess_uid:
            if _qp_code:
                st.session_state["_li_done_code"] = _qp_code   # verrou anti-double-échange
            _res = linkedin_oauth.handle_callback(get_supabase_client(), session_user_id=_sess_uid)
            if _res:
                st.session_state["_li_oauth_msg"] = _res[1]
except Exception as _e:
    st.session_state["_li_oauth_msg"] = f"Erreur callback LinkedIn : {str(_e)[:200]}"

# ============================================================
# PORTE D'AUTHENTIFICATION — pas d'accès sans connexion
# ============================================================
if not st.session_state.auth_ok:
    login_screen()
    st.stop()

# Écrire le cookie de session après connexion (s'il n'existe pas déjà)
if st.session_state.auth_ok and st.session_state.user_email and _cookies is not None:
    try:
        if _cookie_jar.get("gja_auth") is None:
            _cookies.set(
                "gja_auth",
                f"{st.session_state.user_email}|{_auth_token(st.session_state.user_email)}",
                key="gja_set",
                max_age=60 * 60 * 24 * 14,  # 14 jours
            )
    except Exception:
        pass

# Message de retour de connexion LinkedIn (OAuth)
_lim = st.session_state.pop("_li_oauth_msg", None)
if _lim:
    (st.success if _lim.startswith("✅") else st.error)(_lim)

# Message de retour après paiement Stripe (success_url / cancel_url)
_ab = st.query_params.get("abonnement")
if _ab == "ok":
    st.success("✅ Merci ! Votre abonnement est en cours d'activation. "
               "L'accès s'ouvre dès la confirmation de paiement (quelques secondes).")
elif _ab == "annule":
    st.info("Paiement annulé — vous pouvez réessayer quand vous voulez.")

# Recharger les données user depuis Supabase si besoin (ex: impersonation admin)
if st.session_state.user_email and not st.session_state.user_id:
    try:
        db = get_supabase_client()
        user = db.get_user_by_email(st.session_state.user_email)
        if user:
            st.session_state.user_id = user['id']
            st.session_state.is_whitelisted = bool(user.get('is_whitelisted', False))
            user_is_admin = bool(user.get('is_admin', False))
            # Si un vrai admin est déjà connecté, conserver ses privilèges même
            # en consultant le compte d'un autre utilisateur (impersonation).
            if st.session_state.real_admin_email:
                st.session_state.is_admin = True
            else:
                st.session_state.is_admin = user_is_admin
                if user_is_admin:
                    st.session_state.real_admin_email = st.session_state.user_email
    except Exception:
        pass  # Silently fail si pas de connexion

# ============================================================
# SIDEBAR - NAVIGATION
# ============================================================


@st.cache_resource
def _build_info():
    """Commit Git déployé + heure de démarrage du process (≈ déploiement).
    Capturé UNE seule fois par process (cache_resource) → stable entre les reruns,
    et rafraîchi automatiquement à chaque nouveau déploiement Render."""
    commit = (os.getenv("RENDER_GIT_COMMIT", "") or "")[:7] or "local"
    try:
        from zoneinfo import ZoneInfo
        ts = datetime.now(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d %H:%M")
    except Exception:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    return commit, ts


with st.sidebar:
    # Logo — lockup raffiné (mark dégradé + wordmark)
    st.markdown("""
    <div style="display:flex; align-items:center; gap:.7rem; padding:.5rem .2rem 1.4rem;">
        <div style="width:46px; height:46px; border-radius:13px; flex:0 0 auto;
            display:flex; align-items:center; justify-content:center; font-size:1.5rem;
            background:linear-gradient(135deg,#5b7cff 0%, #9b8bff 50%, #2dd4bf 100%);
            box-shadow:0 6px 18px rgba(91,124,255,.45), inset 0 1px 0 rgba(255,255,255,.25);">🚀</div>
        <div style="line-height:1.12;">
            <div style="font-family:'Poppins','Inter',sans-serif; font-weight:700; font-size:1.38rem;
                background:linear-gradient(95deg,#eaf2ff 0%, #9fc7e8 100%);
                -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;">GetJobAI</div>
            <div style="color:#8ea3c8; font-size:.7rem; letter-spacing:1px; text-transform:uppercase; margin-top:1px;">
                Assistant IA · Emploi</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    nav_options = [
        "🏠 Dashboard",
        "📖 Guide",
        "📋 Offres d'Emploi",
        "📤 Candidatures",
        "🤖 Agents IA",
        "🎤 Simulation entretien",
        "🤝 Réseau",
        "📦 Livrables",
        "📅 Planificateur",
        "💬 Assistant IA",
        "⚙️ Paramètres"
    ]
    # Page Admin visible uniquement pour les administrateurs
    if st.session_state.get("is_admin"):
        nav_options.append("👑 Admin")

    page = st.radio(
        "Navigation",
        nav_options,
        label_visibility="collapsed"
    )

    st.markdown("---")

    # User info
    if st.session_state.user_email:
        st.markdown(f"👤 **{st.session_state.user_email}**")
        # Gestion de l'abonnement (uniquement si la facturation est activée et que
        # l'utilisateur a un abonnement actif/à gérer).
        if billing.enabled() and st.session_state.user_id \
                and not st.session_state.is_admin \
                and billing.is_active(st.session_state.user_id):
            billing.manage_button(st.session_state.user_id)
        if st.button("🚪 Déconnexion"):
            if _cookies is not None:
                try:
                    # Supprimer + écraser par une valeur expirée (double sécurité)
                    _cookies.delete("gja_auth", key="gja_del")
                except Exception:
                    pass
            st.session_state.auth_ok = False
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.is_admin = False
            st.session_state.real_admin_email = None
            st.session_state.is_whitelisted = False
            st.session_state.logged_out = True  # bloque la restauration par cookie
            st.rerun()

    # Marqueur de build : vérifier d'un coup d'œil le commit déployé sur Render
    _b_commit, _b_time = _build_info()
    st.markdown("---")
    st.caption(f"🔖 build `{_b_commit}` · {_b_time}")

# ============================================================
# BARRIÈRE D'ACCÈS — utilisateurs non approuvés
# ============================================================
# Un utilisateur connecté mais non approuvé (et non admin) ne voit rien
# tant qu'un administrateur ne l'a pas validé.
if st.session_state.user_id and not st.session_state.is_admin \
        and not st.session_state.is_whitelisted:
    # Si l'abonnement est activé : un abonné passe ; sinon on affiche l'écran
    # d'abonnement (st.stop interne). Si l'abonnement est désactivé (flag off),
    # on garde EXACTEMENT l'ancien comportement (approbation admin manuelle).
    if not (billing.enabled() and billing.gate_or_subscribe(
            st.session_state.user_id, st.session_state.user_email)):
        section_header("⏳ Compte en attente d'approbation", "")
        alert(
            "Votre compte a bien été créé mais il doit être **approuvé par un "
            "administrateur** avant que vous puissiez utiliser GetJobAI. "
            "Vous recevrez un accès dès validation. Merci de votre patience !",
            "warning"
        )
        st.stop()

# ============================================================
# PAGE: DASHBOARD
# ============================================================

if page == "🏠 Dashboard":
    hero_holographic(
        "GetJobAI — Tableau de Bord",
        f"Votre recherche d'emploi en pilote automatique · {datetime.now().strftime('%d %B %Y')}"
    )

    # Charger stats depuis Supabase
    if st.session_state.user_id:
        try:
            db = get_supabase_client()
            job_stats = db.get_stats(st.session_state.user_id)
            cand_stats = db.get_candidatures(st.session_state.user_id)

            total_offres = job_stats.get("total_offres", 0)
            offres_semaine = job_stats.get("offres_semaine", 0)
            score_moyen = job_stats.get("score_moyen", 0)
            total_cands = cand_stats.get("envoyees", 0) + cand_stats.get("en_attente", 0)

            # Stats principales
            stats_grid([
                {
                    "label": "Total Offres",
                    "value": str(total_offres),
                    "icon": "📊",
                    "delta": f"+{offres_semaine} cette semaine"
                },
                {
                    "label": "Candidatures",
                    "value": str(total_cands),
                    "icon": "📤",
                    "delta": f"+{cand_stats.get('en_attente', 0)} en attente"
                },
                {
                    "label": "Taux de Match",
                    "value": f"{score_moyen}%",
                    "icon": "🎯",
                    "delta": "Basé sur IA scoring"
                },
                {
                    "label": "Réponses",
                    "value": str(cand_stats.get("reponses", 0)),
                    "icon": "💬",
                    "delta": f"{cand_stats.get('entretiens', 0)} entretiens"
                }
            ])
        except Exception as e:
            st.error(f"Erreur chargement stats: {e}")
            # Fallback stats
            stats_grid([
                {"label": "Total Offres", "value": "175", "icon": "📊", "delta": "+55"},
                {"label": "Candidatures", "value": "61", "icon": "📤", "delta": "+28"},
                {"label": "Taux Match", "value": "88%", "icon": "🎯", "delta": "+5%"},
                {"label": "Réponses", "value": "12", "icon": "💬", "delta": "+3"}
            ])
    else:
        # Fallback si pas d'user
        stats_grid([
            {"label": "Total Offres", "value": "175", "icon": "📊", "delta": "+55"},
            {"label": "Candidatures", "value": "61", "icon": "📤", "delta": "+28"},
            {"label": "Taux Match", "value": "88%", "icon": "🎯", "delta": "+5%"},
            {"label": "Réponses", "value": "12", "icon": "💬", "delta": "+3"}
        ])

    st.markdown("<br>", unsafe_allow_html=True)

    # Notifications
    alert("✅ Job Hunter a terminé: 22 nouvelles offres trouvées!", "success")
    alert("✅ Indeed Agent a terminé: 55 offres uploadées (4 sources actives)", "success")

    st.markdown("<br>", unsafe_allow_html=True)

    # Section Agents
    section_header("🤖 Agents IA Actifs", "Vos assistants automatisés")

    col1, col2 = st.columns(2)

    with col1:
        card(
            "Job Hunter",
            "Scraping LinkedIn + Job Bank - Dernière exécution: 22 offres",
            "success",
            "🎯"
        )
        progress_bar("Dernière exécution", 100, 100, "success")

    with col2:
        card(
            "Indeed Agent",
            "Multi-sources: LinkedIn, Job Bank, Talent.com, Charity Village",
            "primary",
            "🔍"
        )
        progress_bar("Dernière exécution", 100, 100, "primary")

    st.markdown("<br>", unsafe_allow_html=True)

    # Activité récente
    section_header("📈 Activité Récente")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Dernières Offres")
        st.markdown("""
        - **Pomerleau** - Chargé de Projet Junior (Score: 85)
        - **VINCI** - Coordinateur Travaux (Score: 82)
        - **Bird Construction** - Estimateur Junior (Score: 78)
        - **Chandos** - Surveillant Chantier (Score: 72)
        """)

    with col2:
        st.markdown("### 📤 Dernières Candidatures")
        st.markdown("""
        - **PCL Construction** - Envoyée il y a 2h
        - **Stantec** - Envoyée il y a 5h
        - **EllisDon** - En attente d'approbation
        - **Aecom** - En attente d'approbation
        """)

# ============================================================
# PAGE: OFFRES D'EMPLOI
# ============================================================

elif page == "📋 Offres d'Emploi":
    if not st.session_state.user_id:
        section_header("📋 Offres d'Emploi", "")
        alert("Connectez-vous pour voir vos offres.", "warning")
    else:
        db = get_supabase_client()
        # Charger les VRAIES offres de l'utilisateur depuis Supabase
        all_jobs = db.get_jobs(st.session_state.user_id, limit=500)

        hero_holographic(
            "📋 Offres d'Emploi",
            f"{len(all_jobs)} offres trouvées par vos agents"
        )

        # Sources réellement présentes dans les données
        sources_dispo = sorted({j.get("source", "") for j in all_jobs if j.get("source")})

        # Filtres
        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
        with col1:
            sel_sources = st.multiselect("Sources", sources_dispo, default=[])
        with col2:
            score_min = st.slider("Score minimum", 0, 100, 0)
        with col3:
            tri = st.selectbox("Trier par", ["🕒 Plus récentes", "🎯 Meilleur score"])
        with col4:
            search = st.text_input("🔍 Rechercher", placeholder="Titre ou entreprise...")

        # Appliquer les filtres
        results = []
        for j in all_jobs:
            score = j.get("score") or 0
            if score < score_min:
                continue
            if sel_sources and j.get("source") not in sel_sources:
                continue
            if search:
                hay = (str(j.get("title", "")) + " " + str(j.get("company", ""))).lower()
                if search.lower() not in hay:
                    continue
            # Normaliser le score (job_card_pro plante si None)
            j["score"] = score
            j["_date_aff"] = _fmt_dt(j.get("scraped_at"))
            results.append(j)

        # Tri hiérarchique : plus récentes (scraped_at) OU meilleur score
        if tri == "🎯 Meilleur score":
            results.sort(key=lambda x: x.get("score") or 0, reverse=True)
        else:
            results.sort(key=lambda x: x.get("scraped_at") or "", reverse=True)

        st.caption(f"📊 {len(results)} offre(s) affichée(s) • {tri.lower()}")
        st.markdown("<br>", unsafe_allow_html=True)

        if not results:
            empty_state("🔍", "Aucune offre ne correspond",
                        "Ajustez vos filtres, ou lancez <b>🔎 Job Hunter</b> / "
                        "<b>COOP Hunter</b> (page 🤖 Agents IA) pour remplir votre liste d'offres.")
        else:
            # URLs déjà en candidatures → éviter de re-préparer
            cand_urls = {c.get("job_url") for c in db.get_candidatures_list(st.session_state.user_id)}
            for idx, offre in enumerate(results[:100]):
                job_card_pro(offre)
                ourl = offre.get("url") or ""
                key = offre.get("id") or f"{idx}"
                if ourl and ourl in cand_urls:
                    st.caption("✅ Déjà en 📤 Candidatures (en attente de validation)")
                else:
                    if st.button("📝 Préparer en candidature", key=f"prep_off_{key}",
                                 use_container_width=True):
                        db.create_action(st.session_state.user_id, "candidature_prep", {
                            "job_url": ourl,
                            "job_id": str(offre.get("id") or ""),
                            "job_title": offre.get("title") or "",
                            "company": offre.get("company") or "",
                            "location": offre.get("location") or "",
                            "score": offre.get("score") or 0,
                        })
                        st.success("✅ Lancé ! Lettre + CV adapté en préparation → "
                                   "retrouvez-la dans 📤 Candidatures (statut « en attente ») "
                                   "pour l'approuver.")
                st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# PAGE: CANDIDATURES
# ============================================================

elif page == "📤 Candidatures":
    hero_holographic(
        "📤 Mes Candidatures",
        "Suivez l'état de vos candidatures"
    )

    # Stats candidatures RÉELLES depuis Supabase
    if st.session_state.user_id:
        db = get_supabase_client()
        cand = db.get_candidatures(st.session_state.user_id)
        en_attente = cand.get("en_attente", 0)
        stats_grid([
            {"label": "En Attente", "value": str(en_attente), "icon": "⏳"},
            {"label": "Envoyées", "value": str(cand.get("envoyees", 0)), "icon": "✅"},
            {"label": "Réponses", "value": str(cand.get("reponses", 0)), "icon": "💬"},
            {"label": "Entretiens", "value": str(cand.get("entretiens", 0)), "icon": "🎯"}
        ])
    else:
        en_attente = 0

    st.markdown("<br>", unsafe_allow_html=True)

    # Liste RÉELLE des candidatures depuis Supabase
    if st.session_state.user_id:
        cands = db.get_candidatures_list(st.session_state.user_id)

        cv_texte = db.get_user_cv(st.session_state.user_id)

        if not cands:
            empty_state("📭", "Aucune candidature pour l'instant",
                        "Lancez <b>📝 Préparer Candidatures</b> (page 🤖 Agents IA) : il génère "
                        "vos lettres et les place ici, en attente de votre validation.")
        else:
            statut_icon = {
                "en_attente": "⏳", "validee": "✔️", "a_envoyer": "📨", "sans_email": "✉️",
                "easyapply": "📝", "envoi_en_cours": "📤", "envoyee": "✅", "recue": "📬",
                "relancee": "🔁", "reponse": "💬", "entretien": "🎯", "refus": "❌",
                "a_explorer": "🔎",
            }
            # Classement hiérarchique : les plus récentes en premier (date + heure)
            cands = sorted(cands, key=lambda c: c.get("created_at") or "", reverse=True)

            # Filtre par statut : retrouver Réponses, Entretiens, etc. d'un clic
            GROUPES = {
                "Toutes": None,
                "⏳ À valider": ("en_attente", "validee"),
                "📨 À envoyer": ("a_envoyer", "sans_email"),
                "📝 Easy Apply (LinkedIn)": ("easyapply",),
                "🔎 À explorer (portails stages)": ("a_explorer",),
                "✅ Envoyées": ("envoyee", "recue", "envoi_en_cours", "relancee"),
                "💬 Réponses": ("reponse",),
                "🎯 Entretiens": ("entretien",),
                "❌ Refus": ("refus",),
            }
            def _match_grp(c, toks):
                if toks is None:
                    return True
                stt = (c.get("status") or "").lower()
                return any(t in stt for t in toks)
            options = ["Toutes"] + [g for g in GROUPES if g != "Toutes"
                                    and any(_match_grp(c, GROUPES[g]) for c in cands)]
            labels = {g: (f"{g} ({sum(1 for c in cands if _match_grp(c, GROUPES[g]))})"
                          if g != "Toutes" else f"Toutes ({len(cands)})") for g in options}
            choix = st.radio("Filtrer par statut", options,
                             format_func=lambda g: labels[g], horizontal=True)

            vis = [c for c in cands if _match_grp(c, GROUPES[choix])]
            en_attente_list = [c for c in cands if (c.get("status") or "") == "en_attente"]
            st.caption(f"📋 {len(vis)} candidature(s) affichée(s) • {len(en_attente_list)} à valider "
                       "• triées des plus récentes aux plus anciennes")
            st.markdown("<br>", unsafe_allow_html=True)

            for c in vis:
                cid = c.get("id")
                stt = (c.get("status") or "").lower()
                icon = next((v for k, v in statut_icon.items() if k in stt), "📄")
                titre = c.get("job_title") or "Poste"
                company = c.get("company") or "—"
                score = c.get("score_match") or 0
                lettre = c.get("lettre") or "(pas de lettre)"
                cv_nom = c.get("cv_nom") or "CV.pdf"
                url = c.get("job_url") or ""

                date_aff = _fmt_dt(c.get("created_at"))
                with st.container(border=True):
                    st.markdown(f"### {icon} {titre} — {company}")
                    st.caption((f"🕒 {date_aff} • " if date_aff else "")
                               + f"Score {score}/100 • Statut: **{c.get('status','')}**"
                               + (f" • [Voir l'offre]({url})" if url else ""))

                    # RÉPONSE DÉTECTÉE : extrait du message + lien direct Gmail
                    if stt in ("reponse", "entretien", "recue"):
                        _ex = (c.get("reponse_extrait") or "").strip()
                        _gq = (company or "").replace(" ", "%20")
                        _gurl = f"https://mail.google.com/mail/u/0/#search/{_gq}"
                        _ttl = ("🎯 Invitation à un entretien" if stt == "entretien"
                                else "💬 Réponse reçue" if stt == "reponse"
                                else "📬 Accusé de réception")
                        if _ex:
                            _safe = _ex.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                            st.markdown(
                                "<div style='background:rgba(34,197,94,0.10);border:1px solid "
                                "rgba(34,197,94,0.35);border-radius:10px;padding:10px 12px;margin:4px 0;'>"
                                f"<b>{_ttl}</b><br><span style='color:#cfe9d6'>{_safe}</span></div>",
                                unsafe_allow_html=True)
                        else:
                            st.info(f"{_ttl} — le message complet est dans votre Gmail.")
                        st.markdown(f"📬 [Ouvrir le message dans Gmail]({_gurl})")

                    # Lire la LETTRE
                    with st.expander("✉️ Lire la lettre de motivation"):
                        st.write(lettre)
                    # Lire le CV ADAPTÉ à cette offre (sinon CV de base)
                    cv_offre = c.get("cv_adapte") or cv_texte
                    label_cv = "📎 Lire mon CV adapté à cette offre" if c.get("cv_adapte") else f"📎 Lire mon CV ({cv_nom})"
                    with st.expander(label_cv):
                        if cv_offre:
                            st.text(cv_offre)
                        else:
                            st.info("CV non disponible. Ajoutez-le dans Paramètres.")

                    # TÉLÉCHARGER en PDF (pour postuler manuellement)
                    base = _nom_fichier(f"{company}_{titre}")
                    dlL, dlCV = st.columns(2)
                    with dlL:
                        if lettre and lettre != "(pas de lettre)":
                            st.download_button(
                                "📥 Lettre (PDF)",
                                data=texte_vers_pdf(lettre, f"Lettre de motivation — {titre}"),
                                file_name=f"Lettre_{base}.pdf", mime="application/pdf",
                                key=f"dlL_{cid}", use_container_width=True)
                    with dlCV:
                        if cv_offre:
                            st.download_button(
                                "📥 CV (PDF)",
                                data=texte_vers_pdf(cv_offre, "Curriculum Vitae"),
                                file_name=f"CV_{base}.pdf", mime="application/pdf",
                                key=f"dlCV_{cid}", use_container_width=True)

                    # MODE COPILOTE : approuver -> l'agent enverra par email
                    if stt in ("en_attente", "validee"):
                        if st.button("🚀 Approuver & Postuler (email auto)", key=f"appr_{cid}",
                                     type="primary"):
                            db.update_candidature_status(cid, "a_envoyer")
                            st.success("✅ Approuvée ! Lancez l'agent 🚀 Postuler (Copilote) "
                                       "pour l'envoyer.")
                            st.rerun()
                    elif stt == "a_envoyer":
                        st.info("📨 Approuvée — en file d'envoi. Lancez 🚀 Postuler (Copilote).")
                    elif stt == "sans_email":
                        st.warning("✉️ Aucun email RH trouvé — **à postuler manuellement** : "
                                   "téléchargez la **lettre** et le **CV en PDF** ci-dessus, "
                                   "ouvrez l'offre, et déposez-les sur le formulaire de l'employeur.")

                    # Suivi du cycle de vie réel : Envoyée → Réponse (Refus | Entretien)
                    st.caption("📊 Statut de la candidature :")
                    # Rangée 1 (3 boutons) + rangée 2 (2 boutons) — lisible sur mobile
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("⏳ En attente", key=f"s_att_{cid}", use_container_width=True,
                                     disabled=(stt == "en_attente")):
                            db.update_candidature_status(cid, "en_attente"); st.rerun()
                    with b2:
                        if st.button("📤 Envoyée", key=f"s_env_{cid}", type="primary", use_container_width=True,
                                     disabled=(stt == "envoyee")):
                            db.update_candidature_status(cid, "envoyee"); st.rerun()
                    with b3:
                        if st.button("❌ Refus", key=f"s_ref_{cid}", use_container_width=True,
                                     disabled=("refus" in stt)):
                            db.update_candidature_status(cid, "refus"); st.rerun()
                    b4, b5 = st.columns(2)
                    with b4:
                        if st.button("🎯 Entretien !", key=f"s_ent_{cid}", use_container_width=True,
                                     disabled=(stt == "entretien")):
                            db.update_candidature_status(cid, "entretien"); st.rerun()
                    with b5:
                        if st.button("🗑️ Suppr.", key=f"s_del_{cid}", use_container_width=True):
                            db.delete_candidature(cid); st.rerun()

                    # Si entretien obtenu -> préparer CET entretien (ciblé entreprise/poste)
                    if stt == "entretien":
                        if st.button(f"🎙️ Préparer cet entretien ({company})", key=f"prep_{cid}",
                                     type="primary"):
                            action = db.create_action(
                                user_id=st.session_state.user_id,
                                agent_name="entretien_prep",
                                params={"source": "candidature", "job_title": titre, "company": company}
                            )
                            if action and action.get("id"):
                                alert(f"🎙️ Préparation d'entretien lancée pour {company} ! "
                                      "Suivez-la dans 🤖 Agents IA, résultat dans 📦 Livrables.", "success")
                            else:
                                st.error("Échec du lancement.")

# ============================================================
# PAGE: SIMULATION ENTRETIEN (live)
# ============================================================

elif page == "🎤 Simulation entretien":
    simulation_entretien_page(st.session_state.user_id, {})

# ============================================================
# PAGE: AGENTS IA
# ============================================================

elif page == "🤖 Agents IA":
    hero_holographic(
        "🤖 Agents IA",
        "Lancez vos assistants de recherche d'emploi automatisés"
    )

    # ----- MONITEUR D'EXÉCUTION EN DIRECT (animation + logs) -----
    if st.session_state.get("monitor_action_id"):

        @st.fragment(run_every="3s")
        def live_monitor():
            db = get_supabase_client()
            action = db.get_action(st.session_state.monitor_action_id)
            if not action:
                st.warning("Action introuvable.")
                return
            statut = action.get("status", "pending")
            res = action.get("result") or {}
            live_log = res.get("live_log", "") if isinstance(res, dict) else ""
            agent_nom = st.session_state.get("monitor_agent", "Agent")

            # Étapes animées selon le statut
            etapes = ["🔌 Connexion", "🔍 Recherche", "🧮 Analyse", "☁️ Upload"]
            if statut == "pending":
                actif, libelle, couleur = 0, "En file d'attente…", "#f59e0b"
            elif statut == "processing":
                # progression visuelle basée sur la taille du log
                actif = min(3, 1 + len(live_log) // 800)
                libelle, couleur = "En cours d'exécution…", "#667eea"
            elif statut == "completed":
                actif, libelle, couleur = 4, "Terminé ✅", "#10b981"
            else:
                actif, libelle, couleur = -1, "Échec ❌", "#ef4444"

            # Barre d'étapes animée
            chips = ""
            for idx, et in enumerate(etapes):
                done = (actif > idx) or actif == 4
                running = (idx == actif and statut == "processing")
                bg = couleur if (done or running) else "#e5e7eb"
                txt = "white" if (done or running) else "#9ca3af"
                pulse = "animation: pulse 1s infinite;" if running else ""
                chips += (f"<span style='background:{bg};color:{txt};padding:6px 14px;"
                          f"border-radius:20px;margin:3px;display:inline-block;"
                          f"font-size:0.85rem;{pulse}'>{et}</span>")

            # Loader 3D pendant l'exécution, icône finale sinon
            if statut in ("pending", "processing"):
                visuel = holo_loader_3d()
            else:
                visuel = f"<span style='font-size:2.6rem'>{'✅' if statut=='completed' else '❌'}</span>"

            # Message de l'étape suivante
            if statut == "pending":
                prochaine = "Démarrage imminent…"
            elif statut == "processing":
                nxt = etapes[actif + 1] if actif + 1 < len(etapes) else "☁️ Finalisation"
                prochaine = f"➡️ Étape suivante : {nxt}"
            elif statut == "completed":
                prochaine = "🎉 Toutes les étapes terminées"
            else:
                prochaine = "⛔ Arrêt sur erreur"

            # Où les résultats sont rangés (propre à chaque agent)
            RESULTS_DEST = {
                "Job Hunter": "📋 Offres d'Emploi",
                "Indeed Agent": "📋 Offres d'Emploi",
                "COOP Hunter": "📋 Offres d'Emploi",
                "Orchestrateur": "📋 Offres d'Emploi + 📤 Candidatures (à valider)",
                "Networking Agent": "🤝 Réseau",
                "Follow-up Engine": "📧 relances envoyées + 📦 Livrables",
                "Préparer Candidatures": "📤 Candidatures (à valider)",
                "Préparer mon Entretien": "📦 Livrables (guide d'entretien)",
                "Suivi Boîte Mail": "📤 Candidatures (statuts mis à jour)",
                "Postuler (Copilote)": "📤 Candidatures envoyées + emails RH",
                "Immigration Advisor": "📦 Livrables + votre email",
                "Profil LinkedIn 10/10": "📦 Livrables",
                "ATS Optimizer": "📦 Livrables (CV optimisés)",
                "Stratégie Carrière": "📦 Livrables",
            }
            dest = RESULTS_DEST.get(agent_nom, "📦 Livrables")

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, rgba(17,28,52,0.92), rgba(10,15,30,0.92));
                 padding:1.4rem 1.6rem;border-radius:16px;border:1px solid rgba(45,212,191,0.25);
                 border-left:5px solid {couleur};margin-bottom:1rem;
                 box-shadow:0 0 24px rgba(30,155,255,0.14);">
              <div style="display:flex;align-items:center;gap:18px;">
                {visuel}
                <div>
                  <h3 style="color:#eaf6ff;margin:0;">{agent_nom}</h3>
                  <p style="color:#9fc7e8;margin:.2rem 0 0 0;font-size:0.92rem;">{libelle}</p>
                  <p style="color:#2dd4bf;margin:.35rem 0 0 0;font-size:0.9rem;font-weight:600;">{prochaine}</p>
                </div>
              </div>
              <div style="margin-top:1rem;">{chips}</div>
              <div style="margin-top:1rem;padding:.7rem 1rem;border-radius:10px;
                   background:rgba(30,155,255,0.08);border:1px dashed rgba(45,212,191,0.35);
                   color:#cfe2f5;font-size:0.9rem;">
                📍 <strong>Où trouver les résultats :</strong> {dest}
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Logs en direct
            st.markdown("**📜 Logs en direct (avancement)**")
            st.code(live_log[-2500:] or "En attente de la sortie de l'agent…", language="text")

            if statut in ("completed", "failed"):
                if statut == "completed":
                    st.success(f"✅ {agent_nom} terminé ! 📍 Résultats : {dest}")
                else:
                    st.error(f"❌ {agent_nom} a échoué. Voir les logs ci-dessus.")
                if st.button("✖️ Fermer le moniteur", key="close_monitor"):
                    st.session_state.monitor_action_id = None
                    st.rerun()

        live_monitor()
        st.markdown("---")

    # Agents disponibles
    agents = [
        {
            "name": "Job Hunter",
            "desc": "Scraping LinkedIn + Job Bank Canada",
            "icon": "🎯",
            "color": "primary",
            "stats": "Dernière exec: 22 offres • Taux: 88%"
        },
        {
            "name": "Indeed Agent",
            "desc": "Multi-sources (4 plateformes actives)",
            "icon": "🔍",
            "color": "secondary",
            "stats": "Dernière exec: 55 offres • Sources: LinkedIn, Job Bank, Talent.com, Charity Village"
        },
        {
            "name": "COOP Hunter",
            "desc": "Recherche stages COOP spécialisés",
            "icon": "🎓",
            "color": "success",
            "stats": "Spécialisé: Stages Coop génie civil"
        },
        {
            "name": "Orchestrateur",
            "desc": "Diversifie la recherche : fonction publique fédérale (GC Jobs) + The Muse, Remotive, RemoteOK, Jobicy",
            "icon": "🧭",
            "color": "info",
            "stats": "Complémentaire à Job Hunter & Indeed • transparent sur les sources bloquées"
        },
        {
            "name": "Networking Agent",
            "desc": "Messages LinkedIn automatisés",
            "icon": "🤝",
            "color": "info",
            "stats": "Réseau: Recruteurs + Hiring Managers"
        },
        {
            "name": "Follow-up Engine",
            "desc": "Relances automatiques candidatures",
            "icon": "📧",
            "color": "primary",
            "stats": "Relances J+7, J+14, J+21"
        },
        {
            "name": "Préparer Candidatures",
            "desc": "Génère vos lettres (à valider, SANS envoi)",
            "icon": "📝",
            "color": "success",
            "stats": "Mode validation: vous lisez avant d'envoyer"
        },
        {
            "name": "Préparer mon Entretien",
            "desc": "Guide d'entretien personnalisé (NotebookLM + votre CV)",
            "icon": "🎙️",
            "color": "info",
            "stats": "Pitch + questions probables + réponses + conseils"
        },
        {
            "name": "Suivi Boîte Mail",
            "desc": "Lit votre Gmail et met à jour les statuts (reçue/refus/entretien)",
            "icon": "📬",
            "color": "secondary",
            "stats": "Détecte accusés de réception et réponses automatiquement"
        },
        {
            "name": "Postuler (Copilote)",
            "desc": "Postule aux candidatures APPROUVÉES : email RH + LinkedIn Easy Apply",
            "icon": "🚀",
            "color": "danger",
            "stats": "Email 25/j + LinkedIn 15/j • simulation humaine • offres approuvées seulement"
        },
        {
            "name": "Immigration Advisor",
            "desc": "Conseils immigration Canada (PVT, RP, Arrima)",
            "icon": "🍁",
            "color": "success",
            "stats": "Programmes fédéraux + Québec"
        },
        {
            "name": "Post LinkedIn",
            "desc": "Génère un post engageant (vous copiez et publiez vous-même)",
            "icon": "📝",
            "color": "info",
            "stats": "Texte prêt à coller • 0 risque • vous gardez le contrôle"
        },
        {
            "name": "Profil LinkedIn 10/10",
            "desc": "Optimise votre profil LinkedIn au max",
            "icon": "⭐",
            "color": "warning",
            "stats": "Headline, résumé, mots-clés ATS"
        },
        {
            "name": "ATS Optimizer",
            "desc": "Optimise CV pour les filtres ATS",
            "icon": "🤖",
            "color": "secondary",
            "stats": "Mots-clés + format compatible robots"
        },
        {
            "name": "Stratégie Carrière",
            "desc": "Plan de carrière personnalisé",
            "icon": "🧭",
            "color": "success",
            "stats": "Objectifs + roadmap génie civil"
        }
    ]

    # Afficher agents en grille avec exécution fonctionnelle
    col1, col2 = st.columns(2)

    # Mapping agent name → action_type (= nom du fichier .py dans agents/)
    agent_mapping = {
        "Job Hunter": "job_hunter",
        "Indeed Agent": "indeed_agent",
        "COOP Hunter": "coop_hunter",
        "Orchestrateur": "chercheur_offres",
        "Networking Agent": "networking_agent",
        "Follow-up Engine": "followup_engine",
        "Préparer Candidatures": "candidature_prep",
        "Préparer mon Entretien": "entretien_prep",
        "Suivi Boîte Mail": "mail_tracker",
        "Postuler (Copilote)": "candidature_send",
        "Immigration Advisor": "immigration_advisor",
        "Post LinkedIn": "linkedin_agent",
        "Profil LinkedIn 10/10": "profile_optimizer",
        "ATS Optimizer": "ats_optimizer",
        "Stratégie Carrière": "career_strategy_agent"
    }

    _AG_ACCENTS = ["blue", "purple", "green", "orange", "cyan"]
    for i, agent in enumerate(agents):
        with col1 if i % 2 == 0 else col2:
            card(agent["name"], agent["desc"], agent["color"], agent["icon"],
                 accent=_AG_ACCENTS[i % len(_AG_ACCENTS)], footer=f"📊 {agent['stats']}")

            if st.button(f"🚀 Lancer {agent['name']}", key=f"launch_{i}", use_container_width=True):
                # Post LinkedIn = génération manuelle dans le Dashboard (pas de publication auto)
                if agent["name"] == "Post LinkedIn":
                    st.session_state.show_post_gen = True
                    st.session_state.pop("gen_post_text", None)
                    st.rerun()
                elif st.session_state.user_id:
                    try:
                        db = get_supabase_client()
                        agent_type = agent_mapping.get(agent["name"], "unknown")
                        action = db.create_action(
                            user_id=st.session_state.user_id,
                            agent_name=agent_type,
                            params={"source": "dashboard"}
                        )
                        if action and action.get("id"):
                            # Démarrer le moniteur en direct
                            st.session_state.monitor_action_id = action["id"]
                            st.session_state.monitor_agent = agent["name"]
                            st.rerun()
                        elif action:
                            alert(f"✅ {agent['name']} lancé! (suivi indisponible)", "success")
                        else:
                            st.error("❌ Échec du lancement - vérifiez les logs Supabase")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                else:
                    st.error("User ID manquant - impossible de lancer l'agent")

            st.markdown("<br>", unsafe_allow_html=True)

    # ── Générateur de post LinkedIn (manuel — vous copiez et publiez) ──────────
    if st.session_state.get("show_post_gen"):
        st.markdown("---")
        section_header("📝 Post LinkedIn", "Générez un post, copiez-le, publiez-le vous-même sur LinkedIn")

        # Profil + préférences de CHAQUE utilisateur (Paramètres)
        _db_pref = get_supabase_client()
        _prefs = _db_pref.get_user_settings(st.session_state.user_id) or {}
        _pref_genre = _prefs.get("post_genre", "")
        _pref_peau = _prefs.get("post_peau", "")
        _pref_nom = _prefs.get("full_name") or _prefs.get("nom_complet") or ""
        _pref_secteur = (_prefs.get("sector") or _prefs.get("keywords") or "").replace("\n", ", ").strip(", ")
        _pref_ville = _prefs.get("ville") or ""
        _pref_tag = _prefs.get("post_tag") or ""
        _pref_photo = _prefs.get("photo_b64") or ""
        _pref_lang = {"Français": "fr", "Anglais": "en",
                      "Bilingue (FR + EN)": "fr"}.get(_prefs.get("post_langue"), "fr")
        _pref_editos = [e for e in [_prefs.get("post_edito1"), _prefs.get("post_edito2")]
                        if e and e != "(aucune)"]
        if not _pref_secteur:
            st.warning("⚠️ Renseignez votre **métier / secteur** dans **Paramètres → 👤 Profil** "
                       "(ou ci-dessous) pour que le post colle à VOTRE profession.")

        cga, cgb, cgc = st.columns([2, 1, 1])
        with cga:
            pg_secteur = st.text_input(
                "Votre métier / compétences (le post s'aligne dessus)",
                value=_pref_secteur, placeholder="ex : infirmière, marketing digital, comptabilité…",
                key="pg_secteur")
        with cgb:
            pg_ville = st.text_input("Ville", value=_pref_ville, key="pg_ville")
        with cgc:
            pg_langue = st.selectbox("Langue", ["fr", "en"],
                                     index=(0 if _pref_lang == "fr" else 1), key="pg_langue",
                                     format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English")
        pg_theme = st.text_input("Thème (optionnel — laissez vide pour un thème automatique)",
                                 value="", key="pg_theme")

        pg_avec_image = st.checkbox("🖼️ Générer aussi une image hyper-réaliste alignée sur le post",
                                    value=True, key="pg_avec_image")
        pg_moi = False
        if _pref_photo:
            pg_moi = st.checkbox("🧑 Me mettre en avant (image qui me RESSEMBLE, depuis ma photo)",
                                 value=True, key="pg_moi")
        else:
            st.caption("💡 Ajoutez une photo dans **Paramètres → 🎨 Post LinkedIn** pour des images "
                       "qui vous ressemblent (posts qui vous mettent en avant).")
        _photo_pour_image = _pref_photo if pg_moi else ""

        c_gen, c_close = st.columns([3, 1])
        with c_gen:
            if st.button("✨ Générer le post", type="primary", use_container_width=True):
                with st.spinner("Génération du post…"):
                    st.session_state.gen_post_text = generer_post_linkedin(
                        secteur=pg_secteur, ville=pg_ville, langue=pg_langue,
                        theme=pg_theme or None, editos=_pref_editos,
                        nom=_pref_nom, tag_personne=_pref_tag,
                    )
                st.session_state.pop("gen_post_image", None)
                if pg_avec_image:
                    with st.spinner("Génération de l'image hyper-réaliste (gpt-image-1, ~15s)…"):
                        st.session_state.gen_post_image = generer_image_post(
                            st.session_state.gen_post_text, secteur=pg_secteur,
                            genre=_pref_genre, peau=_pref_peau, photo_b64=_photo_pour_image)
        with c_close:
            if st.button("✖ Fermer", use_container_width=True):
                st.session_state.show_post_gen = False
                st.session_state.pop("gen_post_text", None)
                st.session_state.pop("gen_post_image", None)
                st.rerun()

        post_txt = st.session_state.get("gen_post_text", "")
        if post_txt:
            # On peut relire/modifier le texte avant publication
            post_edit = st.text_area("Post généré (vous pouvez le modifier avant de valider)",
                                     value=post_txt, height=320, key="pg_output")

            # Image générée (gpt-image-1, base64) — affichée pour validation
            img_b64 = st.session_state.get("gen_post_image")
            if img_b64:
                try:
                    _img_bytes = base64.b64decode(img_b64)
                    st.image(_img_bytes,
                             caption="🖼️ Image hyper-réaliste générée (alignée sur le post)",
                             use_container_width=True)
                    st.download_button("⬇️ Télécharger l'image", data=_img_bytes,
                                       file_name="post_linkedin.png", mime="image/png",
                                       use_container_width=True, key="pg_dl_img")
                except Exception:
                    st.caption("⚠️ Aperçu image indisponible.")
                if st.button("🔄 Régénérer l'image", key="pg_regen_img"):
                    with st.spinner("Nouvelle image (gpt-image-1)…"):
                        st.session_state.gen_post_image = generer_image_post(
                            post_edit, secteur=pg_secteur,
                            genre=_pref_genre, peau=_pref_peau, photo_b64=_photo_pour_image)
                    st.rerun()
            elif pg_avec_image:
                st.caption("⚠️ Image non générée (quota OpenAI ou erreur) — le post peut être publié sans image.")

            # --- Connexion LinkedIn (API officielle) : statut + bouton ---
            import linkedin_oauth as _lio
            _db = get_supabase_client()
            _li = _lio.get_status(_db, st.session_state.user_id) if st.session_state.user_id else {"connected": False}
            if _lio.is_configured():
                _au = _lio.build_authorize_url(st.session_state.user_id)
                if _li.get("connected"):
                    st.success("🔗 LinkedIn connecté — publication automatique disponible.")
                    st.link_button("🔄 Reconnecter LinkedIn (si le jeton est révoqué/expiré)",
                                   _au, use_container_width=True)
                else:
                    st.warning("🔗 LinkedIn non connecté. Connectez-le **une fois** pour publier "
                               "automatiquement (sans extension).")
                    st.link_button("🔗 Connecter LinkedIn", _au, use_container_width=True)

            # --- Publier : API officielle (auto) prioritaire, extension en repli ---
            if _lio.is_configured() and _li.get("connected"):
                if st.button("🚀 Publier maintenant sur LinkedIn (API)", type="primary",
                             use_container_width=True, key="pg_publish_api"):
                    with st.spinner("Publication via l'API officielle LinkedIn…"):
                        ok, info = _lio.publish_for_user(
                            _db, st.session_state.user_id, post_edit,
                            st.session_state.get("gen_post_image", ""))
                    if ok:
                        st.success("✅ Post publié sur LinkedIn ! (texte + image)")
                    else:
                        st.error(f"❌ Échec API : {info}")

                # --- Planifier la publication (date + heure, heure de l'Est) ---
                with st.expander("📅 Planifier la publication (au lieu de publier maintenant)"):
                    from datetime import date as _date, time as _time, datetime as _dtmod
                    cD, cH = st.columns(2)
                    with cD:
                        d_pub = st.date_input("Date", min_value=_date.today(), key="pg_sched_date")
                    with cH:
                        h_pub = st.time_input("Heure (heure de l'Est)", value=_time(9, 0), key="pg_sched_time")
                    if st.button("📅 Planifier ce post", use_container_width=True, key="pg_sched_btn"):
                        try:
                            from zoneinfo import ZoneInfo
                            dt_local = _dtmod.combine(d_pub, h_pub, tzinfo=ZoneInfo("America/Toronto"))
                        except Exception:
                            from datetime import timezone as _tz
                            dt_local = _dtmod.combine(d_pub, h_pub, tzinfo=_tz.utc)
                        from datetime import timezone as _tz2
                        if dt_local <= _dtmod.now(dt_local.tzinfo):
                            st.warning("⚠️ Choisissez une date/heure dans le futur.")
                        else:
                            iso_utc = dt_local.astimezone(_tz2.utc).isoformat()
                            okp = _db.create_scheduled_post(
                                st.session_state.user_id, post_edit,
                                st.session_state.get("gen_post_image", ""), iso_utc)
                            if okp:
                                st.success(f"✅ Post planifié pour le {_fmt_dt(iso_utc)} — "
                                           "il sera publié automatiquement (texte + image).")
                            else:
                                st.error("❌ Échec de la planification (colonne scheduled_at créée ? voir SQL).")

            cpub, ccopy = st.columns([2, 1])
            with cpub:
                if st.button("📤 Envoyer à mon extension (repli manuel)",
                             use_container_width=True, key="pg_publish"):
                    if st.session_state.user_id:
                        ok = get_supabase_client().create_post_linkedin(
                            st.session_state.user_id, post_edit,
                            st.session_state.get("gen_post_image", ""))
                        if ok:
                            st.success("✅ Post envoyé à votre extension ! Ouvrez **LinkedIn**, "
                                       "cliquez **« 📤 Publier (GetJobAI) »** en bas à droite, "
                                       "vérifiez et publiez.")
                        else:
                            st.error("❌ Échec de l'envoi (table posts_linkedin créée ? voir SQL).")
                    else:
                        st.error("User ID manquant.")
            with ccopy:
                _safe_post = json.dumps(post_edit)
                components.html(
                    f"""
                    <button onclick='navigator.clipboard.writeText({_safe_post})
                        .then(()=>{{this.innerHTML="✅ Copié !";
                        setTimeout(()=>this.innerHTML="📋 Copier",1600);}})'
                        style="background:linear-gradient(135deg,#1e9bff,#2dd4bf);
                        color:#04101f;border:none;padding:11px 16px;border-radius:8px;
                        cursor:pointer;font-size:15px;font-weight:600;width:100%;
                        box-shadow:0 0 14px rgba(45,212,191,0.35);">
                        📋 Copier
                    </button>
                    """,
                    height=52,
                )
            st.caption("✅ « Approuver et publier » → l'agent publie le post sur LinkedIn pour vous "
                       "(rien n'est publié sans votre validation). 📋 « Copier » reste dispo si vous "
                       "préférez le coller vous-même.")

    # Afficher actions récentes
    section_header("📋 Actions Récentes", "Dernières exécutions d'agents")

    if st.session_state.user_id:
        try:
            db = get_supabase_client()
            actions = db.get_recent_actions(st.session_state.user_id, limit=5)

            if actions:
                for action in actions:
                    stt = (action.get("status") or "pending").lower()
                    libelle, prog = _STATUT_INFO.get(stt, ("⏳ " + stt, 0.10))
                    icon, nom = _agent_label(action)

                    with st.container(border=True):
                        st.markdown(f"**{icon} {nom}** — {libelle}")
                        st.progress(prog, text=libelle)
                        date_aff = _fmt_dt(action.get("created_at"))
                        st.caption(f"🕒 {date_aff}" if date_aff else "")
            else:
                st.info("Aucune action récente")
        except Exception as e:
            st.error(f"Erreur chargement actions: {e}")
    else:
        st.warning("Connectez-vous pour voir vos actions")

# ============================================================
# PAGE: GUIDE D'UTILISATION
# ============================================================

elif page == "📖 Guide":
    hero_holographic(
        "📖 Guide d'utilisation",
        "Comprenez chaque agent : ce qu'il fait, quand l'utiliser, et où trouver vos résultats"
    )

    st.markdown("""
    <div style="background:linear-gradient(135deg, rgba(30,155,255,0.10), rgba(45,212,191,0.08));
         padding:1.2rem 1.4rem;border-radius:14px;border:1px solid rgba(45,212,191,0.30);
         margin-bottom:1.2rem;color:#dceefb;">
      <strong>🚀 Bien démarrer — 3 réglages à faire UNE fois dans ⚙️ Paramètres :</strong><br>
      <b>1. 👤 Profil :</b> CV, mots-clés métier, ville, secteur — ça personnalise <u>tous</u> les agents.<br>
      <b>2. 🔔 Notifications → Gmail d'envoi :</b> votre adresse Gmail + un mot de passe d'application.
      <u>Obligatoire</u> pour que le <b>Copilote</b> postule par email (sinon il affiche « Gmail non configuré »).<br>
      <b>3. 🔗 LinkedIn :</b> connectez votre compte en 1 clic — pour publier vos posts automatiquement.<br>
      <hr style="border-color:rgba(255,255,255,.12);margin:.6rem 0">
      <strong>Ensuite :</strong>
      <b>🤖 Agents IA → Lancer</b> un agent (animation en direct) →
      résultats dans <b>📋 Offres</b>, <b>📤 Candidatures</b>, <b>🤝 Réseau</b>, <b>📦 Livrables</b>
      + un <b>rapport par email</b>.<br>
      <span style="color:#9fc7e8">💡 Pour postuler aux offres LinkedIn « Candidature simplifiée » :
      installez l'<b>extension Chrome GetJobAI</b> → elle remplit le formulaire à votre place,
      vous cliquez juste « Envoyer ».</span>
    </div>
    """, unsafe_allow_html=True)

    # Données du guide : un dictionnaire par agent
    GUIDE = [
        {
            "cat": "🔎 Trouver des offres",
            "items": [
                {
                    "icon": "🎯", "nom": "Job Hunter",
                    "fait": "Cherche des offres d'emploi sur LinkedIn et le Guichet-Emplois "
                            "du Canada (Job Bank), filtrées selon vos mots-clés et votre ville.",
                    "quand": "Pour alimenter votre liste d'offres avec des postes récents et ciblés.",
                    "prerequis": "Paramètres → Mots-clés métier, Ville, Province.",
                    "ou": "📋 Offres d'Emploi",
                },
                {
                    "icon": "🔍", "nom": "Indeed Agent (multi-sources)",
                    "fait": "Comme Job Hunter mais ratisse plusieurs plateformes à la fois "
                            "(LinkedIn, Job Bank, Talent.com, Charity Village).",
                    "quand": "Quand vous voulez un maximum d'offres en un seul lancement.",
                    "prerequis": "Paramètres → Mots-clés métier, Ville.",
                    "ou": "📋 Offres d'Emploi",
                },
                {
                    "icon": "🎓", "nom": "COOP Hunter (stages étudiants)",
                    "fait": "Agent spécial étudiants : trouve des stages COOP/alternance via "
                            "portails universitaires, sites de la fonction publique et entreprises "
                            "ciblées selon votre formation. Peut préparer la candidature (CV + lettre ATS).",
                    "quand": "Si vous êtes étudiant·e à la recherche d'un stage.",
                    "prerequis": "Paramètres → champs étudiants (École, Programme, "
                                 "Parcours scolaire, Ville, Province).",
                    "ou": "📋 Offres d'Emploi + 📤 Candidatures",
                },
                {
                    "icon": "🧭", "nom": "Orchestrateur (sources complémentaires)",
                    "fait": "Diversifie votre recherche sur des plateformes que Job Hunter et "
                            "Indeed Agent ne couvrent pas : fonction publique fédérale (GC Jobs), "
                            "The Muse, Remotive, RemoteOK, Jobicy. Il score chaque offre selon votre "
                            "CV, prépare les meilleures en candidatures (à valider → Copilote), et "
                            "reste transparent : il indique les sources bloquées (ex. Glassdoor, "
                            "Jobillico) et n'invente jamais une offre.",
                    "quand": "Pour élargir vos résultats au-delà de LinkedIn/Indeed/Job Bank.",
                    "prerequis": "Paramètres → Ville, Mots-clés (ou CV).",
                    "ou": "📋 Offres d'Emploi + 📤 Candidatures (à valider)",
                },
            ],
        },
        {
            "cat": "📨 Postuler & suivre",
            "items": [
                {
                    "icon": "📝", "nom": "Préparer Candidatures",
                    "fait": "Génère vos lettres de motivation personnalisées pour les offres "
                            "retenues — SANS rien envoyer. Vous relisez avant.",
                    "quand": "Après avoir trouvé des offres, pour préparer vos dossiers.",
                    "prerequis": "Paramètres → CV. Des offres dans 📋 Offres d'Emploi.",
                    "ou": "📤 Candidatures (statut « à valider »)",
                },
                {
                    "icon": "🚀", "nom": "Postuler (Copilote)",
                    "fait": "Envoie réellement vos candidatures APPROUVÉES : email au RH + "
                            "LinkedIn Easy Apply, avec simulation humaine (limites 25 emails/j, "
                            "15 LinkedIn/j).",
                    "quand": "Une fois que vous avez approuvé des candidatures préparées.",
                    "prerequis": "Des candidatures au statut « approuvée ». Paramètres → CV, email.",
                    "ou": "📤 Candidatures (passe en « envoyée ») + emails RH",
                },
                {
                    "icon": "📬", "nom": "Suivi Boîte Mail",
                    "fait": "Lit votre Gmail et met à jour automatiquement le statut de vos "
                            "candidatures (accusé de réception, refus, invitation à un entretien).",
                    "quand": "Régulièrement, pour garder vos statuts à jour sans effort.",
                    "prerequis": "Connexion Gmail (Paramètres).",
                    "ou": "📤 Candidatures (statuts mis à jour)",
                },
                {
                    "icon": "📧", "nom": "Follow-up Engine (relances)",
                    "fait": "Envoie des relances polies aux recruteurs à J+7, J+14 et J+21 "
                            "après une candidature restée sans réponse.",
                    "quand": "En continu, pour ne jamais laisser une candidature s'éteindre.",
                    "prerequis": "Des candidatures envoyées avec un email de contact.",
                    "ou": "📧 Relances envoyées + 📦 Livrables",
                },
            ],
        },
        {
            "cat": "🎯 Se préparer & se démarquer",
            "items": [
                {
                    "icon": "🎙️", "nom": "Préparer mon Entretien",
                    "fait": "Crée un guide d'entretien personnalisé : pitch, questions probables, "
                            "réponses suggérées et conseils, basé sur votre CV et l'offre.",
                    "quand": "Dès que vous décrochez un entretien.",
                    "prerequis": "Paramètres → CV.",
                    "ou": "📦 Livrables (guide d'entretien)",
                },
                {
                    "icon": "🤖", "nom": "ATS Optimizer",
                    "fait": "Réécrit votre CV pour passer les filtres automatiques (ATS) : "
                            "bons mots-clés et format lisible par les robots.",
                    "quand": "Si vos candidatures restent sans réponse — souvent un filtre ATS.",
                    "prerequis": "Paramètres → CV.",
                    "ou": "📦 Livrables (CV optimisé)",
                },
                {
                    "icon": "⭐", "nom": "Profil LinkedIn 10/10",
                    "fait": "Analyse experte (niveau RH) de votre profil LinkedIn et propose "
                            "headline, résumé et mots-clés pour viser la note 10/10.",
                    "quand": "Pour rendre votre profil attractif aux recruteurs.",
                    "prerequis": "Paramètres → importez l'export PDF de votre profil LinkedIn.",
                    "ou": "📦 Livrables",
                },
                {
                    "icon": "🧭", "nom": "Stratégie Carrière",
                    "fait": "Construit un plan de carrière personnalisé : objectifs et feuille de "
                            "route. Fonctionne même sans offre précise.",
                    "quand": "Pour prendre du recul et définir votre trajectoire.",
                    "prerequis": "Paramètres → CV (une offre est optionnelle).",
                    "ou": "📦 Livrables",
                },
            ],
        },
        {
            "cat": "🤝 Réseau & présence",
            "items": [
                {
                    "icon": "🤝", "nom": "Networking Agent",
                    "fait": "Trouve des contacts pertinents (recruteurs, hiring managers et "
                            "employés des entreprises où vous avez postulé) et prépare des messages "
                            "LinkedIn. Vous envoyez en 1 clic — aucun risque pour votre compte.",
                    "quand": "Pour développer votre réseau autour de vos candidatures.",
                    "prerequis": "Paramètres → Mots-clés, Ville. Idéalement des candidatures existantes.",
                    "ou": "🤝 Réseau",
                },
                {
                    "icon": "📝", "nom": "Post LinkedIn",
                    "fait": "Génère un post LinkedIn engageant, prêt à coller. Vous le publiez "
                            "vous-même (ou via l'extension Chrome) — vous gardez le contrôle.",
                    "quand": "Pour entretenir votre visibilité auprès des recruteurs.",
                    "prerequis": "Paramètres → ligne éditoriale, langue (optionnel).",
                    "ou": "Texte affiché dans la page (bouton copier)",
                },
            ],
        },
        {
            "cat": "🍁 Installation au Canada",
            "items": [
                {
                    "icon": "🍁", "nom": "Immigration Advisor",
                    "fait": "Rapport complet pour nouveaux arrivants : équivalences de diplômes, "
                            "ordres professionnels, mise en valeur des acquis, CV canadien (ATS) + "
                            "lettre, vie pratique (épiceries, carte santé), et checklist détaillée "
                            "des premiers jours (où aller, documents, rendez-vous).",
                    "quand": "Si vous immigrez ou venez d'arriver au Canada.",
                    "prerequis": "Paramètres → Statut d'immigration, Date d'entrée, Pays d'origine, "
                                 "Province, CV.",
                    "ou": "📦 Livrables + rapport par email (CV et lettre en PDF)",
                },
            ],
        },
    ]

    for groupe in GUIDE:
        st.markdown(f"### {groupe['cat']}")
        for a in groupe["items"]:
            with st.expander(f"{a['icon']}  {a['nom']}"):
                st.markdown(f"**Ce qu'il fait —** {a['fait']}")
                st.markdown(f"**Quand l'utiliser —** {a['quand']}")
                st.markdown(f"**Pré-requis —** {a['prerequis']}")
                st.markdown(
                    f"<div style='margin-top:.5rem;padding:.5rem .8rem;border-radius:8px;"
                    f"background:rgba(45,212,191,0.10);border:1px dashed rgba(45,212,191,0.40);"
                    f"color:#bff0e6;'>📍 <b>Où trouver le résultat :</b> {a['ou']}</div>",
                    unsafe_allow_html=True,
                )
        st.markdown("")

    st.markdown("---")
    st.markdown("### 🚀 Une offre trouvée — comment postuler ?")
    st.markdown(
        "<div style='background:linear-gradient(135deg, rgba(30,155,255,0.10), "
        "rgba(45,212,191,0.08));padding:1.1rem 1.3rem;border-radius:14px;"
        "border:1px solid rgba(45,212,191,0.30);color:#dceefb;'>"
        "Les agents de recherche (Job Hunter, Indeed, <b>Orchestrateur</b>, COOP) "
        "préparent déjà les meilleures offres en <b>candidatures « à valider »</b> "
        "(lettre + CV adapté). Pour postuler :<br><br>"
        "<b>1.</b> Allez dans <b>📤 Candidatures</b> et relisez la lettre + le CV.<br>"
        "<b>2.</b> Cliquez <b>« 🚀 Approuver &amp; Postuler (email auto) »</b> sur celles "
        "qui vous intéressent.<br>"
        "<b>3.</b> Lancez <b>🤖 Agents IA › 🚀 Postuler (Copilote)</b> : il envoie "
        "réellement (email RH + LinkedIn Easy Apply).<br><br>"
        "<span style='color:#2dd4bf;font-weight:600;'>🧭 Recherche → 📤 Candidatures "
        "(Approuver) → 🚀 Postuler (Copilote)</span><br>"
        "<span style='font-size:0.85rem;color:#9fc7e8;'>Les autres offres de "
        "📋 Offres d'Emploi : postulez via leur lien, ou lancez 📝 Préparer "
        "Candidatures pour en générer d'autres.</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("### 🛠️ Bon à savoir")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "**📅 Planificateur** — programmez un agent pour qu'il tourne tout seul "
            "chaque jour à l'heure choisie.\n\n"
            "**💬 Assistant IA** — posez vos questions sur votre recherche d'emploi."
        )
    with c2:
        st.markdown(
            "**🧩 Extension Chrome** — publie vos posts et collecte les contacts "
            "directement depuis votre navigateur LinkedIn connecté (sans risque).\n\n"
            "**📧 Rapports email** — chaque agent vous envoie un compte-rendu détaillé."
        )
    alert(
        "Astuce : plus votre profil dans ⚙️ Paramètres est complet, plus les agents "
        "sont précis et personnalisés. Commencez toujours par là.",
        "info",
    )

# ============================================================
# PAGE: RÉSEAU (networking semi-auto)
# ============================================================

elif page == "🤝 Réseau":
    hero_holographic(
        "🤝 Réseau LinkedIn",
        "Contacts trouvés + messages prêts — vous envoyez en 1 clic (robuste, sans risque)"
    )

    if not st.session_state.user_id:
        alert("Connectez-vous pour voir vos contacts réseau.", "warning")
    else:
        db = get_supabase_client()
        contacts = db.get_contacts_reseau(st.session_state.user_id)
        # Identité RÉELLE de l'utilisateur (messages au bon nom + bon secteur, multi-user)
        _me_net = {}
        try:
            _me_net = db.get_user_by_email(st.session_state.user_email) or {}
        except Exception:
            pass
        _nom_user = _me_net.get("full_name") or _me_net.get("nom_complet") or ""
        _secteur_user = _me_net.get("sector") or "votre secteur"
        # Priorisation : recruteurs/décideurs d'abord, non-contactés d'abord (heuristique)
        contacts = prioriser_contacts(contacts)
        a_faire = [c for c in contacts if (c.get("statut") or "") == "a_contacter"]

        alert("💡 L'agent **Networking** trouve les recruteurs et rédige les messages. "
              "Ici, vous ouvrez le profil, copiez le message, et envoyez **vous-même** "
              "(1 min) — aucun risque de ban, rien ne casse. Les contacts les plus utiles "
              "(recruteurs, décideurs) sont **remontés en haut**.", "info")

        if not contacts:
            empty_state("🤝", "Aucun contact pour l'instant",
                        "Lancez <b>🤝 Networking Agent</b> (page 🤖 Agents IA) : il trouvera des "
                        "recruteurs et préparera vos messages d'approche.")
        else:
            st.caption(f"🤝 {len(contacts)} contact(s) • {len(a_faire)} à contacter")

            # Générer TOUS les messages manquants en 1 clic
            sans_msg = [c for c in contacts if not (c.get("message") or "").strip()]
            if sans_msg:
                if st.button(f"✨ Générer TOUS les messages ({len(sans_msg)} manquants)",
                             type="primary"):
                    barre = st.progress(0.0)
                    for idx, c in enumerate(sans_msg):
                        msg = generer_message_linkedin(
                            c.get("nom", ""), c.get("titre", ""), c.get("entreprise", ""),
                            secteur=_secteur_user, nom_user=_nom_user)
                        db.update_contact_message(c.get("id"), msg)
                        barre.progress((idx + 1) / len(sans_msg))
                    st.success(f"✅ {len(sans_msg)} messages générés !")
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            for c in contacts:
                cid = c.get("id")
                statut = c.get("statut") or "a_contacter"
                icon = "✅" if statut == "contacte" else "📨"
                nom = c.get("nom") or "Contact"
                titre = c.get("titre") or ""
                entreprise = c.get("entreprise") or ""
                url = c.get("profil_url") or ""
                message = c.get("message") or ""
                type_action = c.get("type_action") or "invitation"

                _typ = c.get("_type", "pro")
                _badge = {"recruteur": "🔥 Recruteur", "decideur": "⭐ Décideur",
                          "pair": "🤝 Pair", "pro": "• Pro"}.get(_typ, "• Pro")
                with st.container(border=True):
                    st.markdown(f"### {icon} {nom}  <span style='font-size:13px;opacity:.85'>{_badge}</span>",
                                unsafe_allow_html=True)
                    sub = " • ".join([x for x in [titre, entreprise, c.get('source','')] if x])
                    st.caption(sub)
                    st.markdown(f"**Action :** {'💬 Message' if type_action=='message' else '📨 Invitation'}")

                    if url:
                        st.markdown(f"🔗 [Ouvrir le profil LinkedIn]({url})")

                    if not message:
                        if st.button("✨ Générer un message", key=f"gen_{cid}"):
                            msg = generer_message_linkedin(nom, titre, entreprise,
                                                           secteur=_secteur_user, nom_user=_nom_user)
                            db.update_contact_message(cid, msg)
                            st.rerun()
                    st.text_area("✉️ Message (à envoyer sur LinkedIn)",
                                 value=message, height=110, key=f"msg_{cid}")

                    if message:
                        _safe = json.dumps(message)
                        components.html(
                            f"""
                            <button onclick='navigator.clipboard.writeText({_safe})
                                .then(()=>{{this.innerHTML="✅ Copié !";
                                setTimeout(()=>this.innerHTML="📋 Copier le message",1600);}})'
                                style="background:linear-gradient(135deg,#1e9bff,#2dd4bf);
                                color:#04101f;border:none;padding:9px 16px;border-radius:8px;
                                cursor:pointer;font-size:14px;font-weight:600;width:100%;
                                box-shadow:0 0 14px rgba(45,212,191,0.35);">
                                📋 Copier le message
                            </button>
                            """,
                            height=48,
                        )

                    b1, b2 = st.columns(2)
                    with b1:
                        if statut != "contacte":
                            if st.button("✅ Marquer contacté", key=f"ct_{cid}", type="primary",
                                         use_container_width=True):
                                db.update_contact_reseau(cid, "contacte")
                                st.rerun()
                    with b2:
                        if st.button("🗑️ Retirer", key=f"rm_{cid}", use_container_width=True):
                            db.delete_contact_reseau(cid)
                            st.rerun()

# ============================================================
# PAGE: LIVRABLES (résultats de tous les agents)
# ============================================================

elif page == "📦 Livrables":
    hero_holographic(
        "📦 Livrables",
        "Tous les résultats produits par vos agents"
    )

    if not st.session_state.user_id:
        alert("Connectez-vous pour voir vos livrables.", "warning")
    else:
        db = get_supabase_client()
        livrables = db.get_livrables(st.session_state.user_id, limit=100)

        # Libellés lisibles par type
        TYPE_INFO = {
            "scraping": ("🔍", "Recherche d'offres"),
            "candidature": ("📤", "Candidature"),
            "relance": ("📧", "Relance"),
            "networking": ("🤝", "Networking LinkedIn"),
            "post_linkedin": ("📝", "Post LinkedIn"),
            "immigration": ("🍁", "Conseil immigration"),
            "profil": ("⭐", "Optimisation profil"),
            "cv_ats": ("🤖", "CV optimisé ATS"),
            "strategie": ("🧭", "Stratégie carrière"),
            "entretien": ("🎙️", "Préparation entretien"),
            "suivi_mail": ("📬", "Suivi boîte mail"),
            "autre": ("📦", "Livrable"),
        }

        if not livrables:
            empty_state("📦", "Aucun livrable pour l'instant",
                        "Lancez un agent depuis la page <b>🤖 Agents IA</b> — son résultat "
                        "(CV, lettre, rapport, analyse…) apparaîtra ici.")
        else:
            # Filtre par type
            types_presents = sorted({l.get("type", "autre") for l in livrables})
            sel_type = st.selectbox(
                "Filtrer par type",
                ["Tous"] + [TYPE_INFO.get(t, ("📦", t))[1] for t in types_presents]
            )

            # Classement hiérarchique : les plus récents en premier
            livrables = sorted(livrables, key=lambda l: l.get("created_at") or "", reverse=True)
            st.caption(f"📊 {len(livrables)} livrable(s) • des plus récents aux plus anciens")
            st.markdown("<br>", unsafe_allow_html=True)

            for liv in livrables:
                t = liv.get("type", "autre")
                icon, label = TYPE_INFO.get(t, ("📦", t))
                # Appliquer le filtre
                if sel_type != "Tous" and label != sel_type:
                    continue

                statut = liv.get("statut", "")
                statut_badge = "✅" if statut == "termine" else ("❌" if statut == "echec" else "⏳")
                resume = liv.get("resume") or "(pas de résumé)"
                date = _fmt_dt(liv.get("created_at"))

                with st.container(border=True):
                    st.markdown(f"**{icon} {label}** {statut_badge}")
                    st.caption(f"🤖 {liv.get('agent', '')} • 🕒 {date}")
                    st.markdown(f"{resume}")

                    # Contenu en PLEINE LARGEUR (lisible en grand)
                    contenu = liv.get("contenu_json") or {}
                    guide = contenu.get("guide", "") if isinstance(contenu, dict) else ""
                    output = contenu.get("output", "") if isinstance(contenu, dict) else str(contenu)
                    doc_txt = guide or output          # contenu principal du livrable
                    if t == "entretien" and guide:
                        with st.expander("📖 Lire mon guide d'entretien (plein écran)", expanded=False):
                            st.markdown(guide)
                        # 🎧 Session audio de coaching (synthèse vocale du briefing)
                        if st.button("🎧 Écouter le coaching (audio)", key=f"audio_{liv.get('id')}"):
                            try:
                                from chatbot import _get_client, _synthese_vocale
                                _cli = _get_client()
                                if _cli:
                                    with st.spinner("Génération de la session audio…"):
                                        _scr = _cli.chat.completions.create(
                                            model="gpt-4o", temperature=0.4, max_tokens=320,
                                            messages=[{"role": "user", "content":
                                                "À partir de ce guide d'entretien, rédige un BRIEFING ORAL "
                                                "de coach motivant d'environ 60 secondes (le pitch + 3 "
                                                "conseils clés), à la 2e personne, SANS markdown :\n\n"
                                                + guide[:4000]}],
                                        ).choices[0].message.content
                                        _au = _synthese_vocale(_cli, _scr)
                                    if _au:
                                        st.audio(_au, format="audio/mp3")
                                    else:
                                        st.info("Audio momentanément indisponible.")
                                else:
                                    st.info("Service audio indisponible.")
                            except Exception:
                                st.info("Audio indisponible pour le moment.")
                    else:
                        with st.expander("Détail"):
                            st.code(output[-2000:] or "(vide)")

                    # Téléchargement : PDF (+ markdown pour le guide d'entretien)
                    if doc_txt.strip():
                        date10 = (liv.get("created_at") or "")[:10]
                        cols_dl = st.columns(2 if (t == "entretien" and guide) else 1)
                        with cols_dl[0]:
                            st.download_button(
                                "📥 Télécharger en PDF",
                                data=texte_vers_pdf(doc_txt, label),
                                file_name=f"{_nom_fichier(label)}_{date10}.pdf",
                                mime="application/pdf",
                                key=f"dlpdf_{liv.get('id')}",
                                use_container_width=True,
                            )
                        if t == "entretien" and guide:
                            with cols_dl[1]:
                                st.download_button(
                                    "📥 Markdown (.md)",
                                    data=guide,
                                    file_name=f"guide_entretien_{date10}.md",
                                    mime="text/markdown",
                                    key=f"dl_{liv.get('id')}",
                                    use_container_width=True,
                                )

# ============================================================
# PAGE: PLANIFICATEUR
# ============================================================

elif page == "📅 Planificateur":
    hero_holographic(
        "📅 Planificateur",
        "Lancez vos agents automatiquement à heures fixes"
    )

    # Agents planifiables (nom → action_type = fichier .py)
    schedulable = {
        "Job Hunter": "job_hunter",
        "Indeed Agent": "indeed_agent",
        "COOP Hunter": "coop_hunter",
        "Orchestrateur": "chercheur_offres",
        "Networking Agent": "networking_agent",
        "Follow-up Engine": "followup_engine",
        "Préparer Candidatures": "candidature_prep",
        "Préparer mon Entretien": "entretien_prep",
        "Suivi Boîte Mail": "mail_tracker",
        "Postuler (Copilote)": "candidature_send",
        "Immigration Advisor": "immigration_advisor",
        "Post LinkedIn": "linkedin_agent",
        "Publier LinkedIn (auto)": "publish_linkedin",
        "Profil LinkedIn 10/10": "profile_optimizer",
        "ATS Optimizer": "ats_optimizer",
        "Stratégie Carrière": "career_strategy_agent",
    }
    type_to_name = {v: k for k, v in schedulable.items()}

    if not st.session_state.user_id:
        alert("Connectez-vous pour gérer vos planifications.", "warning")
    else:
        db = get_supabase_client()

        alert("⚠️ Le worker (simple_worker.py) doit tourner sur votre PC pour "
              "que les agents planifiés se lancent.", "info")

        # Jours de la semaine (Python weekday: Lun=0 ... Dim=6)
        JOURS = [("Lun", 0), ("Mar", 1), ("Mer", 2), ("Jeu", 3), ("Ven", 4), ("Sam", 5), ("Dim", 6)]
        JOURS_NOMS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

        def format_jours(days_str):
            if not days_str:
                return "tous les jours"
            idxs = sorted(int(x) for x in str(days_str).split(",") if x.strip().isdigit())
            if idxs == [0, 1, 2, 3, 4, 5, 6]:
                return "tous les jours"
            if idxs == [0, 1, 2, 3, 4]:
                return "Lun→Ven"
            if idxs == [5, 6]:
                return "week-end"
            return ", ".join(JOURS_NOMS[i] for i in idxs if 0 <= i < 7)

        # --- Formulaire d'ajout ---
        section_header("➕ Nouvelle planification", "")
        c1, c2, c3 = st.columns([4, 2, 2])
        with c1:
            sel_agent = st.selectbox("Agent", list(schedulable.keys()), key="sched_agent")
        with c2:
            heures = [f"{h:02d}" for h in range(24)]
            sel_heure = st.selectbox("Heure", heures, index=8, key="sched_heure")
        with c3:
            minutes = [f"{m:02d}" for m in range(0, 60, 5)]
            sel_minute = st.selectbox("Minutes", minutes, index=0, key="sched_minute")

        sel_jours = st.multiselect(
            "Jours d'exécution",
            JOURS_NOMS,
            default=JOURS_NOMS,  # tous les jours par défaut
            key="sched_jours"
        )

        if st.button("➕ Ajouter", type="primary"):
            run_time = f"{sel_heure}:{sel_minute}"
            jours_idx = sorted(str(dict(JOURS)[j]) for j in sel_jours)
            if not jours_idx:
                st.error("Choisissez au moins un jour.")
            elif db.create_schedule(st.session_state.user_id,
                                    schedulable[sel_agent], run_time, ",".join(jours_idx)):
                st.success(f"✅ {sel_agent} planifié à {run_time} ({format_jours(','.join(jours_idx))})")
                st.rerun()
            else:
                st.error("Erreur lors de la création.")

        st.markdown("---")

        # --- Liste des planifications ---
        section_header("🗓️ Mes planifications", "")
        schedules = db.get_schedules(st.session_state.user_id)

        if not schedules:
            empty_state("📅", "Aucune planification",
                        "Ajoutez‑en une ci‑dessus pour lancer vos agents automatiquement "
                        "(ex. tous les matins à 9h).")
        else:
            for s in schedules:
                sid = s.get("id")
                agent_name = type_to_name.get(s.get("agent_type"), s.get("agent_type"))
                run_time = s.get("run_time", "")[:5]
                enabled = bool(s.get("enabled"))
                last = s.get("last_run_date") or "jamais"
                statut = "🟢 Actif" if enabled else "⏸️ En pause"

                with st.container(border=True):
                    # Infos en pleine largeur (lisible sur mobile)
                    st.markdown(f"**🤖 {agent_name}** — 🕐 **{run_time}** • {format_jours(s.get('days'))}")
                    st.caption(f"{statut} • Dernier lancement: {last}")
                    # Boutons sur une rangée de 2
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if enabled:
                            if st.button("⏸️ Pause", key=f"pause_{sid}", use_container_width=True):
                                db.toggle_schedule(sid, False)
                                st.rerun()
                        else:
                            if st.button("▶️ Activer", key=f"on_{sid}", use_container_width=True):
                                db.toggle_schedule(sid, True)
                                st.rerun()
                    with bc2:
                        if st.button("🗑️ Suppr.", key=f"del_{sid}", use_container_width=True):
                            db.delete_schedule(sid)
                            st.rerun()

# ============================================================
# PAGE: ASSISTANT IA
# ============================================================

elif page == "💬 Assistant IA":
    hero_holographic(
        "💬 Assistant IA",
        "Votre coach personnel pour la recherche d'emploi"
    )
    chatbot_page()

# ============================================================
# PAGE: PARAMÈTRES
# ============================================================

elif page == "⚙️ Paramètres":
    hero_holographic(
        "⚙️ Paramètres",
        "Configurez votre profil et vos préférences"
    )

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
        ["👤 Profil", "🔑 Keywords", "📄 Mon CV", "🔔 Notifications", "🔒 Mot de passe",
         "🔗 LinkedIn", "🎨 Post LinkedIn", "🧩 Extension", "📝 Easy Apply"])

    # Charger le VRAI profil de l'utilisateur connecté (personnalisé)
    db = get_supabase_client()
    _me = db.get_user_by_email(st.session_state.user_email) or {}

    with tab1:
        st.subheader("Informations Personnelles")

        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom complet", _me.get("full_name") or _me.get("nom_complet") or "")
            email = st.text_input("Email", _me.get("email") or st.session_state.user_email,
                                  disabled=True)
            telephone = st.text_input("Téléphone", _me.get("telephone") or "")

        with col2:
            ville = st.text_input("Ville", _me.get("ville") or "")
            province = st.text_input("Province", _me.get("province") or "")
            linkedin = st.text_input("LinkedIn URL", _me.get("linkedin_url") or "")

        secteur_profil = st.text_input(
            "Métier / secteur (sert aux posts LinkedIn et à l'IA)",
            value=_me.get("sector") or "",
            placeholder="ex : infirmière, génie civil, marketing digital, comptabilité…")

        st.markdown("---")
        st.markdown("### 🎓 Profil étudiant (pour COOP Hunter)")
        st.caption("Renseignez ces champs si vous cherchez un stage COOP — ils orientent "
                   "l'agent vers les bons programmes et employeurs.")
        ec1, ec2 = st.columns(2)
        with ec1:
            ecole = st.text_input("École / Établissement", _me.get("ecole") or "",
                                  placeholder="ex : Collège La Cité, Université d'Ottawa")
            programme = st.text_input("Titre du programme d'études", _me.get("programme_etudes") or "",
                                      placeholder="ex : DEC Techniques de l'informatique")
        with ec2:
            session_coop = st.text_input("Session COOP visée (optionnel)", _me.get("session_coop") or "",
                                         placeholder="ex : Été 2026, Automne 2026")
        parcours = st.text_area("Parcours scolaire (établissements, diplômes, années)",
                                _me.get("parcours_scolaire") or "", height=90,
                                placeholder="ex : DEC en informatique (2024-2026), DES (2024)…")

        st.caption("🎯 **Zone où vous cherchez (stage ou emploi)** — laissez vide = votre ville "
                   "de résidence. COOP Hunter, Job Hunter et Chercheur d'offres cibleront cette zone.")
        zc1, zc2, zc3 = st.columns(3)
        with zc1:
            coop_zone_ville = st.text_input("Ville visée", _me.get("coop_zone_ville") or "",
                                            placeholder="ex : Toronto")
        with zc2:
            coop_zone_province = st.text_input("Province / État visé", _me.get("coop_zone_province") or "",
                                               placeholder="ex : Ontario")
        with zc3:
            coop_zone_pays = st.text_input("Pays visé", _me.get("coop_zone_pays") or "",
                                           placeholder="ex : Canada")

        st.markdown("---")
        st.markdown("### 🍁 Profil immigration (pour Immigration Advisor)")
        st.caption("Renseignez ces champs pour un rapport d'immigration personnalisé "
                   "(programmes, démarches et conseils adaptés à VOTRE situation).")
        STATUTS_CA = [
            "Nouvel arrivant", "Résident permanent (RP)", "Permis de travail",
            "Permis d'études (étudiant)", "Réfugié / demandeur d'asile",
            "Citoyen canadien", "Autre",
        ]
        _cur_statut = (_me.get("statut_immigration") or "").strip()
        _opts = STATUTS_CA if (not _cur_statut or _cur_statut in STATUTS_CA) else [_cur_statut] + STATUTS_CA
        im1, im2, im3 = st.columns(3)
        with im1:
            pays_origine = st.text_input("Pays d'origine", _me.get("pays_origine") or "",
                                         placeholder="ex : Cameroun, France, Inde…")
        with im2:
            statut_immig = st.selectbox(
                "Statut au Canada",
                _opts,
                index=(_opts.index(_cur_statut) if _cur_statut in _opts else 0))
        with im3:
            annee_arrivee = st.text_input("Date d'entrée au Canada", _me.get("annee_arrivee") or "",
                                          placeholder="ex : 2024 ou 03/2024")

        if st.button("💾 Sauvegarder le Profil", type="primary"):
            ok = db.update_user(st.session_state.user_id, {
                "full_name": nom, "nom_complet": nom, "telephone": telephone,
                "ville": ville, "province": province, "linkedin_url": linkedin,
                "sector": secteur_profil,
                "ecole": ecole, "programme_etudes": programme,
                "parcours_scolaire": parcours, "session_coop": session_coop,
                "coop_zone_ville": coop_zone_ville, "coop_zone_province": coop_zone_province,
                "coop_zone_pays": coop_zone_pays,
                "pays_origine": pays_origine, "statut_immigration": statut_immig,
                "annee_arrivee": annee_arrivee,
            })
            st.success("✅ Profil sauvegardé!") if ok else st.error("Erreur de sauvegarde.")

    with tab2:
        st.subheader("Mots-clés de Recherche")
        st.caption("Les agents de recherche d'emploi utilisent VOS mots-clés (un par ligne).")

        keywords = st.text_area(
            "Keywords (un par ligne)",
            value=_me.get("keywords") or "",
            height=200, placeholder="CHARGE DE PROJET CONSTRUCTION\nESTIMATEUR JUNIOR\n...",
        )

        if st.button("💾 Sauvegarder les Keywords", type="primary"):
            ok = db.update_user(st.session_state.user_id, {"keywords": keywords.strip()})
            st.success("✅ Keywords sauvegardés!") if ok else st.error("Erreur de sauvegarde.")

    with tab3:
        st.subheader("📄 Mon CV")
        st.caption("Votre CV sert aux agents (lettres, candidatures, entretien). Personnel à votre compte.")

        _cv_actuel = _me.get("cv_text") or ""
        _cv_nom = _me.get("cv_filename") or ""
        if _cv_actuel:
            st.success(f"✅ CV enregistré : {_cv_nom or 'CV'} ({len(_cv_actuel)} caractères)")
        else:
            st.warning("❌ Aucun CV enregistré.")

        up = st.file_uploader("Téléverser votre CV (PDF)", type=["pdf"], key="cv_pdf")
        if up is not None:
            try:
                from pypdf import PdfReader
                import io as _io
                reader = PdfReader(_io.BytesIO(up.read()))
                texte = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
                if texte:
                    st.text_area("Aperçu du texte extrait", value=texte[:1500], height=160,
                                 disabled=True)
                    if st.button("💾 Enregistrer ce CV", type="primary", key="save_cv_pdf"):
                        ok = db.update_user(st.session_state.user_id,
                                            {"cv_text": texte, "cv_filename": up.name})
                        st.success("✅ CV enregistré!") if ok else st.error("Erreur de sauvegarde.")
                else:
                    st.error("Impossible d'extraire le texte (PDF scanné ?). Collez-le ci-dessous.")
            except Exception as e:
                st.error(f"Erreur lecture PDF : {e}")

        st.markdown("**Ou collez le texte de votre CV :**")
        cv_txt = st.text_area("Texte du CV", value=_cv_actuel, height=220, key="cv_texte")
        if st.button("💾 Enregistrer le CV (texte)", key="save_cv_txt"):
            ok = db.update_user(st.session_state.user_id,
                                {"cv_text": cv_txt.strip(), "cv_filename": _cv_nom or "CV.txt"})
            st.success("✅ CV enregistré!") if ok else st.error("Erreur de sauvegarde.")

    with tab4:
        st.subheader("📧 Gmail d'envoi (Copilote — postuler par email)")
        st.markdown("""
Le **Copilote** envoie vos candidatures (lettre + CV) **depuis VOTRE Gmail**, pour que les
**réponses arrivent dans VOTRE boîte**. Il faut donc votre adresse Gmail + un **mot de passe
d'application** (Google l'exige pour les apps tierces — votre mot de passe habituel ne marche pas).

**Créer un mot de passe d'application (2 min) :**
1. Activez la **validation en 2 étapes** : https://myaccount.google.com/security
2. Ouvrez **https://myaccount.google.com/apppasswords**
3. Créez un mot de passe (nom : « GetJobAI ») → Google affiche **16 lettres**
4. Collez ces 16 lettres ci-dessous (les espaces seront retirés automatiquement)
""")
        _g_addr = st.text_input("Votre adresse Gmail", value=_me.get("gmail_address") or "",
                                placeholder="prenom.nom@gmail.com", key="cfg_gmail_addr")
        _has_pwd = bool((_me.get("gmail_password") or "").strip())
        _g_pwd = st.text_input(
            "Mot de passe d'application (16 lettres)", type="password",
            placeholder="●●●● déjà enregistré ●●●●" if _has_pwd else "abcd efgh ijkl mnop",
            key="cfg_gmail_pwd")
        st.caption("✅ Mot de passe déjà enregistré (laissez vide pour le garder)." if _has_pwd
                   else "❌ Aucun mot de passe — le Copilote ne peut pas encore envoyer d'email.")
        if st.button("💾 Enregistrer mon Gmail d'envoi", type="primary", key="save_gmail"):
            if not _g_addr.strip():
                st.error("Entrez votre adresse Gmail.")
            elif not _has_pwd and not _g_pwd.strip():
                st.error("Entrez le mot de passe d'application (16 lettres).")
            else:
                _patch = {"gmail_address": _g_addr.strip()}
                if _g_pwd.strip():
                    _pwd_clean = _g_pwd.replace(" ", "").strip()
                    try:
                        from linkedin_oauth import enc_token
                        _pwd_clean = enc_token(_pwd_clean)  # chiffré au repos (enc:...)
                    except Exception:
                        pass
                    _patch["gmail_password"] = _pwd_clean
                if db.update_user(st.session_state.user_id, _patch):
                    st.success("✅ Gmail d'envoi enregistré ! Le Copilote peut maintenant postuler par email.")
                else:
                    st.error("Erreur d'enregistrement.")
        st.markdown("---")
        st.caption("🔔 Vous recevez aussi un rapport par email après chaque agent (automatique).")

    with tab5:
        st.subheader("Changer mon mot de passe")
        new_pwd = st.text_input("Nouveau mot de passe (min. 6 caractères)", type="password", key="param_new_pwd")
        new_pwd2 = st.text_input("Confirmer le nouveau mot de passe", type="password", key="param_new_pwd2")
        if st.button("🔒 Changer le mot de passe", type="primary"):
            if len(new_pwd) < 6:
                st.error("Le mot de passe doit faire au moins 6 caractères.")
            elif new_pwd != new_pwd2:
                st.error("Les mots de passe ne correspondent pas.")
            elif set_password(st.session_state.user_id, new_pwd):
                st.success("✅ Mot de passe changé avec succès!")
            else:
                st.error("Erreur lors du changement de mot de passe.")

    with tab6:
        # --- Publication automatique : connexion officielle LinkedIn (OAuth, 1 clic) ---
        st.subheader("🔗 Publier sur LinkedIn — connexion officielle (1 clic)")
        st.markdown("""
**Pour publier vos posts automatiquement** (y compris les **posts planifiés**), connectez
votre compte LinkedIn **une seule fois** avec le bouton officiel ci-dessous. Aucune
extension, aucun cookie à manipuler.

**La méthode (30 secondes) :**
1. Cliquez **« 🔗 Connecter LinkedIn »** ci-dessous.
2. Sur la page LinkedIn, cliquez **« Autoriser »**.
3. Vous revenez ici et le message **« ✅ LinkedIn connecté »** s'affiche. C'est tout !

> 🔒 Votre jeton d'accès est **chiffré** et rangé dans **votre compte uniquement**.
> À refaire seulement si un message indique que la connexion a expiré.
> ⚠️ Sur la page de retour, ne rechargez pas l'adresse qui contient `?code=…`.
""")
        if st.session_state.user_id:
            try:
                import linkedin_oauth as _lio_p
                _dbp = get_supabase_client()
                _lip = _lio_p.get_status(_dbp, st.session_state.user_id)
                if _lio_p.is_configured():
                    _aup = _lio_p.build_authorize_url(st.session_state.user_id)
                    if _lip.get("connected"):
                        st.success("✅ LinkedIn connecté — publication automatique disponible.")
                        st.link_button("🔄 Reconnecter LinkedIn (si la connexion a expiré)",
                                       _aup, use_container_width=True)
                    else:
                        st.warning("❌ LinkedIn non connecté. Connectez-le une fois pour "
                                   "publier automatiquement.")
                        st.link_button("🔗 Connecter LinkedIn", _aup, use_container_width=True)
                else:
                    st.info("ℹ️ La connexion LinkedIn n'est pas encore configurée par l'administrateur.")
            except Exception as _e_lp:
                st.caption(f"LinkedIn momentanément indisponible : {str(_e_lp)[:80]}")

        st.markdown("---")
        st.subheader("🔗 Connexion LinkedIn (pour Networking & Easy Apply)")
        st.markdown("""
**Pourquoi ?** Pour que l'agent **Networking** (recherche de recruteurs) et le **LinkedIn
Easy Apply** fonctionnent, il faut votre session LinkedIn complète. Le cookie `li_at` seul
ne suffit pas pour la recherche (LinkedIn bloque).

**Comment faire (2 min) :**
1. Installez l'extension **Cookie-Editor** : https://cookie-editor.com/
2. Allez sur **linkedin.com** (connecté à votre compte)
3. Cliquez l'icône **Cookie-Editor** → bouton **Export** (en haut à droite) → **Export as JSON**
4. Collez le bloc JSON ci-dessous, puis **Enregistrer**

⚠️ Ces cookies donnent accès à votre LinkedIn — ils sont stockés **dans votre compte uniquement**.
""")
        if st.session_state.user_id:
            db = get_supabase_client()
            cur = db.get_user_settings(st.session_state.user_id)
            deja = bool(cur.get("linkedin_cookie"))
            st.caption("✅ Cookies LinkedIn déjà enregistrés" if deja
                       else "❌ Aucun cookie LinkedIn enregistré pour l'instant")

            cookies_txt = st.text_area(
                "Cookies LinkedIn (JSON exporté via Cookie-Editor)",
                placeholder='[{"name":"li_at","value":"...","domain":".linkedin.com",...}, ...]',
                height=160, key="li_cookies")
            if st.button("💾 Enregistrer mes cookies LinkedIn", type="primary"):
                import json as _json
                try:
                    data = _json.loads(cookies_txt)
                    if not isinstance(data, list) or not data:
                        raise ValueError("format")
                    # Extraire li_at au passage (pour Easy Apply)
                    li_at = next((c.get("value") for c in data
                                  if c.get("name") == "li_at"), "")
                    try:
                        from linkedin_oauth import enc_token
                    except Exception:
                        enc_token = lambda s: s
                    ok = db.save_setting(st.session_state.user_id, "linkedin_cookie", enc_token(cookies_txt.strip()))
                    if li_at:
                        db.save_setting(st.session_state.user_id, "linkedin_cookie_li_at", enc_token(li_at))
                    if ok:
                        st.success(f"✅ {len(data)} cookies enregistrés ! "
                                   "L'agent Networking peut maintenant fonctionner.")
                    else:
                        st.error("Erreur d'enregistrement.")
                except Exception:
                    st.error("❌ JSON invalide. Collez bien l'export complet (commence par `[` ).")

            st.markdown("---")
            st.markdown("### 📄 Votre profil LinkedIn (pour l'analyse 10/10 approfondie)")
            st.caption("Exportez votre profil : LinkedIn → votre profil → bouton **Ressources** "
                       "(ou **More/Plus**) → **Enregistrer au format PDF**. Importez ce PDF ici "
                       "(ou collez le texte). L'agent **Profil LinkedIn 10/10** l'analysera en "
                       "profondeur avec l'œil d'un expert RH.")
            st.caption("✅ Profil LinkedIn déjà importé" if (_me.get("linkedin_profile") or "").strip()
                       else "❌ Aucun profil importé pour l'instant")
            up_li = st.file_uploader("Importer le PDF de votre profil LinkedIn", type=["pdf"], key="li_pdf")
            li_paste = st.text_area("…ou collez le texte de votre profil LinkedIn", height=140, key="li_txt")
            if st.button("💾 Enregistrer mon profil LinkedIn", key="save_li_profile"):
                texte = (li_paste or "").strip()
                if up_li is not None and not texte:
                    try:
                        import io
                        from pypdf import PdfReader
                        reader = PdfReader(io.BytesIO(up_li.read()))
                        texte = "\n".join((p.extract_text() or "") for p in reader.pages).strip()
                    except Exception as e:
                        st.error(f"Lecture du PDF impossible : {e}")
                if texte:
                    ok = db.update_user(st.session_state.user_id, {"linkedin_profile": texte[:12000]})
                    if ok:
                        st.success(f"✅ Profil LinkedIn enregistré ({len(texte)} car) — "
                                   "l'agent Profil 10/10 fera une analyse approfondie.")
                    else:
                        st.error("Erreur d'enregistrement.")
                else:
                    st.warning("Importez un PDF ou collez le texte de votre profil LinkedIn.")

    with tab7:
        st.subheader("🎨 Préférences des posts LinkedIn")
        st.caption("Ces réglages personnalisent le texte ET l'image générée (apparence, ton, langue).")
        if st.session_state.user_id:
            db = get_supabase_client()
            cur = db.get_user_settings(st.session_state.user_id) or {}

            _GENRES = ["Homme", "Femme", "Autre / ne pas préciser"]
            _PEAUX = ["Noire", "Métisse", "Brune / olive", "Blanche", "Ne pas préciser"]
            _EDITOS = ["Conseil pratique", "Question / débat", "Récit d'expérience",
                       "Analyse / réflexion", "Coulisses du métier", "Motivation / mindset"]
            _LANGUES = ["Français", "Anglais", "Bilingue (FR + EN)"]

            colA, colB = st.columns(2)
            with colA:
                genre = st.selectbox("Sexe (pour l'image)", _GENRES,
                                     index=_GENRES.index(cur.get("post_genre")) if cur.get("post_genre") in _GENRES else 0)
                peau = st.selectbox("Couleur de peau (pour l'image)", _PEAUX,
                                    index=_PEAUX.index(cur.get("post_peau")) if cur.get("post_peau") in _PEAUX else 0)
                langue_post = st.selectbox("Langue du post", _LANGUES,
                                           index=_LANGUES.index(cur.get("post_langue")) if cur.get("post_langue") in _LANGUES else 0)
            with colB:
                edito1 = st.selectbox("Ligne éditoriale principale", _EDITOS,
                                      index=_EDITOS.index(cur.get("post_edito1")) if cur.get("post_edito1") in _EDITOS else 0)
                edito2 = st.selectbox("Ligne éditoriale secondaire (variété)",
                                      ["(aucune)"] + _EDITOS,
                                      index=(["(aucune)"] + _EDITOS).index(cur.get("post_edito2"))
                                      if cur.get("post_edito2") in (["(aucune)"] + _EDITOS) else 0)

            tag_perso = st.text_input(
                "Personne à taguer dans VOS posts (optionnel — vous choisissez qui)",
                value=cur.get("post_tag") or "",
                placeholder="ex : Jean Dupont — laissez vide pour ne taguer personne")

            st.markdown("**🧑 Photo de profil** (pour les posts qui vous mettent en avant — "
                        "l'image générée vous ressemblera)")
            if cur.get("photo_b64"):
                try:
                    st.image(base64.b64decode(cur["photo_b64"]), width=120,
                             caption="Photo enregistrée")
                except Exception:
                    pass
            photo_up = st.file_uploader("Téléverser une photo (portrait net, visage visible)",
                                        type=["jpg", "jpeg", "png"], key="pf_photo")
            if photo_up is not None:
                _pb64 = base64.b64encode(photo_up.read()).decode()
                if st.button("💾 Enregistrer ma photo", key="save_photo"):
                    if db.update_user(st.session_state.user_id, {"photo_b64": _pb64}):
                        st.success("✅ Photo enregistrée !")
                    else:
                        st.error("Erreur — colonne photo_b64 créée ? (voir SQL)")

            if st.button("💾 Sauvegarder mes préférences de post", type="primary"):
                ok = db.update_user(st.session_state.user_id, {
                    "post_genre": genre, "post_peau": peau, "post_langue": langue_post,
                    "post_edito1": edito1, "post_edito2": edito2, "post_tag": tag_perso.strip(),
                })
                if ok:
                    st.success("✅ Préférences enregistrées ! Elles s'appliquent aux prochains posts.")
                else:
                    st.error("Erreur — avez-vous lancé le SQL d'ajout des colonnes post_* ? (voir guide)")
        else:
            st.warning("Connectez-vous pour configurer vos préférences.")

    with tab8:
        st.subheader("🧩 Extension GetJobAI pour Chrome")
        st.caption("Collectez des recruteurs ET publiez vos posts LinkedIn depuis votre vrai "
                   "navigateur — aucune détection, votre session reste intacte.")

        # Lien store (à renseigner une fois l'extension approuvée par Google)
        STORE_URL = ""  # ex: https://chrome.google.com/webstore/detail/xxxx
        if STORE_URL:
            st.success("✅ Installez l'extension en 1 clic :")
            st.markdown(f"### 👉 [Installer l'extension GetJobAI]({STORE_URL})")
        else:
            st.info("⏳ L'extension est **en cours de validation** sur le Chrome Web Store. "
                    "En attendant, installez-la en mode développeur (ci-dessous).")

        st.markdown("---")
        st.markdown("#### 📥 Installation (mode développeur, en attendant le store)")
        st.markdown("""
1. Ouvrez **`chrome://extensions`**
2. En haut à droite, activez **« Mode développeur »**
3. Cliquez **« Charger l'extension non empaquetée »**
4. Sélectionnez le dossier de l'extension (fourni par GetJobAI)
""")

        st.markdown("#### ⚙️ Configuration (1 fois)")
        st.markdown(f"""
1. Cliquez l'icône **🧩 GetJobAI** dans la barre d'extensions
2. Entrez **votre email GetJobAI** : `{st.session_state.user_email}`
3. Cliquez **💾 Enregistrer**
""")

        st.markdown("#### 🎯 Utilisation")
        st.markdown("""
**Collecter des recruteurs** : sur une recherche LinkedIn → bouton **📥 Collecter** → ils
arrivent dans 🤝 Réseau.

**Publier un post** : ici → **Agents IA → Post LinkedIn → Générer → Envoyer à l'extension** →
sur **linkedin.com/feed** → bouton **📤 Publier (GetJobAI)** → vérifiez → **Publier**.
""")
        st.success("🛡️ Robuste : ça tourne dans VOTRE navigateur connecté → LinkedIn voit une "
                   "session normale, jamais de blocage.")

    with tab9:
        st.subheader("📝 Easy Apply — réponses pré-remplies")
        st.caption("Renseignez vos réponses aux questions classiques d'Easy Apply LinkedIn. "
                   "Sur une offre LinkedIn, l'extension remplira le formulaire à votre place — "
                   "vous n'avez qu'à vérifier et cliquer « Soumettre ».")
        c1, c2 = st.columns(2)
        with c1:
            ea_tel = st.text_input("Téléphone", _me.get("telephone") or "", key="ea_tel")
            ea_exp = st.text_input("Années d'expérience", _me.get("ea_experience") or "",
                                   key="ea_exp", placeholder="ex : 8")
            ea_sal = st.text_input("Prétentions salariales (annuel)", _me.get("ea_salaire") or "",
                                   key="ea_sal", placeholder="ex : 70000")
        with c2:
            ea_auth = st.selectbox("Autorisé(e) à travailler au Canada ?", ["Oui", "Non"],
                                   index=0 if (_me.get("ea_autorise") or "Oui") == "Oui" else 1,
                                   key="ea_auth")
            ea_spons = st.selectbox("Avez-vous besoin d'un parrainage (visa) ?", ["Non", "Oui"],
                                    index=0 if (_me.get("ea_sponsorship") or "Non") == "Non" else 1,
                                    key="ea_spons")
            ea_preavis = st.text_input("Préavis / disponibilité", _me.get("ea_preavis") or "",
                                       key="ea_preavis", placeholder="ex : Immédiate / 2 semaines")
        if st.button("💾 Enregistrer mes réponses Easy Apply", key="save_ea", type="primary"):
            ok = db.update_user(st.session_state.user_id, {
                "telephone": ea_tel.strip(),
                "ea_experience": ea_exp.strip(),
                "ea_salaire": ea_sal.strip(),
                "ea_autorise": ea_auth,
                "ea_sponsorship": ea_spons,
                "ea_preavis": ea_preavis.strip(),
            })
            if ok:
                st.success("✅ Réponses enregistrées ! L'extension les utilisera sur LinkedIn.")
            else:
                st.error("❌ Échec (les colonnes ea_* sont-elles créées ? voir le SQL fourni).")
        st.info("ℹ️ **Comment ça marche** : sur une offre LinkedIn, cliquez le bouton orange "
                "**📝 Postuler auto (GetJobAI)** de l'extension → il **ouvre Easy Apply, remplit "
                "et soumet automatiquement** avec vos réponses. Il **s'arrête** si une question "
                "inhabituelle requiert votre réponse (vous la complétez puis soumettez).")

# ============================================================
# PAGE: ADMIN
# ============================================================

elif page == "👑 Admin":
    hero_holographic(
        "👑 Administration",
        "Gestion des utilisateurs GetJobAI"
    )

    # Sécurité: double-vérification du statut admin
    if not st.session_state.get("is_admin"):
        alert("⛔ Accès réservé aux administrateurs.", "danger")
    else:
        try:
            db = get_supabase_client()
            users = db.get_all_users()

            # Stats globales
            total_users = len(users)
            approuves = sum(1 for u in users if u.get("is_whitelisted"))
            en_attente = sum(1 for u in users if not u.get("is_whitelisted"))
            admins = sum(1 for u in users if u.get("is_admin"))

            stats_grid([
                {"label": "Utilisateurs", "value": str(total_users), "icon": "👥"},
                {"label": "Approuvés", "value": str(approuves), "icon": "✅"},
                {"label": "En attente", "value": str(en_attente), "icon": "⏳"},
                {"label": "Admins", "value": str(admins), "icon": "👑"},
            ])

            st.markdown("<br>", unsafe_allow_html=True)

            # Bandeau impersonation
            real_admin = st.session_state.get("real_admin_email")
            if real_admin and st.session_state.user_email != real_admin:
                alert(f"🎭 Vous consultez le compte de **{st.session_state.user_email}**. "
                      f"Vous êtes connecté en tant que {real_admin}.", "warning")
                if st.button("↩️ Revenir à mon compte admin", type="primary"):
                    st.session_state.user_email = real_admin
                    st.session_state.user_id = None  # force le rechargement
                    st.rerun()
                st.markdown("<br>", unsafe_allow_html=True)

            section_header("📋 Liste des utilisateurs", "")

            for u in users:
                uid = u.get("id", "")
                email = u.get("email", "?")
                nom = u.get("full_name") or u.get("nom_complet") or "—"
                ville = u.get("ville") or u.get("province") or ""
                nb_offres = db.count_jobs(uid)
                is_approved = bool(u.get("is_whitelisted"))
                badge_admin = " 👑" if u.get("is_admin") else ""
                badge_actif = "🟢" if u.get("is_active") else "🔴"
                badge_appr = "✅ Approuvé" if is_approved else "⏳ En attente"

                with st.container(border=True):
                    # Infos sur 2 colonnes (reflux propre sur mobile)
                    ci1, ci2 = st.columns([3, 2])
                    with ci1:
                        st.markdown(f"**{badge_actif} {nom}{badge_admin}**")
                        st.caption(f"✉️ {email}")
                        st.caption(badge_appr)
                    with ci2:
                        st.markdown(f"📊 **{nb_offres}** offres")
                        if ville:
                            st.caption(f"📍 {ville}")

                    # Actions sur une rangée pleine largeur (3 boutons)
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        # Approuver / Révoquer (sauf pour les admins, toujours approuvés)
                        if not u.get("is_admin"):
                            if is_approved:
                                if st.button("🚫 Révoquer", key=f"revoke_{uid}", use_container_width=True):
                                    if db.update_user_status(uid, "is_whitelisted", False):
                                        st.success(f"{email} révoqué")
                                        st.rerun()
                            else:
                                if st.button("✅ Approuver", key=f"approve_{uid}", type="primary", use_container_width=True):
                                    if db.update_user_status(uid, "is_whitelisted", True):
                                        st.success(f"{email} approuvé")
                                        st.rerun()
                    with ac2:
                        # Consulter ce compte (sauf le sien)
                        if email != st.session_state.user_email:
                            if st.button("👁️ Voir", key=f"view_{uid}", use_container_width=True):
                                st.session_state.user_email = email
                                st.session_state.user_id = None  # force rechargement
                                st.rerun()
                    with ac3:
                        # Supprimer (sauf admin et soi-même) — déclenche la confirmation
                        if not u.get("is_admin") and email != st.session_state.user_email:
                            if not st.session_state.get(f"confirm_del_{uid}"):
                                if st.button("🗑️ Supprimer", key=f"del_{uid}", use_container_width=True):
                                    st.session_state[f"confirm_del_{uid}"] = True
                                    st.rerun()

                    # Confirmation de suppression — pleine largeur
                    if (not u.get("is_admin") and email != st.session_state.user_email
                            and st.session_state.get(f"confirm_del_{uid}")):
                        st.warning("⚠️ Supprimer définitivement ce compte ET ses données ?")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("✅ Oui, supprimer", key=f"cfm_{uid}", use_container_width=True):
                                if db.delete_user(uid):
                                    st.success(f"{email} supprimé")
                                st.session_state[f"confirm_del_{uid}"] = False
                                st.rerun()
                        with cc2:
                            if st.button("Annuler", key=f"cancel_{uid}", use_container_width=True):
                                st.session_state[f"confirm_del_{uid}"] = False
                                st.rerun()

        except Exception as e:
            st.error(f"Erreur page admin: {e}")

# ============================================================
# FOOTER
# ============================================================

st.markdown("---")
st.markdown(
    f"""
    <div style='
        text-align: center;
        color: {COLOR_SCHEMES['getjobai']['primary']};
        padding: 2rem 1rem;
        background: {COLOR_SCHEMES['getjobai']['light']};
        border-radius: 12px;
        margin-top: 2rem;
    '>
        <p style='margin: 0; font-size: 1.1rem; font-weight: 600;'>
            🚀 GetJobAI - Votre Assistant IA de Recherche d'Emploi
        </p>
        <p style='margin: 0.5rem 0 0 0; opacity: 0.7;'>
            Powered by UI UX PRO MAX • © 2026 GetJobAI
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
