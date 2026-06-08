"""
UI UX PRO MAX - Design System for GetJobAI
===========================================
Base de données intégrée de composants UI/UX professionnels
pour Streamlit Dashboard
"""
import streamlit as st

# ============================================================
# PALETTES DE COULEURS PROFESSIONNELLES
# ============================================================

COLOR_SCHEMES = {
    "getjobai": {
        "primary": "#1e9bff",      # bleu électrique
        "secondary": "#2dd4bf",    # teal
        "success": "#2dd4bf",
        "warning": "#fbbf24",
        "danger": "#f87171",
        "info": "#38bdf8",
        "light": "#16223d",        # surface "claire" = panneau sombre
        "dark": "#070b16",
        "text": "#dbeafe",         # texte clair sur fond sombre
        "background": "#0a0f1e"
    },
    "modern": {
        "primary": "#6366f1",
        "secondary": "#8b5cf6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#3b82f6",
        "light": "#f9fafb",
        "dark": "#111827"
    },
    "dark_mode": {
        "primary": "#818cf8",
        "secondary": "#a78bfa",
        "success": "#34d399",
        "warning": "#fbbf24",
        "danger": "#f87171",
        "info": "#60a5fa",
        "light": "#1f2937",
        "dark": "#111827",
        "background": "#0f172a",
        "text": "#f3f4f6"
    }
}

# ============================================================
# COMPOSANTS UI STYLÉS
# ============================================================

