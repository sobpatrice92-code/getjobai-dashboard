"""
simulation_entretien.py — Simulation d'entretien LIVE avec un recruteur IA.

Le candidat passe un vrai entretien : un recruteur RH expert (GPT-4o) pose les
questions une par une (poste/entreprise ciblés, ancré sur le CV + l'offre), le
candidat répond par écrit OU à la voix (Whisper). À la fin : SCORE détaillé +
points forts/faibles + recommandations + réponse modèle. Débrief AUDIO (TTS).

Au-dessus du marché (Final Round AI / Pramp) : 100% personnalisé (CV + vraie
offre), bilingue, voix bidirectionnelle, scorecard multi-critères actionnable.
"""
import json
import os

import httpx
import streamlit as st

try:
    from chatbot import _get_client, _synthese_vocale, _transcrire
except Exception:  # repli si l'import change
    _get_client = _synthese_vocale = _transcrire = None

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = (os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                or os.getenv("SUPABASE_KEY") or "")
_H = {"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY}


def _fetch_job_desc(user_id, poste, entreprise):
    """Description réelle de l'offre (table jobs) pour ancrer l'entretien."""
    if not user_id or not (poste or entreprise):
        return ""
    try:
        r = httpx.get(f"{SUPABASE_URL}/rest/v1/jobs?user_id=eq.{user_id}"
                      "&select=title,company,description&order=scraped_at.desc&limit=60",
                      headers=_H, timeout=12)
        rows = r.json() if r.status_code == 200 else []
        pl, el, best = (poste or "").lower(), (entreprise or "").lower(), ""
        for x in rows:
            t, c = (x.get("title") or "").lower(), (x.get("company") or "").lower()
            if (el and el[:18] in c) or (pl and pl[:18] in t):
                d = x.get("description") or ""
                if len(d) > len(best):
                    best = d
        return best[:2000]
    except Exception:
        return ""


def _fetch_profil(user_id):
    """Récupère le profil (cv_text, province…) pour personnaliser l'entretien."""
    try:
        r = httpx.get(f"{SUPABASE_URL}/rest/v1/users?id=eq.{user_id}"
                      "&select=cv_text,province,location,full_name,sector",
                      headers=_H, timeout=10)
        if r.status_code == 200 and r.json():
            return r.json()[0]
    except Exception:
        pass
    return {}


def _system_prompt(cfg, cv, jd):
    lang = "anglais" if cfg["langue"] == "en" else "français"
    cible = (f"pour le poste « {cfg['poste']} »" + (f" chez « {cfg['entreprise']} »"
             if cfg["entreprise"] else "")) if cfg["poste"] else "pour un poste dans le secteur du candidat"
    niveau = {"Doux": "bienveillant, questions accessibles",
              "Réaliste": "professionnel et exigeant comme un vrai entretien",
              "Exigeant": "très exigeant, questions pièges et de mise en situation"}[cfg["niveau"]]
    return (
        f"Tu es un·e RECRUTEUR·EUSE RH EXPERT·E qui fait passer un entretien d'embauche {cible}. "
        f"Style : {niveau}. Langue de l'entretien : {lang}.\n"
        f"CV DU CANDIDAT :\n{cv[:3000]}\n"
        + (f"DESCRIPTION DU POSTE :\n{jd}\n" if jd else "")
        + "RÈGLES STRICTES :\n"
        "- Pose UNE SEULE question à la fois. Commence par « Parlez-moi de vous ».\n"
        "- Réagis en UNE phrase brève et neutre à la réponse, puis enchaîne la question suivante.\n"
        "- Varie : comportementales (STAR), techniques liées au poste, mise en situation, motivation.\n"
        "- NE donne PAS de feedback détaillé ni de score pendant l'entretien (réservé à la fin).\n"
        f"- Après {cfg['nb']} questions, conclus poliment l'entretien (sans noter)."
    )


def _scorecard(client, cfg, transcript):
    """Demande à GPT-4o une évaluation structurée du candidat (JSON)."""
    lang = "anglais" if cfg["langue"] == "en" else "français"
    prompt = (
        "Tu es un jury RH. Évalue le CANDIDAT (pas le recruteur) à partir de la transcription "
        f"de cet entretien simulé, de façon exigeante mais juste. Réponds en {lang}, UNIQUEMENT "
        "ce JSON :\n"
        '{"global": entier 0-100, "dimensions": {"Pertinence": 0-100, "Structure STAR": 0-100, '
        '"Clarté": 0-100, "Impact chiffré": 0-100, "Communication": 0-100}, '
        '"points_forts": ["2-3"], "points_faibles": ["2-3"], '
        '"recommandations": ["3-5 conseils CONCRETS pour progresser"], '
        '"reponse_modele": "pour la question la MOINS bien répondue : rappelle la question puis '
        'donne une réponse modèle STAR exemplaire"}\n\n'
        f"TRANSCRIPTION :\n{transcript[:6000]}"
    )
    r = client.chat.completions.create(
        model="gpt-4o", temperature=0.2, max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}])
    return json.loads(r.choices[0].message.content)


