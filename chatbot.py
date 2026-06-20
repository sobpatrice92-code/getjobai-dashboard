"""
Assistant IA — chatbot d'aide à la recherche d'emploi (GPT-4o)
==============================================================
Lit la clé OpenAI depuis l'env OPENAI_API_KEY (Render).
"""
import os
import re
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
    "confirme à l'utilisateur en lui disant TOUJOURS et EXPLICITEMENT où voir le "
    "résultat (la page exacte du Dashboard retournée par l'outil) et où suivre "
    "l'avancement (🏠 Dashboard → Actions Récentes).\n"
    "Si la demande est vague, pose une question avant de lancer. Pour une simple "
    "question de conseil, réponds normalement sans lancer d'agent.\n"
    "Réponds en français, concret et bienveillant, sans clichés. Sois CONCIS "
    "(2-4 phrases) car ta réponse peut être lue à voix haute."
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


# Où l'utilisateur retrouve le résultat de chaque agent (page du Dashboard)
AGENT_DESTINATION = {
    "job_hunter": "📋 Offres d'Emploi",
    "chercheur_offres": "📋 Offres d'Emploi (+ 📤 Candidatures à valider)",
    "coop_hunter": "📋 Offres d'Emploi",
    "candidature_prep": "📤 Candidatures (statut « à valider »)",
    "candidature_send": "📤 Candidatures (statut « envoyée ») + une copie dans votre boîte mail",
    "entretien_prep": "📦 Livrables → 🎙️ Préparation entretien",
    "followup_engine": "📤 Candidatures + votre boîte mail (relances)",
    "networking_agent": "🤝 Réseau",
    "immigration_advisor": "📦 Livrables",
    "profile_optimizer": "📦 Livrables",
    "ats_optimizer": "📦 Livrables",
    "career_strategy_agent": "📦 Livrables",
    "mail_tracker": "📤 Candidatures (statuts mis à jour)",
    "publish_linkedin": "votre profil LinkedIn",
}


def _executer_agent(user_id, args):
    """Crée l'action correspondante dans Supabase. Retourne un message pour l'IA."""
    agent = (args or {}).get("agent")
    if agent not in AGENTS_LANCABLES:
        return f"Agent inconnu : {agent}"
    if not user_id:
        return "Utilisateur non identifié — connexion requise."
    params = {k: args[k] for k in ("job_title", "company") if args.get(k)}
    dest = AGENT_DESTINATION.get(agent, "le Dashboard")
    try:
        from database import get_supabase_client
        res = get_supabase_client().create_action(user_id, agent, params)
        if res:
            return (f"Action '{agent}' lancée avec succès" +
                    (f" ({params})" if params else "") +
                    f". IMPORTANT: indique à l'utilisateur que le résultat apparaîtra dans : "
                    f"« {dest} » (et son avancement dans « 🏠 Dashboard → Actions Récentes »).")
        return f"Échec du lancement de '{agent}'."
    except Exception as e:
        return f"Erreur lancement '{agent}': {str(e)[:120]}"


def _synthese_vocale(client, texte):
    """Génère l'audio (MP3) de la réponse via OpenAI TTS. Retourne les bytes ou None."""
    if not texte:
        return None
    try:
        # nettoyer le markdown pour une lecture fluide
        import re
        propre = re.sub(r"[*#`_>\-]{1,}", " ", texte)
        propre = re.sub(r"\s+", " ", propre).strip()[:900]
        r = (_audio_client() or client).audio.speech.create(model="tts-1", voice="alloy", input=propre)
        return r.content
    except Exception:
        return None


def _transcrire(client, audio_file):
    """Transcrit l'audio du micro (WAV) en texte via Whisper. Retourne le texte ou None."""
    try:
        data = audio_file.getvalue() if hasattr(audio_file, "getvalue") else audio_file.read()
        tr = (_audio_client() or client).audio.transcriptions.create(
            model="whisper-1", file=("commande.wav", data), language="fr")
        return (tr.text or "").strip()
    except Exception as e:
        st.error(f"Transcription impossible : {str(e)[:150]}")
        return None


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