def card(title: str, content: str, color: str = "primary", icon: str = "📋"):
    """Carte stylée avec bordure colorée"""
    colors = COLOR_SCHEMES["getjobai"]

    st.markdown(f"""
    <div style="
        border-left: 4px solid {colors[color]};
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, rgba(22,34,61,0.65) 0%, rgba(10,15,30,0.55) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(30,155,255,0.18);
        border-left: 4px solid {colors[color]};
        border-radius: 10px;
        box-shadow: 0 0 18px rgba(30,155,255,0.10), inset 0 0 12px rgba(45,212,191,0.04);
    ">
        <h3 style="margin: 0; color: {colors[color]};">{icon} {title}</h3>
        <p style="margin: 0.5rem 0 0 0; color: {colors['text']};">{content}</p>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = None, icon: str = "📊"):
    """Métrique stylée avec delta"""
    colors = COLOR_SCHEMES["getjobai"]

    delta_html = ""
    if delta:
        delta_color = colors["success"] if delta.startswith("+") else colors["danger"]
        delta_html = f'<div style="color: {delta_color}; font-size: 0.9rem; margin-top: 0.5rem;">{delta}</div>'

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(22,34,61,0.65) 0%, rgba(10,15,30,0.55) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(30,155,255,0.18);
        padding: 1.5rem;
        border-radius: 14px;
        box-shadow: 0 0 18px rgba(30,155,255,0.12), inset 0 0 14px rgba(45,212,191,0.05);
        text-align: center;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="color: {colors['text']}; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">{label}</div>
        <div style="font-size: 2rem; font-weight: bold; color: {colors['primary']}; margin-top: 0.5rem;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def alert(message: str, type: str = "info", dismissible: bool = False):
    """Alerte stylée (info, success, warning, danger)"""
    colors = COLOR_SCHEMES["getjobai"]
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "danger": "❌"
    }

    st.markdown(f"""
    <div style="
        background-color: {colors[type]}15;
        border-left: 4px solid {colors[type]};
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 4px;
        color: {colors['text']};
    ">
        <strong>{icons[type]} {message}</strong>
    </div>
    """, unsafe_allow_html=True)


def progress_bar(label: str, value: int, max_value: int = 100, color: str = "primary"):
    """Barre de progression stylée"""
    colors = COLOR_SCHEMES["getjobai"]
    percentage = (value / max_value) * 100

    st.markdown(f"""
    <div style="margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: {colors['text']}; font-weight: 500;">{label}</span>
            <span style="color: {colors['text']}; font-weight: bold;">{value}/{max_value}</span>
        </div>
        <div style="
            background-color: {colors['light']};
            border-radius: 10px;
            height: 10px;
            overflow: hidden;
        ">
            <div style="
                background: linear-gradient(90deg, {colors[color]} 0%, {colors['secondary']} 100%);
                width: {percentage}%;
                height: 100%;
                border-radius: 10px;
                transition: width 0.3s ease;
            "></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def badge(text: str, color: str = "primary", size: str = "md"):
    """Badge stylé"""
    colors = COLOR_SCHEMES["getjobai"]
    sizes = {"sm": "0.75rem", "md": "0.85rem", "lg": "1rem"}

    return f"""
    <span style="
        background-color: {colors[color]};
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: {sizes[size]};
        font-weight: 600;
        display: inline-block;
        margin: 0.25rem;
    ">{text}</span>
    """


def button_custom(label: str, color: str = "primary", icon: str = ""):
    """Bouton HTML stylé (pour affichage uniquement, pas interactif)"""
    colors = COLOR_SCHEMES["getjobai"]

    return f"""
    <button style="
        background: linear-gradient(135deg, {colors[color]} 0%, {colors['secondary']} 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: transform 0.2s;
    " onmouseover="this.style.transform='translateY(-2px)'"
       onmouseout="this.style.transform='translateY(0)'">
        {icon} {label}
    </button>
    """


def section_header(title: str, subtitle: str = "", icon: str = ""):
    """En-tête de section stylé"""
    colors = COLOR_SCHEMES["getjobai"]

    subtitle_html = f'<p style="color: {colors["text"]}; opacity: 0.7; margin: 0.5rem 0 0 0;">{subtitle}</p>' if subtitle else ""

    st.markdown(f"""
    <div style="margin: 2rem 0 1.5rem 0; padding-bottom: 0.4rem;">
        <h2 style="
            margin: 0;
            color: {colors['primary']};
            font-size: 1.8rem;
            font-weight: 700;
            text-shadow: 0 0 14px rgba(30,155,255,0.30);
        ">{icon} {title}</h2>
        {subtitle_html}
        <div class="holo-section-bar"></div>
    </div>
    """, unsafe_allow_html=True)


def stats_grid(stats: list):
    """Grille de statistiques

    Args:
        stats: Liste de dicts avec 'label', 'value', 'icon', 'delta' (optionnel)
    """
    cols = st.columns(len(stats))
    for i, stat in enumerate(stats):
        with cols[i]:
            metric_card(
                stat.get('label', ''),
                stat.get('value', '0'),
                stat.get('delta'),
                stat.get('icon', '📊')
            )


def job_card_pro(job: dict):
    """Carte offre d'emploi professionnelle"""
    colors = COLOR_SCHEMES["getjobai"]

    score = job.get('score', 0)
    score_color = colors['success'] if score >= 75 else (colors['warning'] if score >= 60 else colors['danger'])

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, rgba(22,34,61,0.65) 0%, rgba(10,15,30,0.55) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(30,155,255,0.18);
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 12px;
        box-shadow: 0 0 18px rgba(30,155,255,0.10);
        border-left: 4px solid {score_color};
        transition: transform 0.2s, box-shadow 0.2s;
    " onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 8px 28px rgba(30,155,255,0.30)'"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 0 18px rgba(30,155,255,0.10)'">

        <div style="display: flex; justify-content: space-between; align-items: start;">
            <div style="flex: 1;">
                <h3 style="margin: 0; color: {colors['primary']}; font-size: 1.3rem;">{job.get('title', 'N/A')}</h3>
                <p style="margin: 0.5rem 0; color: {colors['text']}; font-size: 1.1rem; font-weight: 500;">🏢 {job.get('company', 'N/A')}</p>
                <p style="margin: 0.25rem 0; color: {colors['text']}; opacity: 0.7;">📍 {job.get('location', 'N/A')} | 🌐 {job.get('source', 'N/A')}</p>
            </div>
            <div style="
                background: {score_color};
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-size: 1.2rem;
                font-weight: bold;
                text-align: center;
                min-width: 60px;
            ">
                {score}<br><span style="font-size: 0.7rem;">/ 100</span>
            </div>
        </div>

        <div style="margin-top: 1rem;">
            <a href="{job.get('url', '#')}" target="_blank" style="
                background: {colors['primary']};
                color: white;
                padding: 0.5rem 1.5rem;
                border-radius: 6px;
                text-decoration: none;
                display: inline-block;
                font-weight: 600;
            ">🔗 Voir l'offre</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# ANIMATIONS CSS
# ============================================================

def inject_animations():
    """Injecte les animations CSS dans le dashboard"""
    st.markdown("""
    <style>
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes slideIn {
        from { transform: translateX(-100%); }
        to { transform: translateX(0); }
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }

    .slide-in {
        animation: slideIn 0.3s ease-out;
    }

    .pulse {
        animation: pulse 2s infinite;
    }

    @keyframes neonPulse {
        0%, 100% { box-shadow: 0 0 8px rgba(30,155,255,0.35); }
        50%      { box-shadow: 0 0 22px rgba(45,212,191,0.55); }
    }

    /* ===== THÈME GLOBAL HOLOGRAPHIQUE (bleu électrique + teal) ===== */
    /* Fond sombre dégradé + grille high-tech subtile */
    [data-testid="stAppViewContainer"] {
        background:
            linear-gradient(rgba(30,155,255,0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(30,155,255,0.04) 1px, transparent 1px),
            radial-gradient(circle at 18% 0%, #0d1a33 0%, #0a0f1e 45%, #060912 100%);
        background-size: 42px 42px, 42px 42px, 100% 100%;
    }
    [data-testid="stHeader"] { background: transparent; }

    /* Sidebar : panneau translucide + bord néon */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(13,26,51,0.92) 0%, rgba(8,12,24,0.92) 100%);
        border-right: 1px solid rgba(45,212,191,0.22);
        box-shadow: 4px 0 24px rgba(30,155,255,0.08);
    }

    /* Titres : légère lueur néon */
    h1, h2, h3 { text-shadow: 0 0 14px rgba(30,155,255,0.25); }

    /* Boutons natifs Streamlit : dégradé bleu→teal + lueur au survol */
    .stButton > button {
        background: linear-gradient(135deg, #1e9bff 0%, #2dd4bf 100%);
        color: #04101f;
        font-weight: 600;
        border: 1px solid rgba(45,212,191,0.35);
        border-radius: 10px;
        transition: transform 0.15s, box-shadow 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 18px rgba(45,212,191,0.55);
        color: #04101f;
    }

    /* Champs (input, textarea, select) : panneau sombre + focus bleu */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-baseweb="select"] > div {
        background-color: rgba(17,28,52,0.85) !important;
        border: 1px solid rgba(30,155,255,0.22) !important;
        border-radius: 10px !important;
        color: #dbeafe !important;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stTextArea"] textarea:focus {
        border-color: #2dd4bf !important;
        box-shadow: 0 0 12px rgba(45,212,191,0.35) !important;
    }

    /* Onglets actifs : accent teal */
    .stTabs [aria-selected="true"] { color: #2dd4bf !important; }

    /* Barre de défilement néon */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: #0a0f1e; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #1e9bff, #2dd4bf);
        border-radius: 6px;
    }

    /* ===== PHASE B — effets holographiques avancés ===== */
    @keyframes holoSweep {
        0%   { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
    }
    @keyframes scanline {
        0%   { transform: translateY(-100%); }
        100% { transform: translateY(100%); }
    }
    @keyframes floatY {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-6px); }
    }
    @keyframes titleGlow {
        0%, 100% { text-shadow: 0 0 10px rgba(30,155,255,0.35); }
        50%      { text-shadow: 0 0 22px rgba(45,212,191,0.65); }
    }

    /* Hero holographique */
    .holo-hero {
        position: relative;
        overflow: hidden;
        padding: 2.2rem 2.4rem;
        margin: 0.5rem 0 1.8rem 0;
        border-radius: 18px;
        border: 1px solid rgba(45,212,191,0.28);
        background:
            linear-gradient(120deg,
                rgba(30,155,255,0.16) 0%,
                rgba(45,212,191,0.10) 35%,
                rgba(13,26,51,0.55) 70%) ,
            rgba(10,15,30,0.65);
        background-size: 200% 100%, 100% 100%;
        animation: holoSweep 9s linear infinite;
        backdrop-filter: blur(14px);
        box-shadow: 0 0 30px rgba(30,155,255,0.18), inset 0 0 30px rgba(45,212,191,0.06);
    }
    /* Scanlines + grille sur le hero */
    .holo-hero::before {
        content: "";
        position: absolute; inset: 0;
        background-image:
            repeating-linear-gradient(0deg, transparent 0, transparent 2px, rgba(45,212,191,0.05) 3px),
            linear-gradient(rgba(30,155,255,0.06) 1px, transparent 1px),
            linear-gradient(90deg, rgba(30,155,255,0.06) 1px, transparent 1px);
        background-size: 100% 3px, 34px 34px, 34px 34px;
        pointer-events: none;
    }
    /* Faisceau de scan qui descend */
    .holo-hero::after {
        content: "";
        position: absolute; left: 0; right: 0; top: 0; height: 40%;
        background: linear-gradient(180deg, rgba(45,212,191,0.12), transparent);
        animation: scanline 6s linear infinite;
        pointer-events: none;
    }
    .holo-hero h1 {
        margin: 0; position: relative; z-index: 1;
        font-size: 2.1rem; font-weight: 800; letter-spacing: 0.5px;
        color: #eaf6ff;
        animation: titleGlow 4s ease-in-out infinite;
    }
    .holo-hero p {
        margin: 0.5rem 0 0 0; position: relative; z-index: 1;
        color: #9fc7e8; font-size: 1rem;
    }
    .holo-dot {
        display: inline-block; width: 9px; height: 9px; border-radius: 50%;
        background: #2dd4bf; box-shadow: 0 0 10px #2dd4bf;
        margin-right: 8px; animation: floatY 3s ease-in-out infinite;
    }

    /* En-têtes de section : soulignement lumineux animé */
    .holo-section-bar {
        height: 2px; margin-top: 0.6rem; border-radius: 2px;
        background: linear-gradient(90deg, #1e9bff, #2dd4bf, transparent);
        background-size: 200% 100%;
        animation: holoSweep 6s linear infinite;
        box-shadow: 0 0 10px rgba(30,155,255,0.45);
    }
    </style>
    """, unsafe_allow_html=True)


def hero_holographic(title: str, subtitle: str = ""):
    """Bannière hero holographique animée (scanlines, lueur, dégradé balayé)."""
    sub = f'<p>{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div class="holo-hero">
        <h1><span class="holo-dot"></span>{title}</h1>
        {sub}
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# EXEMPLE D'UTILISATION
# ============================================================

if __name__ == "__main__":
    st.set_page_config(page_title="UI UX PRO MAX Demo", layout="wide")

    inject_animations()

    section_header("🎨 UI UX PRO MAX", "Base de données de composants professionnels", "")

    # Stats
    stats_grid([
        {"label": "Total Offres", "value": "120", "icon": "📊", "delta": "+45 cette semaine"},
        {"label": "Candidatures", "value": "28", "icon": "📤", "delta": "+12 aujourd'hui"},
        {"label": "Taux Match", "value": "88%", "icon": "🎯", "delta": "+5%"},
    ])

    # Alertes
    alert("Bienvenue dans GetJobAI Dashboard!", "success")
    alert("Nouveau job hunter terminé avec 22 offres", "info")

    # Carte
    card("Job Hunter", "Agent de recherche d'emploi automatisé sur LinkedIn et Job Bank", "primary", "🎯")

    # Barre de progression
    progress_bar("Progression du mois", 75, 100, "success")

    # Job card
    job_card_pro({
        "title": "Chargé de Projet Junior",
        "company": "Pomerleau",
        "location": "Ottawa, ON",
        "score": 85,
        "source": "LinkedIn",
        "url": "https://linkedin.com/jobs/123"
    })
