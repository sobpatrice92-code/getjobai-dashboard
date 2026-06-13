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
                <p style="margin: 0.25rem 0; color: {colors['text']}; opacity: 0.7;">📍 {job.get('location', 'N/A')} | 🌐 {job.get('source', 'N/A')}{(" | 🕒 " + job['_date_aff']) if job.get('_date_aff') else ""}</p>
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

    /* Boutons natifs (action, download, submit) : sombre + bord néon, lisible */
    .stButton > button,
    [data-testid="stDownloadButton"] > button,
    [data-testid="stFormSubmitButton"] > button,
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-secondary"] {
        background: rgba(30,155,255,0.12) !important;
        color: #eaf6ff !important;
        font-weight: 600 !important;
        border: 1px solid rgba(45,212,191,0.50) !important;
        border-radius: 10px !important;
        transition: transform 0.15s, box-shadow 0.2s, background 0.2s !important;
    }
    .stButton > button *,
    [data-testid="stDownloadButton"] > button *,
    [data-testid="stFormSubmitButton"] > button * {
        color: #eaf6ff !important;
    }
    .stButton > button:hover,
    [data-testid="stDownloadButton"] > button:hover,
    [data-testid="stFormSubmitButton"] > button:hover,
    [data-testid="baseButton-primary"]:hover,
    [data-testid="baseButton-secondary"]:hover {
        background: linear-gradient(135deg, #1e9bff 0%, #2dd4bf 100%) !important;
        box-shadow: 0 0 18px rgba(45,212,191,0.55) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:hover *,
    [data-testid="stDownloadButton"] > button:hover *,
    [data-testid="stFormSubmitButton"] > button:hover * {
        color: #04101f !important;
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

    /* Légendes (st.caption) : gris trop foncé par défaut -> bleu clair lisible */
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"] * {
        color: #9fc1e0 !important;
    }
    /* Texte secondaire / aide des widgets */
    small, .stMarkdown small { color: #9fc1e0 !important; }

    /* Expanders : panneau sombre + texte clair (en-tête et contenu) */
    [data-testid="stExpander"] details {
        background: rgba(17,28,52,0.60) !important;
        border: 1px solid rgba(30,155,255,0.20) !important;
        border-radius: 10px !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span {
        color: #eaf6ff !important;
    }
    [data-testid="stExpander"] summary svg { fill: #2dd4bf !important; }
    [data-testid="stExpander"] summary strong,
    [data-testid="stExpander"] summary b { color: #eaf6ff !important; }
    /* Contenu déplié : forcer la couleur claire sur TOUS les éléments de texte */
    [data-testid="stExpander"] [data-testid="stExpanderDetails"],
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] p,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] li,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] span,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] div,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] strong,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] b,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] em {
        color: #eaf6ff !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] strong,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] b {
        color: #7fe3d4 !important;   /* libellés en gras → teal lisible */
    }

    /* ===== PASSE LISIBILITÉ COMPLÈTE — widgets natifs ===== */
    /* Libellés de widgets */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    .stRadio label, .stCheckbox label, .stSelectbox label,
    .stMultiSelect label, .stSlider label, .stTextArea label,
    .stTextInput label, .stFileUploader label, .stDateInput label,
    .stNumberInput label, [data-testid="stSubheader"] {
        color: #cfe2f5 !important;
    }

    /* Selectbox / multiselect : valeur affichée */
    [data-baseweb="select"] div { color: #eaf6ff !important; }

    /* Menu déroulant (popover) : fond sombre + options lisibles */
    [data-baseweb="popover"], [data-baseweb="menu"], ul[role="listbox"] {
        background: #0f1a30 !important;
    }
    [role="option"], [data-baseweb="menu"] li {
        background: #0f1a30 !important;
        color: #dbeafe !important;
    }
    [role="option"]:hover, [data-baseweb="menu"] li:hover {
        background: rgba(30,155,255,0.20) !important;
    }

    /* Tags multiselect : pastilles teal lisibles */
    [data-baseweb="tag"] {
        background: linear-gradient(135deg,#1e9bff,#2dd4bf) !important;
    }
    [data-baseweb="tag"], [data-baseweb="tag"] span, [data-baseweb="tag"] svg {
        color: #04101f !important; fill: #04101f !important;
    }

    /* Radio / checkbox : texte des options */
    [data-testid="stRadio"] label, [data-testid="stRadio"] div,
    [data-testid="stCheckbox"] label, [data-testid="stCheckbox"] div {
        color: #dbeafe !important;
    }

    /* Slider : valeur et bornes */
    [data-testid="stThumbValue"] { color: #2dd4bf !important; }
    [data-testid="stTickBarMin"], [data-testid="stTickBarMax"] { color: #9fc1e0 !important; }

    /* File uploader : zone de dépôt */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(17,28,52,0.60) !important;
        border: 1px dashed rgba(45,212,191,0.40) !important;
    }
    [data-testid="stFileUploader"] *,
    [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #cfe2f5 !important;
    }

    /* Blocs de code */
    [data-testid="stCode"], pre, code {
        background: #0c1526 !important;
        color: #d7f0ff !important;
    }

    /* Dataframe / table */
    [data-testid="stDataFrame"] { color: #dbeafe !important; }
    [data-testid="stTable"] th, [data-testid="stTable"] td {
        color: #dbeafe !important;
        border-color: rgba(30,155,255,0.20) !important;
    }

    /* Metric natif (si utilisé) */
    [data-testid="stMetricValue"] { color: #1e9bff !important; }
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { color: #cfe2f5 !important; }

    /* Onglets : inactifs lisibles, actif teal */
    .stTabs [role="tab"] { color: #9fc1e0 !important; }
    .stTabs [aria-selected="true"] { color: #2dd4bf !important; }

    /* Liens */
    a, a:visited { color: #2dd4bf !important; }

    /* Tableaux Markdown */
    [data-testid="stMarkdownContainer"] table th,
    [data-testid="stMarkdownContainer"] table td {
        color: #dbeafe !important;
        border-color: rgba(30,155,255,0.20) !important;
    }

    /* Chat (Assistant IA) */
    [data-testid="stChatMessage"] {
        background: rgba(17,28,52,0.50) !important;
        color: #dbeafe !important;
        border-radius: 12px;
    }
    [data-testid="stChatInput"] textarea { color: #eaf6ff !important; }

    /* ===== PHASE B sur le contenu (toutes pages) ===== */
    /* Séparateurs '---' -> ligne néon dégradée */
    hr {
        border: none !important;
        height: 1px !important;
        margin: 1.2rem 0 !important;
        background: linear-gradient(90deg, transparent, rgba(30,155,255,0.65), rgba(45,212,191,0.65), transparent) !important;
        box-shadow: 0 0 8px rgba(30,155,255,0.30) !important;
    }

    /* Onglets (Paramètres) : barre glass + onglet actif lumineux */
    .stTabs [role="tablist"] {
        background: rgba(17,28,52,0.50);
        border: 1px solid rgba(30,155,255,0.18);
        border-radius: 12px;
        padding: 4px;
        backdrop-filter: blur(8px);
        gap: 4px;
    }
    .stTabs [role="tab"] { border-radius: 8px; padding: 0 14px; }
    .stTabs [aria-selected="true"] {
        background: rgba(30,155,255,0.16) !important;
        box-shadow: 0 0 12px rgba(45,212,191,0.30);
    }

    /* Barres de progression : dégradé néon */
    [data-testid="stProgress"] > div > div > div {
        background: linear-gradient(90deg, #1e9bff, #2dd4bf) !important;
        box-shadow: 0 0 10px rgba(45,212,191,0.45) !important;
    }

    /* Images (post LinkedIn, photo) : cadre lumineux */
    [data-testid="stImage"] img {
        border-radius: 12px;
        border: 1px solid rgba(45,212,191,0.30);
        box-shadow: 0 0 18px rgba(30,155,255,0.15);
    }

    /* Items de liste (st.container(border=True)) -> panneau glass néon */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(135deg, rgba(22,34,61,0.55) 0%, rgba(10,15,30,0.42) 100%);
        border: 1px solid rgba(30,155,255,0.20) !important;
        border-radius: 14px;
        box-shadow: 0 0 16px rgba(30,155,255,0.08);
        backdrop-filter: blur(8px);
        transition: box-shadow 0.2s;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 0 22px rgba(45,212,191,0.20);
    }

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

    /* ===== LOADER 3D HOLOGRAPHIQUE (exécution d'agent) ===== */
    @keyframes holoRingX { from{transform:rotateX(0deg) rotateY(62deg);} to{transform:rotateX(360deg) rotateY(62deg);} }
    @keyframes holoRingY { from{transform:rotateY(0deg) rotateX(62deg);} to{transform:rotateY(360deg) rotateX(62deg);} }
    @keyframes holoRingZ { from{transform:rotateZ(0deg);} to{transform:rotateZ(360deg);} }
    @keyframes holoCore  { 0%,100%{transform:scale(1);opacity:1;} 50%{transform:scale(1.25);opacity:0.7;} }
    .holo3d {
        width: 76px; height: 76px; position: relative;
        transform-style: preserve-3d; perspective: 240px; flex: 0 0 auto;
    }
    .holo3d span {
        position: absolute; inset: 0; border-radius: 50%;
        border: 2px solid transparent;
    }
    .holo3d .r1 { border-top-color:#1e9bff; border-bottom-color:#1e9bff;
        animation: holoRingX 2s linear infinite; box-shadow: 0 0 12px rgba(30,155,255,0.5); }
    .holo3d .r2 { border-left-color:#2dd4bf; border-right-color:#2dd4bf;
        animation: holoRingY 2.6s linear infinite; box-shadow: 0 0 12px rgba(45,212,191,0.5); }
    .holo3d .r3 { border-top-color:#7c5cff; border-bottom-color:#7c5cff;
        animation: holoRingZ 1.6s linear infinite; }
    .holo3d .core {
        position: absolute; inset: 37%; border-radius: 50%;
        background: radial-gradient(circle, #2dd4bf, #1e9bff);
        box-shadow: 0 0 18px #2dd4bf; animation: holoCore 1.4s ease-in-out infinite;
    }

    /* ===== RESPONSIVE / MOBILE (≤ 640px) ===== */
    @media (max-width: 640px) {
        /* Hero : padding et titres réduits pour ne pas déborder */
        .holo-hero { padding: 1.4rem 1.2rem !important; border-radius: 14px !important; }
        .holo-hero h1 { font-size: 1.45rem !important; line-height: 1.2; }
        .holo-hero p { font-size: 0.85rem !important; }
        /* Titres de section plus compacts */
        [data-testid="stMarkdownContainer"] h2 { font-size: 1.3rem !important; }
        [data-testid="stMarkdownContainer"] h3 { font-size: 1.1rem !important; }
        /* Loader 3D un peu plus petit */
        .holo3d { width: 56px !important; height: 56px !important; }
        /* Allège le flou (perf mobile) + grille plus serrée */
        [data-testid="stVerticalBlockBorderWrapper"],
        .holo-hero { backdrop-filter: blur(5px) !important; }
        [data-testid="stAppViewContainer"] {
            background-size: 28px 28px, 28px 28px, 100% 100% !important;
        }
        /* Cartes/panneaux : padding réduit */
        [data-testid="stVerticalBlockBorderWrapper"] { padding: 0.2rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)


def holo_loader_3d():
    """Petit loader 3D holographique (anneaux orbitaux + noyau pulsant)."""
    return (
        '<div class="holo3d"><span class="r1"></span><span class="r2"></span>'
        '<span class="r3"></span><span class="core"></span></div>'
    )


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


# ============================================================
# SURCOUCHE VISUELLE « NEO-GLASS » (CSS uniquement — aucune logique modifiée)
# ============================================================

def inject_neo_glass():
    """Raffinement visuel Neo-Glass : police Inter/Poppins, cartes en verre
    dépoli RÉACTIVES (hover lift + glow), boutons premium animés, fade-in du
    contenu, scrollbar fine. 100 % CSS — aucune fonction ni API touchée."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');

    /* ----- Typographie Inter / Poppins ----- */
    html, body, .stApp, .stMarkdown, p, span, div, label,
    input, textarea, button, select, [data-testid="stWidgetLabel"] {
        font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Poppins', 'Inter', sans-serif !important;
        letter-spacing: .2px;
    }

    /* ----- Fade-in doux du contenu à chaque (re)chargement ----- */
    [data-testid="stAppViewContainer"] .main .block-container {
        animation: gjaFadeUp .55s cubic-bezier(.22,.61,.36,1);
    }
    @keyframes gjaFadeUp {
        from { opacity: 0; transform: translateY(14px); }
        to   { opacity: 1; transform: none; }
    }

    /* ----- CARTES (st.container(border=True)) : verre dépoli réactif ----- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(150deg, rgba(30,41,75,0.55) 0%, rgba(12,18,38,0.45) 100%) !important;
        backdrop-filter: blur(14px) saturate(120%);
        -webkit-backdrop-filter: blur(14px) saturate(120%);
        border: 1px solid rgba(120,160,255,0.16) !important;
        border-radius: 18px !important;
        box-shadow: 0 8px 30px rgba(4,8,20,0.45), inset 0 1px 0 rgba(255,255,255,0.04);
        transition: transform .25s cubic-bezier(.22,.61,.36,1), box-shadow .25s, border-color .25s;
        will-change: transform;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px);
        border-color: rgba(45,212,191,0.45) !important;
        box-shadow: 0 14px 40px rgba(4,8,20,0.55), 0 0 26px rgba(91,124,255,0.22);
    }

    /* ----- Boutons : transitions + appel à l'action lumineux (primary) ----- */
    .stButton > button {
        border-radius: 12px !important;
        transition: transform .18s, box-shadow .25s, background .25s !important;
    }
    .stButton > button[kind="primary"],
    [data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #5b7cff 0%, #9b6bff 50%, #2dd4bf 100%) !important;
        border: none !important;
        color: #fff !important;
        box-shadow: 0 6px 20px rgba(91,124,255,0.35);
        animation: gjaGlow 3.5s ease-in-out infinite;
    }
    .stButton > button[kind="primary"] *,
    [data-testid="baseButton-primary"] * { color: #fff !important; }
    .stButton > button[kind="primary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        transform: translateY(-2px) scale(1.015);
        box-shadow: 0 10px 30px rgba(155,107,255,0.5) !important;
    }
    @keyframes gjaGlow {
        0%,100% { box-shadow: 0 6px 20px rgba(91,124,255,0.35); }
        50%     { box-shadow: 0 8px 28px rgba(45,212,191,0.45); }
    }

    /* ----- Link buttons (Connecter LinkedIn, etc.) ----- */
    [data-testid="stLinkButton"] a {
        border-radius: 12px !important;
        transition: transform .18s, box-shadow .25s !important;
    }
    [data-testid="stLinkButton"] a:hover {
        transform: translateY(-2px);
        box-shadow: 0 0 18px rgba(45,212,191,0.4) !important;
    }

    /* ----- Navigation sidebar : pastilles réactives ----- */
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 10px; padding: 2px 6px;
        transition: background .2s, transform .15s;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(91,124,255,0.12);
        transform: translateX(3px);
    }

    /* ----- Scrollbar fine et discrète ----- */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-thumb { background: rgba(91,124,255,0.35); border-radius: 8px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(45,212,191,0.5); }
    ::-webkit-scrollbar-track { background: transparent; }
    </style>
    """, unsafe_allow_html=True)