def _audio_client():
    """Client OpenAI épinglé sur l'API RÉELLE (api.openai.com). Les endpoints audio
    (/v1/audio/transcriptions, /v1/audio/speech) ne sont PAS routés par un éventuel
    proxy OPENAI_BASE_URL (qui ne gère que le chat) -> on les force en direct."""
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
        return OpenAI(api_key=key, base_url="https://api.openai.com/v1")
    except Exception:
        return None


def _classer_contact(titre):
    """Classe un contact selon son intitulé → adapte l'angle du message + la priorité."""
    t = (titre or "").lower()
    if any(k in t for k in ("recruit", "recruteur", "talent", "human resources", "ressources humaines",
                            "hr ", "rh ", "sourcing", "people ", "acquisition")):
        return "recruteur"
    if any(k in t for k in ("director", "directeur", "directrice", "vp ", " vp", "vice-president", "vice président",
                            "head ", "chef", "lead", "manager", "gestionnaire", "président", "founder",
                            "fondateur", "ceo", "cto", "coo", "owner", "principal")):
        return "decideur"
    if any(k in t for k in ("étudiant", "student", "intern", "stagiaire", "co-op", "coop", "junior",
                            "apprenti", "graduate", "new grad")):
        return "pair"
    return "pro"


_ANGLE = {
    "recruteur": "Destinataire = RECRUTEUR / talent acquisition. Exprime un intérêt clair pour des "
                 "opportunités en {sec}, glisse en 1 phrase ta valeur, et demande à rester en contact "
                 "pour les postes pertinents.",
    "decideur": "Destinataire = DÉCIDEUR / manager. Montre que tu connais son rôle/son entreprise, "
                "exprime ton intérêt pour son équipe/secteur, propose un court échange.",
    "pair": "Destinataire = PAIR (même domaine/niveau). Crée un lien d'entraide, mentionne le point "
            "commun, propose d'échanger des conseils.",
    "pro": "Destinataire = professionnel du secteur. Crée un lien pertinent et propose de rester en contact.",
}


_NOM_GENERIQUE = ("recruteur", "recruiter", "recrutement", "talent", " rh", "hr ", "ressources",
                  "équipe", "team", "service", "—", "•", "department")


def _prenom_utile(nom):
    """Prénom exploitable, ou '' si le contact est générique (« Recruteur — Nokia »)."""
    n = (nom or "").strip()
    if not n or any(g in n.lower() for g in _NOM_GENERIQUE):
        return ""
    p = n.split()[0]
    return p if len(p) >= 2 and p[0].isalpha() else ""


_PLATEFORMES_MSG = ("michael page", "indeed", "linkedin", "jooble", "talent.com",
                    "jobillico", "simplify", "glassdoor", "monster", "jobboom",
                    "neuvoo", "workopolis", "ziprecruiter", "randstad", "adecco",
                    "n/a", "via", "")


def _clean_entreprise(e):
    """Nom d'entreprise propre, ou '' si c'est une plateforme/agence ('via Michael
    Page') — évite la phrase cassée « chez via Michael Page »."""
    e = re.sub(r"^\s*(via|chez|au sein de|@)\s+", "", (e or "").strip(), flags=re.I).strip()
    return "" if e.lower() in _PLATEFORMES_MSG else e


