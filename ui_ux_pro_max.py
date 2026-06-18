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
        "primary": "#2F6BFF",      # bleu confiant (AIApply)
        "secondary": "#2dd4bf",    # teal accent
        "success": "#16A34A",      # vert (statut OK)
        "warning": "#F59E0B",      # ambre
        "danger": "#EF4444",       # rouge
        "info": "#2F6BFF",
        "light": "#F5F7FB",        # surface claire
        "dark": "#111827",
        "text": "#111827",         # texte foncé sur fond clair
        "background": "#FFFFFF"
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

def card(title: str, content: str, color: str = "primary", icon: str = "📋", accent: str = "",
         footer: str = ""):
    """Carte Neo-Glass colorée : badge d'icône en dégradé + bord d'accent + glow +
    hover. 'accent' (blue|purple|green|orange|cyan) prioritaire ; sinon dérivé de 'color'.
    'footer' (optionnel) : ligne de stats discrète en pied de carte (séparateur fin)."""
    _map = {"primary": "blue", "secondary": "purple", "success": "green",
            "warning": "orange", "danger": "orange", "info": "cyan"}
    a1, a2 = _ACCENTS.get(accent or _map.get(color, "blue"), _ACCENTS["blue"])
    _footer_html = (
        f'<div style="margin:.8rem 0 0 0; padding-top:.6rem; border-top:1px solid #EEF1F6;'
        f'color:#5B6678; font-size:.82rem;">{footer}</div>' if footer else ""
    )
    st.markdown(f"""
    <div style="
        position:relative; overflow:hidden;
        background:#FFFFFF;
        border:1px solid #E7EBF2;
        border-left:3px solid {a1};
        padding:1.05rem 1.25rem; margin:.6rem 0 .2rem 0;
        border-radius:14px 14px 6px 6px;
        box-shadow:0 1px 2px rgba(16,24,40,.05), 0 10px 24px rgba(16,24,40,.06);
        transition:transform .2s cubic-bezier(.22,.61,.36,1), border-color .2s, box-shadow .2s;
    " onmouseover="this.style.transform='translateY(-3px)';this.style.borderColor='#D5DCE8';this.style.boxShadow='0 16px 32px rgba(16,24,40,.12)'"
       onmouseout="this.style.transform='none';this.style.borderColor='#E7EBF2';this.style.boxShadow='0 1px 2px rgba(16,24,40,.05), 0 10px 24px rgba(16,24,40,.06)'">
        <div style="display:flex; align-items:center; gap:.7rem;">
            <div style="width:38px;height:38px;border-radius:10px;display:flex;align-items:center;
                        justify-content:center;font-size:1.15rem;flex:0 0 auto;
                        background:linear-gradient(135deg,{a1},{a2});box-shadow:0 4px 12px {a1}40;">{icon}</div>
            <h3 style="margin:0;color:#111827;font-family:'Poppins','Inter',sans-serif;font-size:1.07rem;font-weight:600;">{title}</h3>
        </div>
        <p style="margin:.55rem 0 0 0;color:#5B6678;font-size:.9rem;line-height:1.5;">{content}</p>
        {_footer_html}
    </div>
    """, unsafe_allow_html=True)


# Palette d'accents Neo-Glass pour les cartes stats (bleu/violet/vert/orange…)
_ACCENTS = {
    "blue":   ("#6271FF", "#4E5BE6"),   # indigo — accent principal
    "purple": ("#A78BFA", "#7C3AED"),
    "green":  ("#34D399", "#10B981"),
    "orange": ("#FBBF24", "#F59E0B"),
    "cyan":   ("#2DD4BF", "#0EA5A4"),
}