def _ask_next(client, sys_prompt, messages):
    convo = [{"role": "system", "content": sys_prompt}] + messages
    r = client.chat.completions.create(model="gpt-4o", temperature=0.6,
                                       max_tokens=400, messages=convo)
    return (r.choices[0].message.content or "").strip()


def simulation_entretien_page(user_id, profil):
    st.markdown("## 🎤 Simulation d'entretien (live)")
    st.caption("Un recruteur IA expert vous fait passer un vrai entretien, puis vous note "
               "et vous donne des recommandations. Répondez par écrit ou à la voix.")

    client = _get_client() if _get_client else None
    if client is None:
        st.error("Service IA indisponible (clé OpenAI manquante).")
        return

    if not (profil or {}).get("cv_text"):
        profil = _fetch_profil(user_id)

    S = st.session_state
    # ---------- Écran de configuration ----------
    if not S.get("sim_active"):
        S.pop("sim_score", None)
        with st.form("sim_cfg"):
            c1, c2 = st.columns(2)
            poste = c1.text_input("Poste visé", value=S.get("sim_poste", ""))
            entreprise = c2.text_input("Entreprise (optionnel)", value=S.get("sim_ent", ""))
            c3, c4, c5 = st.columns(3)
            langue = c3.selectbox("Langue", ["fr", "en"], format_func=lambda x: "Français" if x == "fr" else "English")
            niveau = c4.selectbox("Difficulté", ["Doux", "Réaliste", "Exigeant"], index=1)
            nb = c5.slider("Nombre de questions", 4, 12, 6)
            go = st.form_submit_button("🎬 Démarrer l'entretien", type="primary", use_container_width=True)
        if go:
            cv = profil.get("cv_text") or ""
            if not cv:
                st.warning("Ajoutez d'abord votre CV (Paramètres) pour un entretien personnalisé.")
                return
            jd = _fetch_job_desc(user_id, poste, entreprise)
            S["sim_conf"] = {"poste": poste.strip(), "entreprise": entreprise.strip(),
                            "langue": langue, "niveau": niveau, "nb": nb}
            S["sim_sys"] = _system_prompt(S["sim_conf"], cv, jd)
            S["sim_msgs"] = []
            S["sim_qcount"] = 0
            try:
                with st.spinner("Le recruteur prépare l'entretien…"):
                    q = _ask_next(client, S["sim_sys"], [{"role": "user", "content": "Commençons l'entretien."}])
                S["sim_msgs"].append({"role": "assistant", "content": q})
                S["sim_qcount"] = 1
                S["sim_active"] = True
                S["sim_poste"], S["sim_ent"] = poste, entreprise
            except Exception as e:
                S["sim_active"] = False
                st.error(f"❌ Le recruteur IA n'a pas pu démarrer : {str(e)[:180]}\n\n"
                         "Si l'erreur mentionne « API key » / 401 : la clé OPENAI_API_KEY du "
                         "dashboard (Render) doit être mise à jour.")
                return
            st.rerun()
        # Afficher le dernier score s'il existe
        if S.get("sim_score"):
            _afficher_score(client, S["sim_score"])
        return

    # ---------- Entretien en cours ----------
    cfg = S["sim_conf"]
    st.info(f"🎯 Entretien : **{cfg['poste'] or 'poste général'}**"
            + (f" @ **{cfg['entreprise']}**" if cfg["entreprise"] else "")
            + f" • {cfg['niveau']} • question {min(S['sim_qcount'], cfg['nb'])}/{cfg['nb']}")

    for m in S["sim_msgs"]:
        avatar = "🧑‍💼" if m["role"] == "assistant" else "🙂"
        with st.chat_message(m["role"], avatar=avatar):
            st.write(m["content"])

    termine = S["sim_qcount"] > cfg["nb"]
    col_end, _ = st.columns([1, 2])
    if col_end.button("🏁 Terminer & obtenir mon score", use_container_width=True):
        termine = True

    if not termine:
        # Réponse à la voix (optionnel) ou écrite
        rep = None
        if hasattr(st, "audio_input") and _transcrire:
            au = st.audio_input("🎙️ Répondre à la voix (optionnel)")
            if au is not None:
                rep = _transcrire(client, au)
        typed = st.chat_input("Votre réponse…")
        rep = typed or rep
        if rep:
            S["sim_msgs"].append({"role": "user", "content": rep})
            try:
                with st.spinner("…"):
                    q = _ask_next(client, S["sim_sys"], S["sim_msgs"])
                S["sim_msgs"].append({"role": "assistant", "content": q})
                S["sim_qcount"] += 1
            except Exception as e:
                st.error(f"❌ Erreur du recruteur IA : {str(e)[:180]}")
            st.rerun()
    else:
        with st.spinner("Évaluation de votre entretien par le jury IA…"):
            transcript = "\n".join(
                ("RECRUTEUR: " if m["role"] == "assistant" else "CANDIDAT: ") + m["content"]
                for m in S["sim_msgs"])
            try:
                S["sim_score"] = _scorecard(client, cfg, transcript)
            except Exception as e:
                st.error(f"Évaluation impossible : {str(e)[:120]}")
                S["sim_score"] = None
        S["sim_active"] = False
        st.rerun()