def generer_message_linkedin(nom, titre, entreprise, secteur="votre secteur",
                             nom_user="", objectif="", poste_postule=""):
    """Message LinkedIn ancré (< 300 car). Si `poste_postule` est fourni, le contact
    travaille dans une entreprise où l'utilisateur a POSTULÉ -> on rédige un MESSAGE
    qui le mentionne (pas une invitation générique). Sinon, invitation ciblée selon
    le type de contact. ZÉRO compliment ou fait inventé sur la personne."""
    client = _get_client()
    prenom = _prenom_utile(nom)
    moi = nom_user or "un professionnel"
    ent = _clean_entreprise(entreprise)
    salut = f"Bonjour {prenom}, " if prenom else "Bonjour, "
    if poste_postule:
        _chez = f" chez {ent}" if ent else ""
        fb = (f"{salut}je viens de déposer ma candidature pour le poste de {poste_postule}{_chez}. "
              f"Comme vous y travaillez, je me permets de vous le signaler — votre regard me serait "
              f"précieux. Au plaisir d'échanger, {nom_user}.")
    else:
        fb = (f"{salut}je suis {nom_user}, en {secteur}. Je développe mon réseau dans ce domaine et "
              f"serais heureux d'entrer en contact. Au plaisir, {nom_user}.")
    if client is None:
        return fb[:290]
    try:
        if poste_postule:
            consigne = (
                f"CONTEXTE RÉEL (n'invente RIEN d'autre) : je viens de POSTULER au poste de "
                f"« {poste_postule} »" + (f" chez {ent}" if ent else " dans son entreprise")
                + f", où ce contact travaille" + (f" comme {titre}" if titre else "") + ".\n"
                "Rédige un MESSAGE (PAS une invitation) : signale ma candidature avec tact, demande "
                "poliment son point de vue sur le poste/l'équipe ou s'il/elle peut en toucher un mot, "
                "sans rien exiger ni supplier. Direct, sincère, reconnaissant.")
        else:
            consigne = (
                f"Je suis {moi}, dans le domaine {secteur}.\n"
                + _ANGLE[_classer_contact(titre)].format(sec=secteur) + "\n"
                + ("Ce que tu SAIS du contact : "
                   + (f"poste « {titre} »" if titre else "poste inconnu")
                   + (f", entreprise {ent}" if ent else "") + ". "
                   "Rédige une INVITATION de connexion avec un motif clair et pertinent."))
        ouverture = (f"Commence par « Bonjour {prenom}, »." if prenom
                     else "Prénom INCONNU : commence simplement par « Bonjour, » (sans nom).")
        prompt = (
            "Tu es un expert RH en recrutement et en mise en relation. Rédige UN message LinkedIn en "
            "français, MAX 280 caractères, qui sonne HUMAIN, sincère et naturel.\n"
            + consigne + "\n"
            "INTERDITS ABSOLUS : n'invente AUCUN compliment ni fait sur la personne (jamais « votre "
            "travail m'inspire », « approche innovante », « j'admire votre parcours » — tu ne connais "
            "PAS son travail) ; pas de superlatifs ni de clichés IA ; pas d'astérisques ; AUCUN crochet "
            "[Nom] ni placeholder ; n'écris jamais « chez » sans nom d'entreprise. "
            + ouverture + " "
            + (f"Objectif : {objectif}. " if objectif else "")
            + f"Signe par « {nom_user} ». Réponds UNIQUEMENT par le message, sans guillemets."
        )
        r = client.chat.completions.create(
            model="gpt-4o", temperature=0.6, max_tokens=170,
            messages=[{"role": "user", "content": prompt}],
        )
        msg = (r.choices[0].message.content or "").strip().strip('"').strip()
        # Filets de sécurité : crochets résiduels, « chez » orphelin, espaces
        msg = re.sub(r"\s*\[[^\]]*\]", "", msg)
        msg = re.sub(r"\bchez\s*(?=[.,;:!?]|$)", "", msg, flags=re.I)
        msg = re.sub(r"\s{2,}", " ", msg).strip()
        return (msg or fb)[:290]
    except Exception:
        return fb[:290]


def prioriser_contacts(contacts):
    """Trie les contacts par PRIORITÉ de prise de contact (les plus utiles d'abord)
    et annote chacun de _type et _priorite. Performant : 100% heuristique, zéro appel IA."""
    poids = {"recruteur": 100, "decideur": 80, "pair": 55, "pro": 45}
    for c in contacts:
        typ = _classer_contact(c.get("titre", ""))
        score = poids.get(typ, 45)
        if (c.get("statut") or "a_contacter") != "contacte":
            score += 10  # à contacter en priorité
        if (c.get("entreprise") or "").strip():
            score += 5
        c["_type"] = typ
        c["_priorite"] = score
    return sorted(contacts, key=lambda c: c.get("_priorite", 0), reverse=True)


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

