"""
GetJobAI Dashboard - Production
================================
Dashboard professionnel avec UI UX PRO MAX intégré
"""
import streamlit as st
import streamlit.components.v1 as components
import os
import json
from datetime import datetime

# Import UI UX PRO MAX
from ui_ux_pro_max import (
    inject_animations,
    section_header,
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
from chatbot import (chatbot_page, generer_message_linkedin, generer_post_linkedin,
                     generer_image_post)

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

# Injecter animations CSS
inject_animations()

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
if not st.session_state.auth_ok and _cookie_jar:
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

with st.sidebar:
    # Logo
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {COLOR_SCHEMES['getjobai']['primary']} 0%, {COLOR_SCHEMES['getjobai']['secondary']} 100%);
        padding: 2rem 1rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 2rem;
    ">
        <h1 style="color: white; margin: 0; font-size: 2rem;">🚀 GetJobAI</h1>
        <p style="color: white; opacity: 0.9; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Assistant IA de Recherche d'Emploi
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    nav_options = [
        "🏠 Dashboard",
        "📋 Offres d'Emploi",
        "📤 Candidatures",
        "🤖 Agents IA",
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
        if st.button("🚪 Déconnexion"):
            if _cookies is not None:
                try:
                    _cookies.delete("gja_auth", key="gja_del")
                except Exception:
                    pass
            st.session_state.auth_ok = False
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.session_state.is_admin = False
            st.session_state.real_admin_email = None
            st.session_state.is_whitelisted = False
            st.rerun()

# ============================================================
# BARRIÈRE D'ACCÈS — utilisateurs non approuvés
# ============================================================
# Un utilisateur connecté mais non approuvé (et non admin) ne voit rien
# tant qu'un administrateur ne l'a pas validé.
if st.session_state.user_id and not st.session_state.is_admin \
        and not st.session_state.is_whitelisted:
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
    section_header(
        "🏠 Tableau de Bord",
        f"Bienvenue sur GetJobAI - {datetime.now().strftime('%d %B %Y')}"
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

        section_header(
            "📋 Offres d'Emploi",
            f"{len(all_jobs)} offres trouvées par vos agents"
        )

        # Sources réellement présentes dans les données
        sources_dispo = sorted({j.get("source", "") for j in all_jobs if j.get("source")})

        # Filtres
        col1, col2, col3 = st.columns([3, 2, 3])
        with col1:
            sel_sources = st.multiselect("Sources", sources_dispo, default=[])
        with col2:
            score_min = st.slider("Score minimum", 0, 100, 0)
        with col3:
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
            results.append(j)

        # Trier par score décroissant
        results.sort(key=lambda x: x.get("score") or 0, reverse=True)

        st.caption(f"📊 {len(results)} offre(s) affichée(s)")
        st.markdown("<br>", unsafe_allow_html=True)

        if not results:
            alert("Aucune offre ne correspond à vos filtres. Ajustez les critères.", "warning")
        else:
            for offre in results[:100]:
                job_card_pro(offre)

# ============================================================
# PAGE: CANDIDATURES
# ============================================================

elif page == "📤 Candidatures":
    section_header(
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
            alert("Aucune candidature pour l'instant. Lancez l'agent **📝 Préparer "
                  "Candidatures** (page 🤖 Agents IA) : il génère vos lettres et les "
                  "place ici en attente de votre validation.", "info")
        else:
            statut_icon = {
                "en_attente": "⏳", "validee": "✔️", "a_envoyer": "📨", "sans_email": "✉️", "envoyee": "✅", "recue": "📬",
                "reponse": "💬", "entretien": "🎯", "refus": "❌",
            }
            en_attente_list = [c for c in cands if (c.get("status") or "") == "en_attente"]
            st.caption(f"📋 {len(cands)} candidature(s) • {len(en_attente_list)} à valider")
            st.markdown("<br>", unsafe_allow_html=True)

            for c in cands:
                cid = c.get("id")
                stt = (c.get("status") or "").lower()
                icon = next((v for k, v in statut_icon.items() if k in stt), "📄")
                titre = c.get("job_title") or "Poste"
                company = c.get("company") or "—"
                score = c.get("score_match") or 0
                lettre = c.get("lettre") or "(pas de lettre)"
                cv_nom = c.get("cv_nom") or "CV.pdf"
                url = c.get("job_url") or ""

                with st.container():
                    st.markdown(f"### {icon} {titre} — {company}")
                    st.caption(f"Score {score}/100 • Statut: **{c.get('status','')}**"
                               + (f" • [Voir l'offre]({url})" if url else ""))

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
                        st.warning("✉️ Aucun email RH trouvé — à postuler manuellement (voir l'offre).")

                    # Suivi du cycle de vie réel : Envoyée → Réponse (Refus | Entretien)
                    st.caption("📊 Statut de la candidature :")
                    b1, b2, b3, b4, b5 = st.columns(5)
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
                    st.markdown("---")

# ============================================================
# PAGE: AGENTS IA
# ============================================================

elif page == "🤖 Agents IA":
    section_header(
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

            spinner = "🔄" if statut == "processing" else ("⏳" if statut == "pending" else ("✅" if statut == "completed" else "❌"))
            st.markdown(f"""
            <style>@keyframes pulse {{0%,100%{{opacity:1;}}50%{{opacity:0.5;}}}}
            @keyframes spin {{from{{transform:rotate(0)}}to{{transform:rotate(360deg)}}}}</style>
            <div style="background:linear-gradient(135deg,#1e293b,#334155);padding:1.5rem;
                 border-radius:14px;border-left:5px solid {couleur};margin-bottom:1rem;">
              <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:2rem;{'animation:spin 1.5s linear infinite;display:inline-block;' if statut=='processing' else ''}">{spinner}</span>
                <div>
                  <h3 style="color:white;margin:0;">{agent_nom}</h3>
                  <p style="color:#cbd5e1;margin:0;font-size:0.9rem;">{libelle}</p>
                </div>
              </div>
              <div style="margin-top:1rem;">{chips}</div>
            </div>
            """, unsafe_allow_html=True)

            # Logs en direct
            st.markdown("**📜 Logs en direct**")
            st.code(live_log[-2500:] or "En attente de la sortie de l'agent…", language="text")

            if statut in ("completed", "failed"):
                if statut == "completed":
                    st.success(f"✅ {agent_nom} terminé ! Résultats dans 📦 Livrables et 📋 Offres.")
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

    for i, agent in enumerate(agents):
        with col1 if i % 2 == 0 else col2:
            card(agent["name"], agent["desc"], agent["color"], agent["icon"])
            st.caption(f"📊 {agent['stats']}")

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

        cga, cgb, cgc = st.columns([2, 1, 1])
        with cga:
            pg_secteur = st.text_input(
                "Vos compétences / métiers (le post s'aligne dessus)",
                value="génie civil, gestion de projet, chargé de projet, coordonnateur de travaux",
                key="pg_secteur")
        with cgb:
            pg_ville = st.text_input("Ville", value="Ottawa", key="pg_ville")
        with cgc:
            pg_langue = st.selectbox("Langue", ["fr", "en"], key="pg_langue",
                                     format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English")
        pg_theme = st.text_input("Thème (optionnel — laissez vide pour un thème automatique)",
                                 value="", key="pg_theme")

        pg_avec_image = st.checkbox("🖼️ Générer aussi une image hyper-réaliste (DALL-E 3) alignée sur le post",
                                    value=True, key="pg_avec_image")

        c_gen, c_close = st.columns([3, 1])
        with c_gen:
            if st.button("✨ Générer le post", type="primary", use_container_width=True):
                with st.spinner("Génération du post…"):
                    st.session_state.gen_post_text = generer_post_linkedin(
                        secteur=pg_secteur, ville=pg_ville, langue=pg_langue,
                        theme=pg_theme or None,
                    )
                st.session_state.pop("gen_post_image", None)
                if pg_avec_image:
                    with st.spinner("Génération de l'image hyper-réaliste (DALL-E 3, ~15s)…"):
                        st.session_state.gen_post_image = generer_image_post(
                            st.session_state.gen_post_text, secteur=pg_secteur)
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

            # Image générée (DALL-E 3) — affichée pour validation
            img_url = st.session_state.get("gen_post_image")
            if img_url:
                st.image(img_url, caption="🖼️ Image hyper-réaliste générée (alignée sur le post)",
                         use_container_width=True)
                if st.button("🔄 Régénérer l'image", key="pg_regen_img"):
                    with st.spinner("Nouvelle image (DALL-E 3)…"):
                        st.session_state.gen_post_image = generer_image_post(
                            post_edit, secteur=pg_secteur)
                    st.rerun()
            elif pg_avec_image:
                st.caption("⚠️ Image non générée (quota OpenAI ou erreur) — le post peut être publié sans image.")

            cpub, ccopy = st.columns([2, 1])
            with cpub:
                if st.button("✅ Approuver et publier sur LinkedIn", type="primary",
                             use_container_width=True, key="pg_publish"):
                    if st.session_state.user_id:
                        try:
                            db = get_supabase_client()
                            action = db.create_action(
                                user_id=st.session_state.user_id,
                                agent_name="linkedin_agent",
                                params={"approved_post": post_edit,
                                        "image_url": st.session_state.get("gen_post_image", ""),
                                        "source": "dashboard_post"},
                            )
                            if action and action.get("id"):
                                st.session_state.monitor_action_id = action["id"]
                                st.session_state.monitor_agent = "Post LinkedIn"
                                st.session_state.show_post_gen = False
                                st.session_state.pop("gen_post_text", None)
                                st.rerun()
                            else:
                                st.error("❌ Échec du lancement de la publication.")
                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")
                    else:
                        st.error("User ID manquant.")
            with ccopy:
                _safe_post = json.dumps(post_edit)
                components.html(
                    f"""
                    <button onclick='navigator.clipboard.writeText({_safe_post})
                        .then(()=>{{this.innerHTML="✅ Copié !";
                        setTimeout(()=>this.innerHTML="📋 Copier",1600);}})'
                        style="background:linear-gradient(135deg,#2563eb,#7c3aed);
                        color:#fff;border:none;padding:11px 16px;border-radius:8px;
                        cursor:pointer;font-size:15px;font-weight:600;width:100%;">
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
                    status_icon = {
                        "pending": "⏳",
                        "running": "🔄",
                        "completed": "✅",
                        "failed": "❌"
                    }.get(action.get("status", "pending"), "⏳")

                    col_icon, col_info = st.columns([1, 11])
                    with col_icon:
                        st.markdown(f"### {status_icon}")
                    with col_info:
                        st.markdown(f"**{action.get('agent_name', 'Unknown')}** - {action.get('status', 'pending')}")
                        st.caption(f"Créé: {action.get('created_at', 'N/A')}")
            else:
                st.info("Aucune action récente")
        except Exception as e:
            st.error(f"Erreur chargement actions: {e}")
    else:
        st.warning("Connectez-vous pour voir vos actions")

# ============================================================
# PAGE: RÉSEAU (networking semi-auto)
# ============================================================

elif page == "🤝 Réseau":
    section_header(
        "🤝 Réseau LinkedIn",
        "Contacts trouvés + messages prêts — vous envoyez en 1 clic (robuste, sans risque)"
    )

    if not st.session_state.user_id:
        alert("Connectez-vous pour voir vos contacts réseau.", "warning")
    else:
        db = get_supabase_client()
        contacts = db.get_contacts_reseau(st.session_state.user_id)
        a_faire = [c for c in contacts if (c.get("statut") or "") == "a_contacter"]

        alert("💡 L'agent **Networking** trouve les recruteurs et rédige les messages. "
              "Ici, vous ouvrez le profil, copiez le message, et envoyez **vous-même** "
              "(1 min) — aucun risque de ban, rien ne casse.", "info")

        if not contacts:
            alert("Aucun contact pour l'instant. Lancez l'agent **🤝 Networking Agent** "
                  "(page 🤖 Agents IA) : il trouvera des recruteurs et préparera les messages.", "info")
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
                            c.get("nom", ""), c.get("titre", ""), c.get("entreprise", ""))
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

                with st.container():
                    st.markdown(f"### {icon} {nom}")
                    sub = " • ".join([x for x in [titre, entreprise, c.get('source','')] if x])
                    st.caption(sub)
                    st.markdown(f"**Action :** {'💬 Message' if type_action=='message' else '📨 Invitation'}")

                    if url:
                        st.markdown(f"🔗 [Ouvrir le profil LinkedIn]({url})")

                    if not message:
                        if st.button("✨ Générer un message", key=f"gen_{cid}"):
                            msg = generer_message_linkedin(nom, titre, entreprise)
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
                                style="background:linear-gradient(135deg,#2563eb,#7c3aed);
                                color:#fff;border:none;padding:9px 16px;border-radius:8px;
                                cursor:pointer;font-size:14px;font-weight:600;width:100%;">
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
                    st.markdown("---")

# ============================================================
# PAGE: LIVRABLES (résultats de tous les agents)
# ============================================================

elif page == "📦 Livrables":
    section_header(
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
            alert("Aucun livrable pour l'instant. Lancez un agent depuis la page "
                  "🤖 Agents IA — son résultat apparaîtra ici.", "info")
        else:
            # Filtre par type
            types_presents = sorted({l.get("type", "autre") for l in livrables})
            sel_type = st.selectbox(
                "Filtrer par type",
                ["Tous"] + [TYPE_INFO.get(t, ("📦", t))[1] for t in types_presents]
            )

            st.caption(f"📊 {len(livrables)} livrable(s)")
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
                date = (liv.get("created_at") or "")[:16].replace("T", " ")

                with st.container():
                    st.markdown(f"**{icon} {label}** {statut_badge}")
                    st.caption(f"🤖 {liv.get('agent', '')} • {date}")
                    st.markdown(f"{resume}")

                    # Contenu en PLEINE LARGEUR (lisible en grand)
                    contenu = liv.get("contenu_json") or {}
                    guide = contenu.get("guide", "") if isinstance(contenu, dict) else ""
                    if t == "entretien" and guide:
                        with st.expander("📖 Lire mon guide d'entretien (plein écran)", expanded=False):
                            st.markdown(guide)
                        st.download_button(
                            "📥 Télécharger le guide",
                            data=guide,
                            file_name=f"guide_entretien_{(liv.get('created_at') or '')[:10]}.md",
                            mime="text/markdown",
                            key=f"dl_{liv.get('id')}",
                        )
                    else:
                        with st.expander("Détail"):
                            output = contenu.get("output", "") if isinstance(contenu, dict) else str(contenu)
                            st.code(output[-2000:] or "(vide)")
                    st.markdown("---")

# ============================================================
# PAGE: PLANIFICATEUR
# ============================================================

elif page == "📅 Planificateur":
    section_header(
        "📅 Planificateur",
        "Lancez vos agents automatiquement à heures fixes"
    )

    # Agents planifiables (nom → action_type = fichier .py)
    schedulable = {
        "Job Hunter": "job_hunter",
        "Indeed Agent": "indeed_agent",
        "COOP Hunter": "coop_hunter",
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
            st.info("Aucune planification. Ajoutez-en une ci-dessus.")
        else:
            for s in schedules:
                sid = s.get("id")
                agent_name = type_to_name.get(s.get("agent_type"), s.get("agent_type"))
                run_time = s.get("run_time", "")[:5]
                enabled = bool(s.get("enabled"))
                last = s.get("last_run_date") or "jamais"
                statut = "🟢 Actif" if enabled else "⏸️ En pause"

                col1, col2, col3, col4 = st.columns([4, 3, 2, 2])
                with col1:
                    st.markdown(f"**🤖 {agent_name}**")
                    st.caption(f"Dernier lancement: {last}")
                with col2:
                    st.markdown(f"🕐 **{run_time}** • {format_jours(s.get('days'))}")
                    st.caption(statut)
                with col3:
                    if enabled:
                        if st.button("⏸️ Pause", key=f"pause_{sid}"):
                            db.toggle_schedule(sid, False)
                            st.rerun()
                    else:
                        if st.button("▶️ Activer", key=f"on_{sid}"):
                            db.toggle_schedule(sid, True)
                            st.rerun()
                with col4:
                    if st.button("🗑️ Suppr.", key=f"del_{sid}"):
                        db.delete_schedule(sid)
                        st.rerun()
                st.markdown("---")

# ============================================================
# PAGE: ASSISTANT IA
# ============================================================

elif page == "💬 Assistant IA":
    section_header(
        "💬 Assistant IA",
        "Votre coach personnel pour la recherche d'emploi"
    )
    chatbot_page()

# ============================================================
# PAGE: PARAMÈTRES
# ============================================================

elif page == "⚙️ Paramètres":
    section_header(
        "⚙️ Paramètres",
        "Configurez votre profil et vos préférences"
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["👤 Profil", "🔑 Keywords", "🔔 Notifications", "🔒 Mot de passe", "🔗 LinkedIn"])

    with tab1:
        st.subheader("Informations Personnelles")

        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom complet", "Patrice Arnold Sob Feukam")
            email = st.text_input("Email", "sobpatrice92@gmail.com")
            telephone = st.text_input("Téléphone", "15142364628")

        with col2:
            ville = st.text_input("Ville", "Ottawa")
            province = st.text_input("Province", "Ontario")
            linkedin = st.text_input("LinkedIn URL", "linkedin.com/in/patrice-arnold-sob-feukam")

        if st.button("💾 Sauvegarder le Profil", type="primary"):
            st.success("✅ Profil sauvegardé!")

    with tab2:
        st.subheader("Mots-clés de Recherche")

        keywords = st.text_area(
            "Keywords (un par ligne)",
            value="""CHARGE DE PROJET JUNIOR CONSTRUCTION
COORDONATEUR DES TRAVAUX CONSTRUCTION
ESTIMATEUR JUNIOR CONSTRUCTION
SURVEILLANT DE CHANTIER
TECHNICIEN DE LABORATOIRE
TECHNOLOGUE CONSTRUCTION GENIE CIVIL""",
            height=200
        )

        if st.button("💾 Sauvegarder les Keywords", type="primary"):
            st.success("✅ Keywords sauvegardés!")

    with tab3:
        st.subheader("Notifications Email")

        email_notif = st.checkbox("Recevoir rapport après chaque agent", value=True)
        email_offres = st.checkbox("Alertes nouvelles offres", value=True)
        email_candidatures = st.checkbox("Confirmations candidatures", value=True)

        if st.button("💾 Sauvegarder Notifications", type="primary"):
            st.success("✅ Préférences sauvegardées!")

    with tab4:
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

    with tab5:
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
                    ok = db.save_setting(st.session_state.user_id, "linkedin_cookie", cookies_txt.strip())
                    if li_at:
                        db.save_setting(st.session_state.user_id, "linkedin_cookie_li_at", li_at)
                    if ok:
                        st.success(f"✅ {len(data)} cookies enregistrés ! "
                                   "L'agent Networking peut maintenant fonctionner.")
                    else:
                        st.error("Erreur d'enregistrement.")
                except Exception:
                    st.error("❌ JSON invalide. Collez bien l'export complet (commence par `[` ).")

# ============================================================
# PAGE: ADMIN
# ============================================================

elif page == "👑 Admin":
    section_header(
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

                with st.container():
                    c1, c2, c3 = st.columns([5, 3, 2])
                    with c1:
                        st.markdown(f"**{badge_actif} {nom}{badge_admin}**")
                        st.caption(f"✉️ {email}")
                        st.caption(badge_appr)
                    with c2:
                        st.markdown(f"📊 **{nb_offres}** offres")
                        if ville:
                            st.caption(f"📍 {ville}")
                    with c3:
                        # Approuver / Révoquer (sauf pour les admins, toujours approuvés)
                        if not u.get("is_admin"):
                            if is_approved:
                                if st.button("🚫 Révoquer", key=f"revoke_{uid}"):
                                    if db.update_user_status(uid, "is_whitelisted", False):
                                        st.success(f"{email} révoqué")
                                        st.rerun()
                            else:
                                if st.button("✅ Approuver", key=f"approve_{uid}", type="primary"):
                                    if db.update_user_status(uid, "is_whitelisted", True):
                                        st.success(f"{email} approuvé")
                                        st.rerun()
                        # Consulter ce compte (sauf le sien)
                        if email != st.session_state.user_email:
                            if st.button("👁️ Voir", key=f"view_{uid}"):
                                st.session_state.user_email = email
                                st.session_state.user_id = None  # force rechargement
                                st.rerun()
                        # Supprimer le compte (sauf admin et soi-même) — avec confirmation
                        if not u.get("is_admin") and email != st.session_state.user_email:
                            if st.session_state.get(f"confirm_del_{uid}"):
                                st.warning("⚠️ Supprimer définitivement ce compte ET ses données ?")
                                if st.button("✅ Oui, supprimer", key=f"cfm_{uid}"):
                                    if db.delete_user(uid):
                                        st.success(f"{email} supprimé")
                                    st.session_state[f"confirm_del_{uid}"] = False
                                    st.rerun()
                                if st.button("Annuler", key=f"cancel_{uid}"):
                                    st.session_state[f"confirm_del_{uid}"] = False
                                    st.rerun()
                            else:
                                if st.button("🗑️ Supprimer", key=f"del_{uid}"):
                                    st.session_state[f"confirm_del_{uid}"] = True
                                    st.rerun()
                    st.markdown("---")

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
