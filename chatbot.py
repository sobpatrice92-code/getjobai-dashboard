"""
Assistant IA — chatbot d'aide à la recherche d'emploi (GPT-4o)
==============================================================
Lit la clé OpenAI depuis l'env OPENAI_API_KEY (Render).
"""
import os
import streamlit as st

SYSTEM_PROMPT = (
    "Tu es l'assistant IA de GetJobAI, une plateforme d'aide à la recherche "
    "d'emploi au Canada. Tu aides l'utilisateur sur : CV, lettres de motivation, "
    "entretiens, profil LinkedIn, stratégie de candidature, immigration au Canada "
    "(PVT, résidence permanente, Arrima, Entrée Express).\n\n"
    "TU PEUX AUSSI LANCER LES AGENTS pour l'utilisateur via l'outil `lancer_agent`. "
    "Dès qu'il demande une ACTION concrète (ex. « trouve-moi des offres », "
    "« prépare une candidature », « prépare mon entretien chez X pour le poste Y », "
    "« envoie mes candidatures approuvées », « publie mon post »), appelle "
    "`lancer_agent` avec le bon agent (et job_title/company si pertinent), puis "
    "confirme à l'utilisateur en lui disant où voir le résultat dans le Dashboard.\n"
    "Si la demande est vague, pose une question avant de lancer. Pour une simple "
    "question de conseil, réponds normalement sans lancer d'agent.\n"
    "Réponds en français, concret et bienveillant, sans clichés."
)

# Agents que l'assistant peut déclencher (action_type Supabase -> description)
AGENTS_LANCABLES = {
    "job_hunter": "Chercher des offres (LinkedIn, Job Bank, Talent.com) dans la zone de l'utilisateur",
    "chercheur_offres": "Orchestrateur : recherche multi-plateformes diversifiée",
    "coop_hunter": "Chercher des stages / emplois COOP pour étudiants",
    "candidature_prep": "Préparer des candidatures (lettre + CV adapté) à valider",
    "candidature_send": "Postuler aux candidatures APPROUVÉES (Copilote : email au RH)",
    "entretien_prep": "Préparer un guide d'entretien ciblé (utiliser job_title + company)",
    "followup_engine": "Relancer les candidatures sans réponse",
    "networking_agent": "Développer le réseau LinkedIn (messages de connexion)",
    "immigration_advisor": "Conseils d'immigration au Canada",
    "profile_optimizer": "Optimiser le profil LinkedIn",
    "ats_optimizer": "Optimiser le CV pour les ATS",
    "career_strategy_agent": "Élaborer une stratégie de carrière",
    "mail_tracker": "Suivre la boîte mail (réponses recruteurs)",
    "publish_linkedin": "Publier le post LinkedIn en attente",
}

TOOLS = [{
    "type": "function",
    "function": {
        "name": "lancer_agent",
        "description": "Lance un agent GetJobAI (crée une action exécutée en arrière-plan par le worker). À utiliser pour toute ACTION concrète demandée par l'utilisateur.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": list(AGENTS_LANCABLES.keys()),
                    "description": "Agent à lancer. " + " | ".join(
                        f"{k}: {v}" for k, v in AGENTS_LANCABLES.items()),
                },
                "job_title": {"type": "string",
                              "description": "Titre du poste (entretien_prep ou candidature ciblée)"},
                "company": {"type": "string",
                            "description": "Nom de l'entreprise (entretien_prep)"},
            },
            "required": ["agent"],
        },
    },
}]


def _executer_agent(user_id, args):
    """Crée l'action correspondante dans Supabase. Retourne un message pour l'IA."""
    agent = (args or {}).get("agent")
    if agent not in AGENTS_LANCABLES:
        return f"Agent inconnu : {agent}"
    if not user_id:
        return "Utilisateur non identifié — connexion requise."
    params = {k: args[k] for k in ("job_title", "company") if args.get(k)}
    try:
        from database import get_supabase_client
        res = get_supabase_client().create_action(user_id, agent, params)
        if res:
            return (f"Action '{agent}' lancée avec succès" +
                    (f" ({params})" if params else "") +
                    ". Le résultat apparaîtra dans le Dashboard une fois terminé.")
        return f"Échec du lancement de '{agent}'."
    except Exception as e:
        return f"Erreur lancement '{agent}': {str(e)[:120]}"


