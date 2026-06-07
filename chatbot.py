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
    "la coordination de chantier et la gestion des imprévus au quotidien",
    "la planification et le respect des délais sur un projet de construction",
    "la gestion des parties prenantes (clients, sous-traitants, équipes)",
    "l'estimation et le contrôle des coûts sur un projet",
    "la sécurité et la qualité comme priorités sur un chantier",
    "la communication entre le bureau et le terrain",
    "ce que la gestion de projet m'a appris sur le leadership",
    "comment se démarquer dans le génie civil au Canada",
    "l'apport des outils numériques (MS Project, BIM, AutoCAD) en gestion de projet",
    "comment anticiper et résoudre un retard sur un chantier",
]

# Clichés IA / formules creuses à bannir (cœur de la 'compétence humanizer')
_CLICHES_BANNIS = (
    "dans un monde où, à l'ère du numérique, je suis ravi/heureux de, force est de constater, "
    "passionné par, n'hésitez pas, en tant que professionnel, plongeons dans, "
    "il est important de noter, au cœur de, véritable atout, game changer, "
    "repousser les limites, ensemble, nous pouvons"
)


def _humaniser_texte(client, texte, is_en=False):
    """Passe 'humanizer' : retire les clichés IA et rend le texte naturel.
    Conserve hashtags, chiffres et question finale. Interdit astérisques et '...'."""
    if client is None:
        return texte
    consigne = (
        ("Rewrite this LinkedIn post so it sounds 100% human and authentic, written by a real "
         "professional from personal experience. Remove every AI cliché and empty corporate phrase. "
         "Keep the meaning, concrete numbers, the hashtags and the final question. "
         "FORBIDDEN: asterisks, markdown, ellipses (...). Reply ONLY with the rewritten post."
         if is_en else
         "Réécris ce post LinkedIn pour qu'il sonne 100% humain et authentique, comme écrit par un "
         "vrai professionnel à partir de son vécu. Supprime TOUT cliché IA et toute formule corporate "
         f"creuse (ex : {_CLICHES_BANNIS}). Garde le sens, les chiffres concrets, les hashtags et la "
         "question finale. GARDE une mise en page TRÈS AÉRÉE : chaque idée sur sa ligne, une LIGNE "
         "VIDE entre chaque idée. INTERDIT : astérisques, markdown, points de suspension (...). "
         "Réponds UNIQUEMENT avec le post réécrit.")
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4o", temperature=0.7, max_tokens=550,
            messages=[{"role": "user", "content": consigne + "\n\nPOST :\n" + texte}],
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return texte


def generer_post_linkedin(secteur="génie civil, gestion de projet, chargé de projet, construction",
                          ville="Ottawa", province="Ontario", langue="fr",
                          nom="Patrice", theme=None):
    """Génère un post LinkedIn humanisé (texte seul, sans publication), aligné sur le profil.
    Aucune dépendance navigateur — GPT-4o + passe humanizer."""
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
    q_instr = ('End with ONE open question starting with "What about you," or "In your experience,"'
               if is_en else
               'Termine par UNE QUESTION OUVERTE commençant par "Et vous," ou "Selon vous,"')

    if client is None:
        return "⚠️ Configurez OPENAI_API_KEY dans Render pour générer des posts."

    prompt = f"""Tu es {nom}, professionnel basé à {loc}, en recherche d'emploi.
Ton profil couvre : {secteur}. Tu parles depuis TON vécu sur le terrain et en gestion de projet.

Thème du post : {theme}

LANGUE : {lang_instr}

RÈGLES (STRICTES) :
- Parle à la PREMIÈRE PERSONNE, depuis ton expérience concrète (chantier ET bureau)
- Aligne le contenu sur tes compétences réelles : {secteur}
- Ton humain et authentique — JAMAIS corporatif, JAMAIS de cliché
- Détails précis : chiffres, méthodes, outils réels (MS Project, AutoCAD, échéanciers, devis…)
- CHAQUE idée sur sa PROPRE LIGNE, une ligne vide entre chaque idée
- Maximum 4 idées distinctes — texte aéré, lisible sur mobile
- 1 emoji pertinent par idée clé (maximum 4 emojis au total)
- {q_instr}
- Ligne vide, puis ces hashtags : {hashtags}
- NE JAMAIS mentionner une IA
- INTERDICTION ABSOLUE : astérisques (*), Markdown, points de suspension (...)
- Retourne UNIQUEMENT le texte du post"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o", temperature=0.8, max_tokens=450,
            messages=[{"role": "user", "content": prompt}],
        )
        post = resp.choices[0].message.content.strip()
        # Passe humanizer (de-cliché) puis nettoyage format
        post = _humaniser_texte(client, post, is_en=is_en)
        post = post.replace("**", "").replace("*", "").replace("…", "")
        while "..." in post:
            post = post.replace("...", "")
        # Filet : garantir les hashtags
        if "#" not in post:
            post = post.rstrip() + "\n\n" + hashtags
        # Toujours taguer Fredy Beukam (inséré juste avant les hashtags)
        if "Fredy Beukam" not in post:
            lines = post.split("\n")
            idx = next((i for i, l in enumerate(lines) if l.strip().startswith("#")), len(lines))
            lines.insert(idx, "@Fredy Beukam")
            lines.insert(idx + 1, "")
            post = "\n".join(lines)
        # Toujours aérer : une ligne vide entre les blocs (jamais 3+ sauts de suite)
        while "\n\n\n" in post:
            post = post.replace("\n\n\n", "\n\n")
        return post.strip()
    except Exception as e:
        return f"Erreur de génération : {e}"


def generer_image_post(post_text, secteur="génie civil / construction"):
    """Génère une image hyper-réaliste (DALL-E 3) alignée sur le contenu du post.
    Retourne une URL d'image (valide ~1h) ou None."""
    client = _get_client()
    if client is None:
        return None
    # 1. Dériver une scène visuelle concrète à partir du post
    try:
        desc = client.chat.completions.create(
            model="gpt-4o", max_tokens=120, temperature=0.6,
            messages=[{"role": "user", "content": (
                f"À partir de ce post LinkedIn (secteur : {secteur}), décris EN ANGLAIS, en UNE "
                f"phrase, une scène PHOTOGRAPHIQUE hyper-réaliste et professionnelle qui illustre "
                f"le message. AUCUN texte, logo ou mot dans l'image. Décris uniquement la scène "
                f"(lieu, personne, action, ambiance).\n\nPOST:\n{post_text[:700]}"
            )}],
        )
        scene = desc.choices[0].message.content.strip()
    except Exception:
        scene = f"a professional {secteur} work environment"

    prompt = (
        f"Hyperrealistic professional photograph. {scene} "
        "Natural lighting, sharp focus, shallow depth of field, editorial magazine quality, "
        "candid and authentic. Absolutely NO text, NO words, NO letters, NO watermark, NO logo."
    )
    try:
        img = client.images.generate(
            model="dall-e-3", prompt=prompt, size="1024x1024",
            quality="standard", n=1,
        )
        return img.data[0].url
    except Exception:
        return None


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
