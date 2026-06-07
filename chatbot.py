"""
Assistant IA — chatbot d'aide à la recherche d'emploi (GPT-4o)
==============================================================
Lit la clé OpenAI depuis l'env OPENAI_API_KEY (Render).
"""
import os
import streamlit as st

SYSTEM_PROMPT = (
    "Tu es l'assistant IA de GetJobAI, une plateforme d'aide à la recherche "
    "d'emploi au Canada. Tu aides l'utilisateur sur : rédaction et amélioration "
    "de CV, lettres de motivation, préparation aux entretiens, optimisation de "
    "profil LinkedIn, stratégie de candidature, et immigration au Canada "
    "(PVT, résidence permanente, Arrima, Entrée Express). "
    "Réponds en français, de façon concrète, structurée et bienveillante. "
    "Écris naturellement, sans clichés ni formules toutes faites."
)


def _get_client():
    """Retourne un client OpenAI ou None si la clé manque."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        try:
            key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            key = None
    if not key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=key)
    except Exception as e:
        st.error(f"Erreur initialisation OpenAI: {e}")
        return None


def generer_message_linkedin(nom, titre, entreprise, secteur="génie civil / construction",
                             nom_user="Patrice"):
    """Génère un message de connexion LinkedIn personnalisé (< 300 caractères)."""
    client = _get_client()
    if client is None:
        return (f"Bonjour {nom.split()[0] if nom else ''}, je suis {nom_user}, "
                f"professionnel en {secteur}. J'aimerais rejoindre votre réseau. Merci !")
    try:
        prompt = (
            f"Rédige un court message d'invitation LinkedIn (MAX 280 caractères, ton "
            f"professionnel et chaleureux, pas de cliché IA) de la part de {nom_user} "
            f"(candidat en {secteur}) vers {nom}"
            + (f", {titre}" if titre else "")
            + (f" chez {entreprise}" if entreprise else "")
            + ". Objectif : se connecter pour des opportunités. Réponds UNIQUEMENT avec le "
            "message, sans guillemets."
        )
        r = client.chat.completions.create(
            model="gpt-4o", temperature=0.7, max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return r.choices[0].message.content.strip()[:290]
    except Exception:
        return (f"Bonjour {nom.split()[0] if nom else ''}, je suis {nom_user}, "
                f"professionnel en {secteur}. J'aimerais échanger avec vous. Merci !")


_POST_THEMES = [
    "comment se démarquer sur le marché du travail canadien",
    "une leçon concrète apprise sur le terrain dans votre domaine",
    "l'importance du réseautage professionnel quand on cherche un emploi",
    "les compétences les plus recherchées dans votre secteur en 2026",
    "un conseil pratique pour réussir un entretien d'embauche",
    "l'adaptation et la résilience dans une recherche d'emploi",
    "pourquoi la formation continue fait la différence dans votre métier",
    "comment la technologie transforme votre profession",
]


def generer_post_linkedin(secteur="génie civil / construction", ville="Ottawa",
                          province="Ontario", langue="fr", nom="Patrice", theme=None):
    """Génère un post LinkedIn humanisé (texte seul, sans publication).
    Aucune dépendance navigateur — GPT-4o uniquement."""
    import random
    client = _get_client()
    if theme is None or not str(theme).strip():
        theme = random.choice(_POST_THEMES)
    loc = f"{ville}{', ' + province if province else ''}".strip(", ")
    is_en = (langue == "en")
    kws = [k.strip().replace(" ", "") for k in secteur.replace("/", ",").split(",") if k.strip()][:4]
    ht_user = " ".join(f"#{k.capitalize()}" for k in kws)
    ht_base = (f"#JobSearch #Professional #{ville.replace(' ', '') or 'Canada'}" if is_en
               else f"#Emploi #Professionnel #{ville.replace(' ', '') or 'Canada'}")
    hashtags = (ht_user + " " + ht_base).strip()
    lang_instr = ("Write the ENTIRE post in natural, professional ENGLISH." if is_en
                  else "Rédige TOUT le post en FRANÇAIS naturel et professionnel.")
    q_instr = ('End with ONE open question starting with "What about you,"' if is_en
               else 'Termine par UNE QUESTION OUVERTE commençant par "Et vous," ou "Selon vous,"')

    if client is None:
        return "⚠️ Configurez OPENAI_API_KEY dans Render pour générer des posts."

    prompt = f"""Tu es {nom}, professionnel actif sur LinkedIn ({secteur}) basé à {loc}, en recherche d'emploi.

Thème du post : {theme}

LANGUE : {lang_instr}

RÈGLES DE FORMAT (STRICTES) :
- Ton humain et authentique — jamais corporatif ni creux
- Détails concrets (chiffres, méthodes, outils réels du secteur)
- CHAQUE idée sur sa PROPRE LIGNE, une ligne vide entre chaque idée
- Maximum 4 idées distinctes — texte aéré, lisible sur mobile
- 1 emoji pertinent par idée clé (maximum 4 emojis au total)
- {q_instr}
- Ligne vide, puis ces hashtags : {hashtags}
- NE JAMAIS mentionner une IA
- INTERDICTION ABSOLUE d'astérisques (*) ou de Markdown — LinkedIn les affiche tels quels
- Retourner UNIQUEMENT le texte du post, rien d'autre"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o", temperature=0.8, max_tokens=450,
            messages=[{"role": "user", "content": prompt}],
        )
        post = resp.choices[0].message.content.strip()
        post = post.replace("**", "").replace("*", "").replace("…", "").replace("...", "")
        return post.strip()
    except Exception as e:
        return f"Erreur de génération : {e}"


def chatbot_page():
    """Affiche la page de l'assistant IA conversationnel."""
    st.markdown("### 💬 Assistant IA")
    st.caption("Posez vos questions sur le CV, les lettres, les entretiens, l'immigration…")

    client = _get_client()
    if client is None:
        st.warning(
            "⚠️ L'assistant n'est pas configuré : ajoutez la variable "
            "`OPENAI_API_KEY` dans Render → Settings → Environment."
        )
        return

    # Historique de conversation
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Afficher l'historique
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Saisie utilisateur
    prompt = st.chat_input("Votre question…")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full = ""
            try:
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                             + st.session_state.chat_messages,
                    stream=True,
                    temperature=0.7,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content or ""
                    full += delta
                    placeholder.markdown(full + "▌")
                placeholder.markdown(full)
            except Exception as e:
                full = f"Erreur: {e}"
                placeholder.error(full)

        st.session_state.chat_messages.append({"role": "assistant", "content": full})

    # Bouton effacer
    if st.session_state.chat_messages:
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.chat_messages = []
            st.rerun()