def _run_assistant(client, user_id, chat_messages):
    """Boucle conversation + appels d'outils (function calling)."""
    import json
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in chat_messages:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            messages.append({"role": m["role"], "content": m["content"]})
    try:
        for _ in range(4):  # au plus 4 tours d'outils
            resp = client.chat.completions.create(
                model="gpt-4o", messages=messages, tools=TOOLS,
                tool_choice="auto", temperature=0.7)
            m = resp.choices[0].message
            if not m.tool_calls:
                return m.content or ""
            messages.append({
                "role": "assistant", "content": m.content or "",
                "tool_calls": [{"id": tc.id, "type": "function",
                                "function": {"name": tc.function.name,
                                             "arguments": tc.function.arguments}}
                               for tc in m.tool_calls]})
            for tc in m.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except Exception:
                    args = {}
                result = _executer_agent(user_id, args)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        return "J'ai lancé les actions demandées — vérifiez le Dashboard."
    except Exception as e:
        return f"Erreur: {e}"


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
    "comment se démarquer dans votre domaine",
    "une leçon concrète apprise dans votre métier",
    "l'importance du réseautage professionnel",
    "les compétences les plus recherchées dans votre secteur",
    "un conseil pratique tiré de votre expérience",
    "l'adaptation et la résilience au travail",
    "pourquoi la formation continue compte dans votre métier",
    "comment la technologie transforme votre profession",
    "un défi récent et comment vous l'avez surmonté",
    "ce qui vous motive vraiment dans votre travail",
]

# Concepts de gestion de projet à mobiliser (posts orientés gestion de projet)
_PM_CONCEPTS = [
    "le triangle portée-coût-délai (triple contrainte)",
    "la structure de découpage du projet (WBS)",
    "le diagramme de Gantt et le chemin critique",
    "la gestion des risques et le registre des risques",
    "la gestion des parties prenantes",
    "les jalons, livrables et le suivi d'avancement",
    "les standards PMBOK et le rôle du PMO",
    "la démarche PMP et le référentiel du PMI",
    "le management de la valeur acquise (EVM)",
    "les méthodes agiles (Scrum) appliquées à la construction",
    "le lean construction et la réduction du gaspillage",
    "le plan de communication projet",
    "le leadership d'équipe entre bureau et terrain",
]

# Angles d'écriture (pour ne JAMAIS écrire deux fois la même chose)
_POST_ANGLES = [
    "raconte une anecdote précise vécue sur un projet",
    "partage une erreur passée et la leçon que tu en as tirée",
    "donne 3 conseils concrets et applicables",
    "compare une bonne et une mauvaise pratique",
    "explique ta méthode étape par étape",
    "pose un problème fréquent puis présente ta solution",
    "prends position sur une idée reçue du métier",
]