# HOOKS — la 1ère ligne est LE levier #1 sur LinkedIn (arrêter le défilement).
_HOOKS = [
    "une affirmation audacieuse, à contre-courant du consensus",
    "un résultat chiffré qui surprend (ex : « J'ai réduit X de 40 % en 3 mois »)",
    "une mini-scène qui démarre en plein milieu de l'action",
    "une erreur coûteuse que tu as commise (et assumée)",
    "une vérité que peu osent dire à voix haute dans ton métier",
    "une question directe qui met le lecteur face à lui-même",
    "un avant/après frappant en une phrase",
    "une croyance répandue que tu démontes en 3 mots",
]

# STRUCTURES de post éprouvées (variété pour ne jamais se répéter).
_POST_FORMATS = [
    "HISTOIRE : situation → tension → ce que tu as fait → résultat → leçon",
    "LEÇONS : 3 à 4 leçons courtes, numérotées et concrètes",
    "CONTRE-PIED : l'idée reçue → pourquoi elle est fausse → quoi faire à la place",
    "MÉTHODE : le problème → ta méthode en étapes claires → le bénéfice",
    "AVANT / APRÈS : où tu en étais → le déclic → où tu en es",
    "ERREUR → LEÇON : l'erreur → ses conséquences → ce que tu fais autrement aujourd'hui",
]

# Variations de composition photo (pour ne JAMAIS produire deux fois la même image)
_IMG_COMPOS = [
    "wide establishing shot", "close-up detail shot", "over-the-shoulder perspective",
    "candid mid-action moment", "golden hour natural lighting", "modern bright office interior",
    "active construction site setting", "team collaboration around plans", "low-angle dynamic shot",
]

# Clichés IA / formules creuses à bannir (cœur de la 'compétence humanizer')
_CLICHES_BANNIS = (
    "dans un monde où, à l'ère du numérique, je suis ravi/heureux/fier de, force est de constater, "
    "passionné par, n'hésitez pas, en tant que professionnel, plongeons dans, "
    "il est important de noter, au cœur de, véritable atout, game changer, "
    "repousser les limites, ensemble nous pouvons, et ce n'est que le début, "
    "le secret c'est, voici ce que j'ai appris, spoiler, croyez-moi, la vérité c'est que, "
    "ça m'a fait réfléchir, et si je vous disais que, laissez-moi vous raconter, "
    "changer la donne, faire la différence, sortir de sa zone de confort, "
    "chaque jour est une opportunité, le pouvoir de, libérer son potentiel"
)