def metric_card(label: str, value: str, delta: str = None, icon: str = "📊", accent: str = "blue"):
    """Métrique Neo-Glass : badge d'icône coloré + valeur + delta, avec glow et
    hover (couleur d'accent par carte). 'accent' ∈ blue|purple|green|orange|cyan."""
    a1, a2 = _ACCENTS.get(accent, _ACCENTS["blue"])
    delta_html = ""
    if delta:
        delta_html = f'<div style="color:#16A34A;font-size:0.82rem;font-weight:600;margin-top:0.55rem;">{delta}</div>'

    st.markdown(f"""
    <div style="
        position:relative; overflow:hidden;
        background:#FFFFFF;
        border:1px solid #E7EBF2;
        padding:1.25rem 1.3rem;
        border-radius:16px;
        box-shadow:0 1px 2px rgba(16,24,40,.05), 0 10px 24px rgba(16,24,40,.06);
        transition:transform .2s cubic-bezier(.22,.61,.36,1), box-shadow .2s, border-color .2s;
    " onmouseover="this.style.transform='translateY(-4px)';this.style.borderColor='#D5DCE8';this.style.boxShadow='0 16px 34px rgba(16,24,40,.12)'"
       onmouseout="this.style.transform='none';this.style.borderColor='#E7EBF2';this.style.boxShadow='0 1px 2px rgba(16,24,40,.05), 0 10px 24px rgba(16,24,40,.06)'">
        <div style="display:flex; align-items:center; gap:.6rem; margin-bottom:.55rem;">
            <div style="width:42px;height:42px;border-radius:12px;display:flex;align-items:center;
                        justify-content:center;font-size:1.25rem;
                        background:linear-gradient(135deg,{a1},{a2});box-shadow:0 4px 14px {a1}40;">{icon}</div>
            <div style="color:#5B6678;font-size:0.82rem;font-weight:600;letter-spacing:.3px;">{label}</div>
        </div>
        <div style="font-size:2.1rem;font-weight:700;color:#111827;line-height:1.1;
                    font-family:'Poppins','Inter',sans-serif;">{value}</div>
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
                stat.get('icon', '📊'),
                stat.get('accent', ['blue', 'purple', 'green', 'orange'][i % 4])
            )


def job_card_pro(job: dict):
    """Carte offre d'emploi professionnelle"""
    colors = COLOR_SCHEMES["getjobai"]

    score = job.get('score', 0)
    score_color = colors['success'] if score >= 75 else (colors['warning'] if score >= 60 else colors['danger'])

    st.markdown(f"""
    <div style="
        background:#FFFFFF;
        border: 1px solid #E7EBF2;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 14px;
        box-shadow: 0 1px 2px rgba(16,24,40,.05), 0 10px 24px rgba(16,24,40,.06);
        border-left: 4px solid {score_color};
        transition: transform 0.2s, box-shadow 0.2s, border-color .2s;
    " onmouseover="this.style.transform='translateY(-3px)'; this.style.borderColor='#D5DCE8'; this.style.boxShadow='0 16px 32px rgba(16,24,40,.12)'"
       onmouseout="this.style.transform='translateY(0)'; this.style.borderColor='#E7EBF2'; this.style.boxShadow='0 1px 2px rgba(16,24,40,.05), 0 10px 24px rgba(16,24,40,.06)'">
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


def inject_premium_polish():
    """Couche de FINITION premium (au-dessus de neo_glass) : tabs en segmented
    control, champs avec focus-ring lumineux, hiérarchie typographique raffinée,
    sidebar en profondeur, métriques en cartes, densité aérée. 100% CSS, additif."""
    st.markdown("""
    <style>
    :root{
      --gja-blue:#5b7cff; --gja-blue2:#1e9bff; --gja-teal:#2dd4bf;
      --gja-ink:#eaf2ff; --gja-muted:#93a4c8; --gja-line:rgba(120,160,255,.14);
    }

    /* Densité + largeur de lecture confortable */
    .main .block-container{ padding-top:2.1rem; padding-bottom:4rem; max-width:1180px; }

    /* Rendu net + hiérarchie typographique */
    html, body, .stApp{ -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; }
    .main h1{ font-size:2.05rem !important; font-weight:700 !important; line-height:1.15 !important;
      letter-spacing:-.5px !important;
      background:linear-gradient(92deg,#eaf2ff 0%, #bcd4ff 58%, var(--gja-teal) 130%);
      -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
    [data-testid="stSidebar"] h1{ -webkit-text-fill-color:#fff !important; background:none !important; }
    h2{ font-size:1.45rem !important; letter-spacing:-.3px !important; }
    h3{ font-size:1.16rem !important; letter-spacing:-.2px !important; }
    p, li, label{ line-height:1.6; }
    [data-testid="stCaptionContainer"]{ color:var(--gja-muted) !important; }

    /* ----- TABS : segmented control premium ----- */
    [data-testid="stTabs"] [role="tablist"]{
      gap:6px; background:rgba(12,20,40,.55); padding:6px; border-radius:14px;
      border:1px solid var(--gja-line); backdrop-filter:blur(8px); }
    [data-testid="stTabs"] [role="tab"]{
      border-radius:10px !important; padding:8px 15px !important; color:var(--gja-muted) !important;
      font-weight:600 !important; transition:all .2s; }
    [data-testid="stTabs"] [role="tab"]:hover{ color:var(--gja-ink) !important; background:rgba(91,124,255,.10); }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"]{
      color:#fff !important; background:linear-gradient(135deg,var(--gja-blue),var(--gja-teal)) !important;
      box-shadow:0 4px 14px rgba(91,124,255,.35); }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"]{ display:none !important; }

    /* ----- CHAMPS : focus-ring lumineux ----- */
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    [data-baseweb="select"] > div{
      border-radius:12px !important; border:1px solid var(--gja-line) !important;
      transition:border-color .2s, box-shadow .2s !important; }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus,
    [data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within{
      border-color:var(--gja-blue) !important;
      box-shadow:0 0 0 3px rgba(91,124,255,.25) !important; outline:none !important; }
    ::selection{ background:rgba(45,212,191,.32); }

    /* ----- METRICS : carte accent ----- */
    [data-testid="stMetric"]{
      background:linear-gradient(150deg,rgba(30,41,75,.45),rgba(12,18,38,.35));
      border:1px solid var(--gja-line); border-radius:16px; padding:14px 16px; }
    [data-testid="stMetricValue"]{ font-family:'Poppins','Inter',sans-serif; font-weight:700; }
    [data-testid="stMetricLabel"]{ color:var(--gja-muted) !important; }

    /* ----- EXPANDER + SIDEBAR + boutons secondaires ----- */
    [data-testid="stExpander"]{ border:1px solid var(--gja-line) !important; border-radius:14px !important;
      overflow:hidden; background:rgba(12,18,38,.35); }
    [data-testid="stExpander"] summary:hover{ color:var(--gja-teal) !important; }
    [data-testid="stSidebar"]{ background:linear-gradient(180deg,#0c1426 0%, #0a0f1e 100%) !important;
      border-right:1px solid var(--gja-line); }
    .stButton > button[kind="secondary"]{
      background:rgba(91,124,255,.08) !important; border:1px solid var(--gja-line) !important;
      color:var(--gja-ink) !important; border-radius:12px !important; }
    .stButton > button[kind="secondary"]:hover{
      border-color:var(--gja-teal) !important; background:rgba(45,212,191,.10) !important; }

    /* ----- Divers : dividers, table, focus clavier ----- */
    hr{ border-color:var(--gja-line) !important; opacity:.7; }
    [data-testid="stDataFrame"]{ border-radius:14px; overflow:hidden; border:1px solid var(--gja-line); }
    *:focus-visible{ outline:2px solid var(--gja-teal) !important; outline-offset:2px; }
    </style>
    """, unsafe_allow_html=True)


def inject_aiapply_light():
    """Thème CLAIR premium inspiré d'AIApply : fond blanc, accent bleu confiant,
    cartes blanches à ombre douce + bordures fines, statuts vert/orange, sobre et
    action-oriented. Appelée en DERNIER (gagne la cascade sur les couches sombres)."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&display=swap');
    :root{
      --bg:#FFFFFF; --bg2:#F5F7FB; --surf:#FFFFFF;
      --line:#E7EBF2; --line2:#D5DCE8;
      --tx:#111827; --tx2:#5B6678; --tx3:#9AA4B5;
      --acc:#2F6BFF; --acc2:#1E5BF0; --green:#16A34A; --orange:#F59E0B;
    }

    /* ---------- Police + fond + texte ---------- */
    html, body, .stApp, p, span, div, label, input, textarea, button, select{
      font-family:'Inter', -apple-system, 'Segoe UI', sans-serif; }
    h1,h2,h3,h4,h5{ font-family:'Poppins','Inter',sans-serif !important; color:var(--tx) !important;
      letter-spacing:-.3px; }
    .stApp, [data-testid="stAppViewContainer"], .main, [data-testid="stHeader"]{ background:var(--bg) !important; }
    .stApp, .stMarkdown, p, li, span, div, label,
    [data-testid="stWidgetLabel"] label{ color:var(--tx); }
    [data-testid="stCaptionContainer"], .stCaption, small{ color:var(--tx2) !important; }
    a, .stMarkdown a{ color:var(--acc) !important; text-decoration:none; }
    a:hover{ text-decoration:underline; }
    .main .block-container{ padding-top:2rem; padding-bottom:4rem; max-width:1180px; }
    .main h1{ color:var(--tx) !important; font-weight:700 !important; letter-spacing:-.6px !important;
      -webkit-text-fill-color:initial !important; background:none !important; }

    /* ---------- CARTES (st.container border=True) : blanc, ombre douce ---------- */
    [data-testid="stVerticalBlockBorderWrapper"]{
      background:#FFFFFF !important; backdrop-filter:none !important; -webkit-backdrop-filter:none !important;
      border:1px solid var(--line) !important; border-radius:16px !important;
      box-shadow:0 1px 2px rgba(16,24,40,.05), 0 12px 28px rgba(16,24,40,.06) !important; }
    [data-testid="stVerticalBlockBorderWrapper"]:hover{
      transform:translateY(-2px); border-color:var(--line2) !important;
      box-shadow:0 16px 34px rgba(16,24,40,.10) !important; }

    /* ---------- Boutons : bleu plein, arrondi ---------- */
    .stButton > button{ border-radius:10px !important; font-weight:600 !important;
      transition:transform .15s, background .18s, border-color .18s, box-shadow .2s !important; }
    .stButton > button[kind="primary"], [data-testid="baseButton-primary"]{
      background:var(--acc) !important; border:1px solid var(--acc) !important; color:#fff !important;
      animation:none !important; box-shadow:0 1px 2px rgba(16,24,40,.10) !important; }
    .stButton > button[kind="primary"] *, [data-testid="baseButton-primary"] *{ color:#fff !important; }
    .stButton > button[kind="primary"]:hover, [data-testid="baseButton-primary"]:hover{
      background:var(--acc2) !important; transform:translateY(-1px);
      box-shadow:0 8px 18px rgba(47,107,255,.28) !important; }
    .stButton > button[kind="secondary"]{
      background:#FFFFFF !important; border:1px solid var(--line2) !important; color:var(--tx) !important; }
    .stButton > button[kind="secondary"]:hover{
      border-color:var(--acc) !important; color:var(--acc) !important; background:#F4F8FF !important; }
    [data-testid="stLinkButton"] a{ border-radius:10px !important; }

    /* ---------- Champs : blanc, bordure claire, focus bleu ---------- */
    .stTextInput input, .stTextArea textarea, .stNumberInput input,
    [data-baseweb="select"] > div, [data-baseweb="input"]{
      background:#FFFFFF !important; border:1px solid var(--line2) !important;
      color:var(--tx) !important; border-radius:10px !important; }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder{ color:var(--tx3) !important; }
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus,
    [data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within{
      border-color:var(--acc) !important; box-shadow:0 0 0 3px rgba(47,107,255,.18) !important; }
    ::selection{ background:rgba(47,107,255,.18); }

    /* ---------- Tabs : segmented clair ---------- */
    [data-testid="stTabs"] [role="tablist"]{
      background:#F1F4FA !important; border:1px solid var(--line) !important; gap:4px; padding:5px;
      border-radius:12px; backdrop-filter:none !important; }
    [data-testid="stTabs"] [role="tab"]{ color:var(--tx2) !important; border-radius:8px !important;
      font-weight:600 !important; padding:7px 14px !important; }
    [data-testid="stTabs"] [role="tab"]:hover{ color:var(--tx) !important; background:#FFFFFF !important; }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"]{
      background:#FFFFFF !important; color:var(--acc) !important;
      box-shadow:0 1px 3px rgba(16,24,40,.12) !important; }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"]{ display:none !important; }

    /* ---------- Sidebar + métriques + expander (clairs) ---------- */
    [data-testid="stSidebar"]{ background:#F7F9FC !important; border-right:1px solid var(--line) !important; }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover{ background:#EAF0FF !important; }
    [data-testid="stMetric"]{ background:#FFFFFF !important; border:1px solid var(--line) !important;
      border-radius:14px; box-shadow:0 1px 2px rgba(16,24,40,.05); }
    [data-testid="stMetricValue"]{ color:var(--tx) !important; }
    [data-testid="stMetricLabel"]{ color:var(--tx2) !important; }
    [data-testid="stExpander"]{ background:#FFFFFF !important; border:1px solid var(--line) !important;
      border-radius:12px; }

    /* ---------- Détails ---------- */
    hr{ border-color:var(--line) !important; }
    ::-webkit-scrollbar-thumb{ background:#CBD5E1 !important; border-radius:8px; }
    ::-webkit-scrollbar-thumb:hover{ background:#94A3B8 !important; }
    code{ background:#F1F4FA !important; color:var(--acc2) !important; border:1px solid var(--line); border-radius:6px; }

    /* ---------- Hero clair (override du bandeau sombre holo-hero) ---------- */
    .holo-hero{ background:linear-gradient(120deg,#F0F5FF 0%, #EAF7F4 100%) !important;
      border:1px solid #E2E8F4 !important; backdrop-filter:none !important; animation:none !important;
      box-shadow:0 1px 2px rgba(16,24,40,.04), 0 12px 30px rgba(16,24,40,.06) !important; }
    .holo-hero::before, .holo-hero::after{ display:none !important; }
    .holo-hero h1{ color:#111827 !important; -webkit-text-fill-color:#111827 !important; background:none !important; }
    .holo-hero p{ color:#5B6678 !important; }
    .holo-dot{ background:#2F6BFF !important; box-shadow:0 0 10px rgba(47,107,255,.5) !important; }
    </style>
    """, unsafe_allow_html=True)


def empty_state(icon: str, title: str, hint: str = ""):
    """État vide élégant : grande icône, titre, indice — centré dans un cadre discret
    (au lieu d'un simple message brut). Pour les listes sans contenu."""
    st.markdown(f"""
    <div style="text-align:center; padding:2.5rem 1.5rem; margin:.6rem 0;
        background:#F7F9FC; border:1px dashed #D5DCE8; border-radius:18px;">
        <div style="font-size:2.7rem; margin-bottom:.4rem;">{icon}</div>
        <div style="font-family:'Poppins','Inter',sans-serif; font-weight:600; color:#111827;
            font-size:1.1rem;">{title}</div>
        <div style="color:#5B6678; font-size:.92rem; margin:.4rem auto 0; max-width:480px;
            line-height:1.55;">{hint}</div>
    </div>
    """, unsafe_allow_html=True)
