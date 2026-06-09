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
        "📖 Guide",
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

                with st.container(border=True):
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
            pg_moi = st.checkbox("🧑 Me mettre en avant (image inspirée de MA photo de profil)",
                                 value=False, key="pg_moi")
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

            cpub, ccopy = st.columns([2, 1])
            with cpub:
                if st.button("✅ Envoyer à mon extension (publier)", type="primary",
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
      <strong>🚀 En 3 étapes :</strong><br>
      <b>1.</b> Remplissez votre profil dans <b>⚙️ Paramètres</b> (CV, mots-clés, ville, secteur…) —
      c'est ce qui personnalise <u>tous</u> les agents.<br>
      <b>2.</b> Allez dans <b>🤖 Agents IA</b> et cliquez <b>Lancer</b> sur l'agent voulu.
      Une animation 3D vous montre l'avancement en direct.<br>
      <b>3.</b> Récupérez le résultat à l'endroit indiqué (📋 Offres, 📤 Candidatures, 🤝 Réseau,
      📦 Livrables) — et un <b>rapport détaillé arrive par email</b>.
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

                with st.container(border=True):
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

                with st.container(border=True):
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

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        ["👤 Profil", "🔑 Keywords", "📄 Mon CV", "🔔 Notifications", "🔒 Mot de passe",
         "🔗 LinkedIn", "🎨 Post LinkedIn", "🧩 Extension"])

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
        st.subheader("Notifications Email")

        email_notif = st.checkbox("Recevoir rapport après chaque agent", value=True)
        email_offres = st.checkbox("Alertes nouvelles offres", value=True)
        email_candidatures = st.checkbox("Confirmations candidatures", value=True)

        if st.button("💾 Sauvegarder Notifications", type="primary"):
            st.success("✅ Préférences sauvegardées!")

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
                "Personne à taguer à chaque post (optionnel)",
                value=cur.get("post_tag") or "",
                placeholder="ex : Fredy Beukam — laissez vide si aucun")

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
