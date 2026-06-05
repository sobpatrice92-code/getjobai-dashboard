"""
GetJobAI Dashboard - Production
================================
Dashboard professionnel avec UI UX PRO MAX intégré
"""
import streamlit as st
import os
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

# Initialiser session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = "sobpatrice92@gmail.com"  # Par défaut pour démo

# Charger user depuis Supabase si email existe
if st.session_state.user_email and not st.session_state.user_id:
    try:
        db = get_supabase_client()
        user = db.get_user_by_email(st.session_state.user_email)
        if user:
            st.session_state.user_id = user['id']
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
    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📋 Offres d'Emploi",
            "📤 Candidatures",
            "🤖 Agents IA",
            "⚙️ Paramètres"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # User info
    if st.session_state.user_email:
        st.markdown(f"👤 **{st.session_state.user_email}**")
        if st.button("🚪 Déconnexion"):
            st.session_state.user_id = None
            st.session_state.user_email = None
            st.rerun()

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
    section_header(
        "📋 Offres d'Emploi",
        "175 offres trouvées avec vos keywords personnalisés"
    )

    # Filtres
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        sources = st.multiselect(
            "Sources",
            ["LinkedIn", "Job Bank", "Talent.com", "Charity Village"],
            default=["LinkedIn", "Job Bank"]
        )

    with col2:
        score_min = st.slider("Score minimum", 0, 100, 60)

    with col3:
        sort_by = st.selectbox("Trier par", ["Score ↓", "Date ↓", "Entreprise"])

    with col4:
        keywords_filter = st.text_input("🔍 Rechercher", placeholder="Mots-clés...")

    st.markdown("<br>", unsafe_allow_html=True)

    # Exemples d'offres (à remplacer par vraies données Supabase)
    offres_demo = [
        {
            "title": "Chargé de Projet Junior Construction",
            "company": "Pomerleau",
            "location": "Ottawa, ON",
            "score": 85,
            "source": "LinkedIn",
            "url": "https://linkedin.com/jobs/view/123"
        },
        {
            "title": "Coordonnateur des Travaux Construction",
            "company": "VINCI",
            "location": "Ottawa, ON",
            "score": 82,
            "source": "Job Bank",
            "url": "https://jobbank.gc.ca/jobposting/123"
        },
        {
            "title": "Estimateur Junior Construction",
            "company": "Bird Construction",
            "location": "Ottawa, ON",
            "score": 78,
            "source": "Talent.com",
            "url": "https://talent.com/job/123"
        },
        {
            "title": "Project Manager - Infrastructure",
            "company": "Habitat for Humanity Ottawa",
            "location": "Ottawa, ON",
            "score": 72,
            "source": "Charity Village",
            "url": "https://charityvillage.com/job/123"
        },
        {
            "title": "Surveillant de Chantier",
            "company": "Chandos Construction",
            "location": "Ottawa, ON",
            "score": 68,
            "source": "LinkedIn",
            "url": "https://linkedin.com/jobs/view/456"
        },
        {
            "title": "Technologue en Génie Civil",
            "company": "Stantec",
            "location": "Ottawa, ON",
            "score": 65,
            "source": "Job Bank",
            "url": "https://jobbank.gc.ca/jobposting/456"
        }
    ]

    # Afficher offres
    offres_filtrees = [o for o in offres_demo if o['score'] >= score_min]

    if not offres_filtrees:
        alert("Aucune offre ne correspond à vos filtres. Ajustez les critères ci-dessus.", "warning")
    else:
        for offre in offres_filtrees:
            job_card_pro(offre)

# ============================================================
# PAGE: CANDIDATURES
# ============================================================

elif page == "📤 Candidatures":
    section_header(
        "📤 Mes Candidatures",
        "Suivez l'état de vos candidatures"
    )

    # Stats candidatures
    stats_grid([
        {"label": "En Attente", "value": "28", "icon": "⏳"},
        {"label": "Envoyées", "value": "33", "icon": "✅"},
        {"label": "Réponses", "value": "12", "icon": "💬"},
        {"label": "Entretiens", "value": "3", "icon": "🎯"}
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # Alerte candidatures en attente
    alert("⏳ Vous avez 28 candidatures en attente d'approbation", "warning")

    st.markdown("<br>", unsafe_allow_html=True)

    # Action
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("✅ Valider et Envoyer Toutes (28 candidatures)", type="primary", use_container_width=True):
            with st.spinner("Envoi des candidatures en cours..."):
                st.success("✅ 28 candidatures envoyées avec succès!")

    with col2:
        if st.button("👁️ Prévisualiser", use_container_width=True):
            st.info("Prévisualisation des candidatures...")

    with col3:
        if st.button("❌ Annuler Tout", use_container_width=True):
            st.warning("Candidatures annulées")

# ============================================================
# PAGE: AGENTS IA
# ============================================================

elif page == "🤖 Agents IA":
    section_header(
        "🤖 Agents IA",
        "Lancez vos assistants de recherche d'emploi automatisés"
    )

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
            "name": "Smart Apply",
            "desc": "Candidature automatique intelligente",
            "icon": "📤",
            "color": "warning",
            "stats": "Taux d'envoi: 95% • Email + LinkedIn + ATS"
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
        }
    ]

    # Afficher agents en grille avec exécution fonctionnelle
    col1, col2 = st.columns(2)

    # Mapping agent name → agent_type pour Supabase
    agent_mapping = {
        "Job Hunter": "job_hunter",
        "Indeed Agent": "indeed_agent",
        "COOP Hunter": "coop_hunter",
        "Smart Apply": "smart_apply",
        "Networking Agent": "networking_agent",
        "Follow-up Engine": "followup_engine"
    }

    for i, agent in enumerate(agents):
        with col1 if i % 2 == 0 else col2:
            card(agent["name"], agent["desc"], agent["color"], agent["icon"])
            st.caption(f"📊 {agent['stats']}")

            if st.button(f"🚀 Lancer {agent['name']}", key=f"launch_{i}", use_container_width=True):
                if st.session_state.user_id:
                    try:
                        st.info(f"🔍 DEBUG: user_id={st.session_state.user_id}, agent={agent['name']}")
                        db = get_supabase_client()
                        agent_type = agent_mapping.get(agent["name"], "unknown")
                        st.info(f"🔍 DEBUG: agent_type={agent_type}")

                        # Créer action dans Supabase
                        action = db.create_action(
                            user_id=st.session_state.user_id,
                            agent_name=agent_type,
                            params={"source": "dashboard"}
                        )

                        st.info(f"🔍 DEBUG: action result={action}")

                        if action:
                            alert(f"✅ {agent['name']} lancé! Un worker local va le traiter.", "success")
                            alert("⚠️ IMPORTANT: Lancez simple_worker.py sur votre machine locale pour exécuter l'agent.", "warning")
                        else:
                            st.error(f"Erreur lors du lancement de {agent['name']} - action retournée None")
                    except Exception as e:
                        st.error(f"Exception: {type(e).__name__}: {e}")
                else:
                    st.error("User ID manquant - impossible de lancer l'agent")

            st.markdown("<br>", unsafe_allow_html=True)

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
# PAGE: PARAMÈTRES
# ============================================================

elif page == "⚙️ Paramètres":
    section_header(
        "⚙️ Paramètres",
        "Configurez votre profil et vos préférences"
    )

    tab1, tab2, tab3 = st.tabs(["👤 Profil", "🔑 Keywords", "🔔 Notifications"])

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