def _afficher_score(client, sc):
    st.markdown("### 📊 Votre bilan d'entretien")
    g = int(sc.get("global", 0))
    coul = "#16A34A" if g >= 75 else "#F59E0B" if g >= 55 else "#EF4444"
    st.markdown(
        f"<div style=\"font-family:'Poppins','Inter',sans-serif;font-weight:800;font-size:3.1rem;"
        f"line-height:1;margin:.2rem 0 .4rem;color:{coul};\">{g}"
        f"<span style='font-size:1.4rem;font-weight:700;color:#9AA4B5;margin-left:2px;'>/100</span></div>",
        unsafe_allow_html=True)
    dims = sc.get("dimensions", {})
    if dims:
        cols = st.columns(len(dims))
        for col, (k, v) in zip(cols, dims.items()):
            col.metric(k, f"{int(v)}")
            col.progress(min(int(v), 100) / 100)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### ✅ Points forts")
        for x in sc.get("points_forts", []):
            st.markdown(f"- {x}")
    with c2:
        st.markdown("#### ⚠️ À améliorer")
        for x in sc.get("points_faibles", []):
            st.markdown(f"- {x}")
    st.markdown("#### 🎯 Recommandations pour progresser")
    for x in sc.get("recommandations", []):
        st.markdown(f"- {x}")
    if sc.get("reponse_modele"):
        with st.expander("💡 Réponse modèle (votre question la moins réussie)"):
            st.write(sc["reponse_modele"])
    # Débrief AUDIO (TTS)
    if _synthese_vocale and st.button("🎧 Écouter le débrief audio"):
        txt = (f"Votre score global est de {g} sur 100. "
               + " ".join(sc.get("recommandations", []))[:800])
        audio = _synthese_vocale(client, txt)
        if audio:
            st.audio(audio, format="audio/mp3")
        else:
            st.info("Audio momentanément indisponible.")
    if st.button("🔄 Nouvel entretien", type="primary"):
        st.session_state.pop("sim_score", None)
        st.rerun()