# Variations de composition photo (pour ne JAMAIS produire deux fois la même image)
_IMG_COMPOS = [
    "wide establishing shot", "close-up detail shot", "over-the-shoulder perspective",
    "candid mid-action moment", "golden hour natural lighting", "modern bright office interior",
    "active construction site setting", "team collaboration around plans", "low-angle dynamic shot",
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


_EDITO_MAP = {
    "Conseil pratique": "donne des conseils concrets et applicables tout de suite",
    "Question / débat": "lance un débat : pose une question forte et défends un point de vue",
    "Récit d'expérience": "raconte une expérience vécue précise, avec un avant/après",
    "Analyse / réflexion": "propose une analyse réfléchie d'une tendance ou d'un enjeu du métier",
    "Coulisses du métier": "montre les coulisses concrètes de ton métier au quotidien",
    "Motivation / mindset": "partage un état d'esprit, une leçon de persévérance, de façon sincère",
}


def generer_post_linkedin(secteur="", ville="", province="", langue="fr",
                          nom="", theme=None, editos=None, tag_personne=""):
    """Génère un post LinkedIn humanisé (texte seul, sans publication), aligné sur le profil
    de CHAQUE utilisateur. Aucune dépendance navigateur — GPT-4o + passe humanizer.
    secteur : métier/compétences de l'utilisateur. tag_personne : mention optionnelle à taguer.
    editos : lignes éditoriales choisies (on en pioche une au hasard pour varier)."""
    import random
    client = _get_client()
    secteur_in = (secteur or "").strip()
    secteur = secteur_in or "votre domaine professionnel"
    nom = (nom or "").strip() or "un professionnel"
    ville = (ville or "").strip()
    tag_personne = (tag_personne or "").strip()
    if theme is None or not str(theme).strip():
        theme = random.choice(_POST_THEMES)
    loc = f"{ville}{', ' + province if province else ''}".strip(", ") or "votre région"
    is_en = (langue == "en")
    # Hashtags depuis le métier RÉEL de l'utilisateur (vide si non renseigné)
    kws = [k.strip().replace(" ", "") for k in secteur_in.replace("/", ",").split(",")
           if k.strip()][:4] if secteur_in else []
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

    # Concepts de gestion de projet UNIQUEMENT si le métier de l'utilisateur s'y rapporte
    _is_pm = any(w in secteur.lower() for w in
                 ["projet", "gestion", "construction", "génie civil", "chantier", "pmo", "pmp"])
    concepts_line = ""
    if _is_pm:
        concepts_line = ("- Si le thème s'y prête, mobilise NATURELLEMENT 1 ou 2 concepts reconnus "
                         f"de gestion de projet parmi : {', '.join(random.sample(_PM_CONCEPTS, 3))} "
                         "(sans jargon gratuit)\n")
    # Angle = ligne éditoriale choisie par l'utilisateur (variété si plusieurs), sinon aléatoire
    _edito_choices = [_EDITO_MAP[e] for e in (editos or []) if e in _EDITO_MAP]
    angle = random.choice(_edito_choices) if _edito_choices else random.choice(_POST_ANGLES)

    prompt = f"""Tu es {nom}, professionnel basé à {loc}.
Ton métier / tes compétences : {secteur}. Tu écris depuis TON vécu dans CE métier précis.

Thème du post : {theme}
Angle d'écriture (pour varier à chaque fois) : {angle}

LANGUE : {lang_instr}

RÈGLES (STRICTES) :
- Parle à la PREMIÈRE PERSONNE, depuis ton expérience concrète dans TON métier ({secteur})
- N'invente PAS un autre métier — reste strictement dans : {secteur}
{concepts_line}- Ton humain et authentique — JAMAIS corporatif, JAMAIS de cliché
- Détails précis et crédibles propres à ce métier (chiffres, méthodes, outils réels du domaine)
- ORIGINAL : ancre le post dans une situation précise et unique
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
        # Tag optionnel (par utilisateur) — inséré juste avant les hashtags
        if tag_personne and tag_personne not in post:
            lines = post.split("\n")
            idx = next((i for i, l in enumerate(lines) if l.strip().startswith("#")), len(lines))
            lines.insert(idx, f"@{tag_personne}")
            lines.insert(idx + 1, "")
            post = "\n".join(lines)
        # Toujours aérer : une ligne vide entre les blocs (jamais 3+ sauts de suite)
        while "\n\n\n" in post:
            post = post.replace("\n\n\n", "\n\n")
        return post.strip()
    except Exception as e:
        return f"Erreur de génération : {e}"


def _person_desc(genre="", peau=""):
    """Construit la description de la personne (sexe + peau) pour l'image."""
    g = {"Homme": "man", "Femme": "woman"}.get(genre, "person")
    p = {
        "Noire": "Black, dark-skinned",
        "Métisse": "mixed-race, medium-brown skin",
        "Brune / olive": "olive-skinned",
        "Blanche": "white",
    }.get(peau, "")
    return (f"a {p} {g}" if p else f"a {g}").strip()


def _photo_vers_png(photo_b64):
    """Normalise une photo (b64, JPG/PNG) en PNG carré ≤1024 pour l'API images.edit."""
    import base64, io as _io
    from PIL import Image
    img = Image.open(_io.BytesIO(base64.b64decode(photo_b64))).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "ref.png"
    return buf


def generer_image_post(post_text, secteur="", genre="", peau="", photo_b64=""):
    """Génère une image hyper-réaliste (gpt-image-1) alignée sur le contenu du post.
    Si photo_b64 est fourni (post qui met l'utilisateur en avant), l'image S'INSPIRE de
    sa photo de profil (ressemblance). Retourne l'image en base64 (string) ou None."""
    client = _get_client()
    if client is None:
        return None
    person = _person_desc(genre, peau)
    # 1. Dériver une scène visuelle concrète à partir du post
    try:
        desc = client.chat.completions.create(
            model="gpt-4o", max_tokens=120, temperature=0.6,
            messages=[{"role": "user", "content": (
                f"À partir de ce post LinkedIn (profil : {secteur}), décris EN ANGLAIS, en UNE "
                f"phrase, une scène PHOTOGRAPHIQUE hyper-réaliste et professionnelle qui illustre "
                f"le message. La personne principale est {person}. "
                f"AUCUN texte, logo ou mot dans l'image. Décris uniquement la scène "
                f"(lieu, personne, action, ambiance).\n\nPOST:\n{post_text[:700]}"
            )}],
        )
        scene = desc.choices[0].message.content.strip()
    except Exception:
        scene = f"{person}, a professional in a {secteur} work environment"

    import random
    compo = random.choice(_IMG_COMPOS)

    # Cas « me mettre en avant » : image inspirée de la photo de profil
    if photo_b64:
        try:
            ref = _photo_vers_png(photo_b64)
            prompt_edit = (
                f"Hyperrealistic professional photograph featuring THIS exact person. {scene} "
                "Preserve the person's likeness, face and skin tone from the reference photo. "
                "Natural lighting, editorial magazine quality, candid and authentic. "
                "Absolutely NO text, NO words, NO watermark, NO logo."
            )
            r = client.images.edit(model="gpt-image-1", image=ref,
                                    prompt=prompt_edit, size="1024x1024")
            return r.data[0].b64_json
        except Exception:
            pass  # repli : génération normale sans photo

    prompt = (
        f"Hyperrealistic professional photograph, {compo}. {scene} "
        f"The main person in the photo is clearly {person}. "
        "Sharp focus, shallow depth of field, editorial magazine quality, "
        "candid and authentic. Absolutely NO text, NO words, NO letters, NO watermark, NO logo."
    )
    try:
        img = client.images.generate(
            model="gpt-image-1", prompt=prompt, size="1024x1024",
            quality="medium", n=1,
        )
        return img.data[0].b64_json
    except Exception:
        return None


def chatbot_page():
    """Affiche la page de l'assistant IA conversationnel."""
    st.markdown("### 💬 Assistant IA")
    st.caption("Demandez une action (« trouve-moi des offres », « prépare une candidature », "
               "« prépare mon entretien chez X ») ou posez vos questions. L'assistant peut "
               "lancer les agents pour vous.")

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
    user_id = st.session_state.get("user_id")
    prompt = st.chat_input("Demandez une action ou posez une question…")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("…"):
                reply = _run_assistant(client, user_id, st.session_state.chat_messages)
            st.markdown(reply)

        st.session_state.chat_messages.append({"role": "assistant", "content": reply})

    # Bouton effacer
    if st.session_state.chat_messages:
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.chat_messages = []
            st.rerun()