def _humaniser_texte(client, texte, is_en=False):
    """Passe 'humanizer' : retire les clichés IA et rend le texte naturel.
    Conserve hashtags, chiffres et question finale. Interdit astérisques et '...'."""
    if client is None:
        return texte
    consigne = (
        ("Rewrite this LinkedIn post so it sounds 100% human and authentic, written by a real "
         "professional from personal experience. Remove every AI cliché and empty corporate phrase. "
         "KEEP the punchy first line (the hook) strong and intact. "
         "Keep the meaning, concrete numbers, the hashtags and the final question. "
         "FORBIDDEN: asterisks, markdown, ellipses (...). Reply ONLY with the rewritten post."
         if is_en else
         "Réécris ce post LinkedIn pour qu'il sonne 100% humain et authentique, comme écrit par un "
         "vrai professionnel à partir de son vécu, à l'oral, comme s'il parlait à un collègue. "
         "Supprime TOUT cliché IA et toute formule corporate "
         f"creuse (ex : {_CLICHES_BANNIS}). "
         "Remplace l'abstrait par du concret : préfère un fait précis à une généralité, un verbe "
         "simple à un mot ronflant. Phrases COURTES. Pas de leçon de vie plaquée à la fin. "
         "Pas de ton « influenceur » ni de fausse vulnérabilité théâtrale. "
         "GARDE la PREMIÈRE LIGNE (le hook) courte et percutante, "
         "intacte. Garde le sens, les chiffres concrets, les hashtags et la "
         "question finale. GARDE une mise en page TRÈS AÉRÉE : chaque idée sur sa ligne, une LIGNE "
         "VIDE entre chaque idée. INTERDIT : astérisques, markdown, points de suspension (...). "
         "Réponds UNIQUEMENT avec le post réécrit.")
    )
    try:
        r = client.chat.completions.create(
            model="gpt-4o", temperature=0.7, max_tokens=1200,
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
                          nom="", theme=None, editos=None, tag_personne="", eviter=None):
    """Génère un post LinkedIn humanisé (texte seul, sans publication), aligné sur le profil
    de CHAQUE utilisateur. Aucune dépendance navigateur — GPT-4o + passe humanizer.
    secteur : métier/compétences de l'utilisateur. tag_personne : mention optionnelle à taguer.
    editos : lignes éditoriales choisies (on en pioche une au hasard pour varier).
    eviter : liste des textes des derniers posts — on interdit d'en réutiliser ouvertures/angles."""
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
    # Hashtags de base ROTATIFS (anti-répétition : ne plus toujours #Emploi #Professionnel)
    _ht_pool = (["#Career", "#Hiring", "#Jobs", "#Growth", "#Networking", "#Leadership",
                 "#Opportunity", "#WorkLife", "#Skills"] if is_en else
                ["#Emploi", "#Carriere", "#Recrutement", "#Reseautage", "#Metier",
                 "#Competences", "#Opportunite", "#Croissance", "#Travail"])
    ht_base = " ".join(random.sample(_ht_pool, 2)) + f" #{ville.replace(' ', '') or 'Canada'}"
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
    hook = random.choice(_HOOKS)
    fmt = random.choice(_POST_FORMATS)

    # ANTI-RÉPÉTITION : on montre les derniers posts et on INTERDIT d'en reprendre l'ouverture
    eviter_block = ""
    recents = [t for t in (eviter or []) if (t or "").strip()][:6]
    if recents:
        apercus = []
        for t in recents:
            premiere = next((l.strip() for l in str(t).splitlines() if l.strip()), "")
            if premiere:
                apercus.append(f"  • « {premiere[:90]} »")
        if apercus:
            eviter_block = (
                "\nPOSTS DÉJÀ PUBLIÉS PAR L'AUTEUR (tu dois être TOTALEMENT différent) :\n"
                + "\n".join(apercus)
                + "\nINTERDIT de réutiliser ces premières lignes, le même angle, la même "
                  "structure ou les mêmes tournures. Choisis un angle, un exemple et une "
                  "ouverture NEUFS. Si un thème a déjà été traité, prends-le sous un autre jour.\n")

    prompt = f"""Tu es {nom}, professionnel basé à {loc}.
Ton métier / tes compétences : {secteur}. Tu écris depuis TON vécu dans CE métier précis.

Thème du post : {theme}
Angle d'écriture (pour varier à chaque fois) : {angle}
Structure du post : {fmt}
{eviter_block}
LANGUE : {lang_instr}

RÈGLES (STRICTES) :
- ACCROCHE (PRIORITÉ #1) : la TOUTE PREMIÈRE LIGNE est un HOOK court et percutant qui arrête
  le défilement — type : {hook}. Le lecteur doit vouloir cliquer « voir plus ».
  INTERDIT les ouvertures molles (« Aujourd'hui je veux parler de… », « En tant que… »).
- Ligne 2 = une respiration courte qui relance, AVANT de dérouler le corps.
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
            model="gpt-4o", temperature=0.8, max_tokens=1200,
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
    # 1. Dériver une scène + décider si l'auteur est MIS EN AVANT (portrait/lumière)
    portrait = bool(photo_b64)
    try:
        import json as _json
        desc = client.with_options(timeout=30.0).chat.completions.create(
            model="gpt-4o", max_tokens=180, temperature=0.5,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": (
                f"À partir de ce post LinkedIn (profil : {secteur}), renvoie UNIQUEMENT ce JSON :\n"
                '{"scene": "UNE phrase EN ANGLAIS décrivant une scène photographique hyper-réaliste '
                'et professionnelle qui illustre le message (lieu, action, ambiance), sans aucun '
                'texte/logo/marque/enseigne", '
                '"portrait": true ou false (true SI le post met PERSONNELLEMENT l\'auteur en avant '
                '— récit personnel, mise en lumière, prise de parole, portrait — où il doit être le '
                'SUJET CENTRAL et reconnaissable ; false si c\'est un concept/scène générale)}\n\n'
                f"POST:\n{post_text[:700]}"
            )}],
        )
        obj = _json.loads(desc.choices[0].message.content)
        scene = (obj.get("scene") or "").strip() or f"{person} in a {secteur} work environment"
        portrait = bool(obj.get("portrait"))
    except Exception:
        scene = f"{person}, a professional in a {secteur} work environment"

    import random
    compo = "editorial head-and-shoulders portrait, subject looking toward camera" if portrait \
        else random.choice(_IMG_COMPOS)
    _REAL = ("Shot on 85mm f/1.8, natural light, ultra-detailed realistic skin texture, "
             "sharp focus, shallow depth of field, editorial magazine quality, candid and authentic.")
    _NOTXT = ("Absolutely NO text, letters, numbers, words, watermark, logo or brand anywhere "
              "— including on hard hats, helmets, safety vests, clothing, badges, walls, screens, "
              "banners or signs. Plain, unbranded equipment and clothing.")

    # Cas « me mettre en avant » : image qui RESSEMBLE à l'utilisateur (sa photo de profil)
    if photo_b64:
        try:
            ref = _photo_vers_png(photo_b64)
            cadrage = ("A clean, flattering editorial PORTRAIT of THIS exact person as the central "
                       "subject. " if portrait else
                       "Hyperrealistic professional photograph featuring THIS exact person. ")
            prompt_edit = (
                f"{cadrage}{scene} "
                "Faithfully PRESERVE the person's exact likeness: same face, facial features, skin "
                "tone, hair and apparent age as the reference photo. " + _REAL + " " + _NOTXT
            )
            r = client.with_options(timeout=110.0).images.edit(
                model="gpt-image-1", image=ref, prompt=prompt_edit,
                size="1024x1024", quality="medium")
            return r.data[0].b64_json
        except Exception:
            pass  # repli : génération normale sans photo

    prompt = (
        f"Hyperrealistic professional photograph, {compo}. {scene} "
        f"The main person in the photo is clearly {person}. " + _REAL + " " + _NOTXT
    )
    try:
        img = client.with_options(timeout=110.0).images.generate(
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

    def _capter_audio(widget):
        """Transcrit un nouvel enregistrement (évite de retraiter le même)."""
        if widget is None:
            return None
        sig = (getattr(widget, "size", None), getattr(widget, "name", ""))
        if st.session_state.get("_last_audio_sig") == sig:
            return None
        st.session_state["_last_audio_sig"] = sig
        with st.spinner("Transcription de votre voix…"):
            return _transcrire(client, widget)

    # Barre d'outils : 🎤 Parler (popover) + 🔊 Réponse vocale
    voice_prompt = None
    c_mic, c_voix = st.columns([1, 1])
    with c_mic:
        if hasattr(st, "popover") and hasattr(st, "audio_input"):
            with st.popover("🎤 Parler", use_container_width=True):
                st.caption("Parlez votre demande, puis **arrêtez** l'enregistrement.")
                voice_prompt = _capter_audio(
                    st.audio_input("Commande vocale", label_visibility="collapsed"))
        elif hasattr(st, "audio_input"):
            voice_prompt = _capter_audio(st.audio_input("🎤 Commande vocale"))
    with c_voix:
        st.session_state["_voice_reply"] = st.toggle(
            "🔊 Réponse vocale", value=st.session_state.get("_voice_reply", False),
            help="L'assistant lit sa réponse à voix haute.")

    typed = st.chat_input("Demandez une action ou posez une question…")
    prompt = typed or voice_prompt
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("…"):
                reply = _run_assistant(client, user_id, st.session_state.chat_messages)
            st.markdown(reply)
            # 🔊 Lire la réponse à voix haute si activé
            if st.session_state.get("_voice_reply"):
                audio_bytes = _synthese_vocale(client, reply)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        st.session_state.chat_messages.append({"role": "assistant", "content": reply})

    # Bouton effacer
    if st.session_state.chat_messages:
        if st.button("🗑️ Effacer la conversation"):
            st.session_state.chat_messages = []
            st.rerun()
