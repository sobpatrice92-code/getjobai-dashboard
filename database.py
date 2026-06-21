"""
Database Module - Supabase Connection
======================================
Gestion de la connexion à Supabase et requêtes
"""
import os
import streamlit as st
from typing import List, Dict, Optional

# Utiliser httpx pour éviter les dépendances supabase-py
import httpx


class SupabaseClient:
    """Client Supabase utilisant l'API REST"""

    def __init__(self):
        # Priorité aux variables d'environnement (Render). st.secrets plante
        # si aucun secrets.toml n'existe → on l'encapsule dans un try/except.
        self.url = os.getenv("SUPABASE_URL")
        # Clé SERVICE en priorité (contourne RLS / privilèges colonnes), repli sur
        # anon. Sans SUPABASE_SERVICE_KEY définie → comportement identique à avant.
        self.key = (os.getenv("SUPABASE_SERVICE_KEY")
                    or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                    or os.getenv("SUPABASE_KEY"))

        if not self.url or not self.key:
            try:
                self.url = self.url or st.secrets.get("SUPABASE_URL")
                self.key = (self.key or st.secrets.get("SUPABASE_SERVICE_KEY")
                            or st.secrets.get("SUPABASE_SERVICE_ROLE_KEY")
                            or st.secrets.get("SUPABASE_KEY"))
            except Exception:
                pass

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL et SUPABASE_KEY requis!")

        # Nettoyer tout espace/saut de ligne (erreurs de copier-coller dans Render).
        # Un JWT et une URL n'ont jamais d'espaces internes.
        self.url = "".join(self.url.split())
        self.key = "".join(self.key.split())

        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json"
        }

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Récupérer utilisateur par email"""
        url = f"{self.url}/rest/v1/users?email=eq.{email}&select=*"
        try:
            response = httpx.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200 and response.json():
                return response.json()[0]
        except Exception as e:
            st.error(f"Erreur get_user: {e}")
        return None

    def get_all_users(self) -> List[Dict]:
        """Récupérer tous les utilisateurs (champs non-sensibles uniquement, pour admin)"""
        # On ne sélectionne JAMAIS les mots de passe / clés / cookies
        fields = "id,email,full_name,nom_complet,ville,province,is_admin,is_active,is_whitelisted,created_at,last_active"
        url = f"{self.url}/rest/v1/users?select={fields}&order=created_at.asc"
        try:
            response = httpx.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Erreur get_all_users: {e}")
        return []

    # ------------------------------------------------------------------
    # LIVRABLES (résultats de tous les agents)
    # ------------------------------------------------------------------
    def get_user_cv(self, user_id: str) -> str:
        """Récupérer le texte du CV de l'utilisateur (colonne cv_text)."""
        url = f"{self.url}/rest/v1/users?id=eq.{user_id}&select=cv_text,cv_filename"
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200 and r.json():
                return r.json()[0].get("cv_text") or ""
        except Exception:
            pass
        return ""

    def get_candidatures_list(self, user_id: str, limit: int = 200) -> List[Dict]:
        """Liste détaillée des candidatures d'un utilisateur."""
        url = (f"{self.url}/rest/v1/candidatures?user_id=eq.{user_id}"
               f"&order=created_at.desc&limit={limit}")
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            st.error(f"Erreur get_candidatures_list: {e}")
        return []

    def update_candidature_status(self, cand_id: str, status: str) -> bool:
        """Changer le statut d'une candidature (en_attente -> validee / refus)."""
        url = f"{self.url}/rest/v1/candidatures?id=eq.{cand_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.patch(url, headers=h, json={"status": status}, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False

    def delete_candidature(self, cand_id: str) -> bool:
        url = f"{self.url}/rest/v1/candidatures?id=eq.{cand_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.delete(url, headers=h, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False

    def vider_table(self, table: str, user_id: str) -> int:
        """Supprime TOUTES les lignes de `table` appartenant à user_id (remise à 0).
        Allowlist stricte : impossible de viser une table non prévue.
        Retourne le nombre de lignes supprimées."""
        if table not in ("jobs", "candidatures", "contacts_reseau", "livrables"):
            return 0
        url = f"{self.url}/rest/v1/{table}?user_id=eq.{user_id}"
        h = {**self.headers, "Prefer": "count=exact, return=minimal"}
        try:
            r = httpx.delete(url, headers=h, timeout=20)
            if r.status_code in (200, 204):
                cr = r.headers.get("content-range", "")
                return int(cr.split("/")[-1]) if "/" in cr else 0
        except Exception as e:
            st.error(f"Erreur remise à zéro ({table}): {e}")
        return 0

    def get_contacts_reseau(self, user_id: str, limit: int = 200) -> List[Dict]:
        """Contacts réseau LinkedIn à contacter (mode semi-auto)."""
        url = (f"{self.url}/rest/v1/contacts_reseau?user_id=eq.{user_id}"
               f"&order=created_at.desc&limit={limit}")
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            st.error(f"Erreur get_contacts_reseau: {e}")
        return []

    def create_post_linkedin(self, user_id: str, texte: str, image_b64: str = "") -> bool:
        """Enregistre un post à publier via l'extension Chrome (statut pending)."""
        url = f"{self.url}/rest/v1/posts_linkedin"
        h = {**self.headers, "Content-Type": "application/json", "Prefer": "return=minimal"}
        body = {"user_id": user_id, "texte": texte, "image_b64": image_b64 or "",
                "statut": "pending"}
        try:
            r = httpx.post(url, headers=h, json=body, timeout=15)
            if r.status_code in (200, 201, 204):
                return True
            st.error(f"Erreur create_post_linkedin: {r.status_code} {r.text[:200]}")
            return False
        except Exception as e:
            st.error(f"Erreur create_post_linkedin: {e}")
            return False

    def enqueue_video_job(self, user_id: str, post_text: str, image_b64: str = "",
                          langue: str = "fr"):
        """Met une tâche de rendu vidéo en file (table actions). Le WORKER LOCAL
        (agents/video_post.py) la rend hors de l'instance web → zéro mémoire ici.
        Retourne l'id de l'action, ou None."""
        url = f"{self.url}/rest/v1/actions"
        h = {**self.headers, "Prefer": "return=representation"}
        body = {"user_id": user_id, "action_type": "video_post",
                "parameters": {"post_text": post_text, "image_b64": image_b64 or "",
                               "langue": langue},
                "status": "pending", "priority": 4}
        try:
            r = httpx.post(url, headers=h, json=body, timeout=20)
            if r.status_code in (200, 201) and r.json():
                return r.json()[0].get("id")
        except Exception as e:
            st.error(f"Erreur enqueue_video_job: {e}")
        return None

    def get_video_job(self, action_id: str) -> dict:
        """Lit l'état d'une tâche vidéo : status + video_b64 (résultat) + error."""
        url = (f"{self.url}/rest/v1/actions?id=eq.{action_id}"
               "&select=status,video_b64,error")
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200 and r.json():
                return r.json()[0]
        except Exception:
            pass
        return {}

    def get_recent_posts(self, user_id: str, limit: int = 6) -> list:
        """Retourne le texte des derniers posts de l'utilisateur (anti-répétition).
        Sert à interdire au générateur de réutiliser les mêmes ouvertures/angles."""
        url = (f"{self.url}/rest/v1/posts_linkedin?user_id=eq.{user_id}"
               f"&statut=neq.debug&select=texte&order=created_at.desc&limit={limit}")
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                return [row.get("texte", "") for row in r.json() if row.get("texte")]
        except Exception:
            pass
        return []

    def create_scheduled_post(self, user_id: str, texte: str, image_b64: str,
                              scheduled_at_iso: str) -> bool:
        """Enregistre un post à publier AUTOMATIQUEMENT à une date/heure (UTC ISO)
        via l'API LinkedIn (statut 'scheduled' → le worker le publie le moment venu)."""
        url = f"{self.url}/rest/v1/posts_linkedin"
        h = {**self.headers, "Content-Type": "application/json", "Prefer": "return=minimal"}
        body = {"user_id": user_id, "texte": texte, "image_b64": image_b64 or "",
                "statut": "scheduled", "scheduled_at": scheduled_at_iso}
        try:
            r = httpx.post(url, headers=h, json=body, timeout=15)
            if r.status_code in (200, 201, 204):
                return True
            st.error(f"Erreur create_scheduled_post: {r.status_code} {r.text[:200]}")
            return False
        except Exception as e:
            st.error(f"Erreur create_scheduled_post: {e}")
            return False

    def create_scheduled_video_post(self, user_id: str, texte: str, video_b64: str,
                                    scheduled_at_iso: str) -> bool:
        """Planifie une VIDÉO déjà rendue : la stocke (posts_linkedin.video_b64) avec
        scheduled_at. Le publieur cloud la postera via la Videos API le moment venu."""
        url = f"{self.url}/rest/v1/posts_linkedin"
        h = {**self.headers, "Content-Type": "application/json", "Prefer": "return=minimal"}
        body = {"user_id": user_id, "texte": texte, "video_b64": video_b64 or "",
                "image_b64": "", "statut": "scheduled", "scheduled_at": scheduled_at_iso}
        try:
            r = httpx.post(url, headers=h, json=body, timeout=30)
            if r.status_code in (200, 201, 204):
                return True
            st.error(f"Erreur create_scheduled_video_post: {r.status_code} {r.text[:200]}")
            return False
        except Exception as e:
            st.error(f"Erreur create_scheduled_video_post: {e}")
            return False

    def update_contact_message(self, contact_id: str, message: str) -> bool:
        url = f"{self.url}/rest/v1/contacts_reseau?id=eq.{contact_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.patch(url, headers=h, json={"message": message}, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False

    def update_contact_reseau(self, contact_id: str, statut: str) -> bool:
        url = f"{self.url}/rest/v1/contacts_reseau?id=eq.{contact_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.patch(url, headers=h, json={"statut": statut}, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False

    def delete_contact_reseau(self, contact_id: str) -> bool:
        url = f"{self.url}/rest/v1/contacts_reseau?id=eq.{contact_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.delete(url, headers=h, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False

    def get_livrables(self, user_id: str, limit: int = 100) -> List[Dict]:
        """Récupérer les livrables (résultats d'agents) d'un utilisateur."""
        url = (f"{self.url}/rest/v1/livrables?user_id=eq.{user_id}"
               f"&order=created_at.desc&limit={limit}")
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            st.error(f"Erreur get_livrables: {e}")
        return []

    # ------------------------------------------------------------------
    # PLANIFICATEUR (table schedules)
    # ------------------------------------------------------------------
    def get_schedules(self, user_id: str) -> List[Dict]:
        """Récupérer les planifications d'un utilisateur."""
        url = f"{self.url}/rest/v1/schedules?user_id=eq.{user_id}&order=run_time.asc"
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            st.error(f"Erreur get_schedules: {e}")
        return []

    def create_schedule(self, user_id: str, agent_type: str, run_time: str,
                        days: str = "0,1,2,3,4,5,6") -> bool:
        """Créer une planification (run_time 'HH:MM', days = jours weekday séparés par virgule)."""
        url = f"{self.url}/rest/v1/schedules"
        data = {
            "user_id": user_id,
            "agent_type": agent_type,
            "run_time": run_time,
            "days": days,
            "enabled": True,
        }
        try:
            r = httpx.post(url, headers=self.headers, json=data, timeout=10)
            return r.status_code in (200, 201)
        except Exception as e:
            st.error(f"Erreur create_schedule: {e}")
        return False

    def toggle_schedule(self, schedule_id: str, enabled: bool) -> bool:
        """Activer/désactiver une planification."""
        url = f"{self.url}/rest/v1/schedules?id=eq.{schedule_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.patch(url, headers=h, json={"enabled": enabled}, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False

    def delete_schedule(self, schedule_id: str) -> bool:
        """Supprimer une planification."""
        url = f"{self.url}/rest/v1/schedules?id=eq.{schedule_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.delete(url, headers=h, timeout=10)
            return r.status_code in (200, 204)
        except Exception:
            return False

    def save_setting(self, user_id: str, field: str, value: str) -> bool:
        """Enregistre un réglage utilisateur (champs autorisés uniquement)."""
        allowed = {"linkedin_cookie", "linkedin_cookie_li_at", "gmail_address",
                   "gmail_password", "telephone"}
        if field not in allowed:
            st.error(f"Champ non autorisé: {field}")
            return False
        url = f"{self.url}/rest/v1/users?id=eq.{user_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.patch(url, headers=h, json={field: value}, timeout=10)
            return r.status_code in (200, 204)
        except Exception as e:
            st.error(f"Erreur save_setting: {e}")
            return False

    def get_user_settings(self, user_id: str) -> Dict:
        """Récupère le profil/réglages complets de l'utilisateur (usage interne)."""
        url = f"{self.url}/rest/v1/users?id=eq.{user_id}&select=*"
        try:
            r = httpx.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200 and r.json():
                return r.json()[0]
        except Exception:
            pass
        return {}

    def update_user(self, user_id: str, data: Dict) -> bool:
        """Met à jour les champs de profil d'un utilisateur (liste blanche de sécurité)."""
        allowed = {"full_name", "nom_complet", "telephone", "ville", "province",
                   "linkedin_url", "linkedin_profile", "location", "keywords", "sector",
                   "cv_text", "cv_filename",
                   "ecole", "programme_etudes", "parcours_scolaire", "session_coop",
                   "coop_zone_ville", "coop_zone_province", "coop_zone_pays",
                   "pays_origine", "statut_immigration", "annee_arrivee",
                   "post_genre", "post_peau", "post_langue", "post_edito1", "post_edito2",
                   "post_tag", "photo_b64", "gmail_address", "gmail_password"}
        payload = {k: v for k, v in data.items() if k in allowed}
        if not payload:
            return False
        url = f"{self.url}/rest/v1/users?id=eq.{user_id}"
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            r = httpx.patch(url, headers=h, json=payload, timeout=10)
            if r.status_code in (200, 204):
                return True
            st.error(f"Erreur update_user: {r.status_code} {r.text[:200]}")
            return False
        except Exception as e:
            st.error(f"Erreur update_user: {e}")
            return False

    def delete_user(self, user_id: str, with_data: bool = True) -> bool:
        """Supprimer un compte utilisateur (et ses données). Destructif."""
        h = {**self.headers, "Prefer": "return=minimal"}
        try:
            if with_data:
                # Supprimer les données liées d'abord
                for table in ["candidatures", "livrables", "schedules", "actions", "jobs"]:
                    try:
                        httpx.delete(f"{self.url}/rest/v1/{table}?user_id=eq.{user_id}",
                                     headers=h, timeout=20)
                    except Exception:
                        pass
            r = httpx.delete(f"{self.url}/rest/v1/users?id=eq.{user_id}",
                             headers=h, timeout=10)
            return r.status_code in (200, 204)
        except Exception as e:
            st.error(f"Erreur delete_user: {e}")
            return False

    def update_user_status(self, user_id: str, field: str, value: bool) -> bool:
        """Mettre à jour un statut booléen d'un utilisateur (is_whitelisted, is_active...).
        Seuls les champs autorisés sont modifiables (sécurité)."""
        allowed = {"is_whitelisted", "is_active"}
        if field not in allowed:
            st.error(f"Champ non autorisé: {field}")
            return False

        url = f"{self.url}/rest/v1/users?id=eq.{user_id}"
        headers = {**self.headers, "Prefer": "return=minimal"}
        try:
            response = httpx.patch(url, headers=headers, json={field: value}, timeout=10)
            return response.status_code in (200, 204)
        except Exception as e:
            st.error(f"Erreur update_user_status: {e}")
        return False

    def count_jobs(self, user_id: str) -> int:
        """Compter les offres d'un utilisateur"""
        url = f"{self.url}/rest/v1/jobs?select=id&user_id=eq.{user_id}"
        try:
            response = httpx.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return len(response.json())
        except Exception:
            pass
        return 0

    def get_jobs(self, user_id: str, limit: int = 100, score_min: int = 0,
                 sources: List[str] = None) -> List[Dict]:
        """Récupérer offres d'emploi"""
        url = f"{self.url}/rest/v1/jobs?user_id=eq.{user_id}&order=scraped_at.desc&limit={limit}"

        try:
            response = httpx.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                jobs = response.json()

                # Filtrer par score
                jobs = [j for j in jobs if j.get('score', 0) >= score_min]

                # Filtrer par sources
                if sources:
                    jobs = [j for j in jobs if j.get('source', '').lower() in
                            [s.lower() for s in sources]]

                return jobs
        except Exception as e:
            st.error(f"Erreur get_jobs: {e}")
        return []

    def get_stats(self, user_id: str) -> Dict:
        """Récupérer statistiques utilisateur"""
        stats = {
            "total_offres": 0,
            "offres_semaine": 0,
            "score_moyen": 0,
            "sources": {}
        }

        try:
            # Total offres
            url = f"{self.url}/rest/v1/jobs?user_id=eq.{user_id}&select=id,score,source,scraped_at"
            response = httpx.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                jobs = response.json()
                stats["total_offres"] = len(jobs)

                if jobs:
                    # Score moyen
                    scores = [j.get('score', 0) for j in jobs if j.get('score')]
                    stats["score_moyen"] = int(sum(scores) / len(scores)) if scores else 0

                    # Sources
                    for job in jobs:
                        source = job.get('source', 'unknown')
                        stats["sources"][source] = stats["sources"].get(source, 0) + 1

                    # Offres cette semaine (7 derniers jours)
                    from datetime import datetime, timedelta
                    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
                    stats["offres_semaine"] = len([
                        j for j in jobs
                        if j.get('scraped_at', '') >= week_ago
                    ])

        except Exception as e:
            st.error(f"Erreur get_stats: {e}")

        return stats

    def create_action(self, user_id: str, agent_name: str, params: Dict = None) -> Optional[Dict]:
        """Créer une action pour lancer un agent"""
        url = f"{self.url}/rest/v1/actions"

        data = {
            "user_id": user_id,
            "action_type": agent_name,
            "parameters": params or {},
            "status": "pending",
            "priority": 5
        }

        try:
            # return=representation pour récupérer l'id de l'action créée (suivi en direct)
            headers = {**self.headers, "Prefer": "return=representation"}
            response = httpx.post(url, headers=headers, json=data, timeout=10)
            if response.status_code in [200, 201]:
                if response.text and response.text.strip():
                    try:
                        result = response.json()
                        return result[0] if isinstance(result, list) else result
                    except:
                        pass
                return {"status": "created", "action_type": agent_name}
            else:
                st.error(f"Erreur HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            st.error(f"Erreur create_action: {e}")
        return None

    def get_action(self, action_id: str) -> Optional[Dict]:
        """Récupérer une action précise (statut + log en direct)."""
        url = f"{self.url}/rest/v1/actions?id=eq.{action_id}&select=*"
        try:
            r = httpx.get(url, headers=self.headers, timeout=8)
            if r.status_code == 200 and r.json():
                return r.json()[0]
        except Exception:
            pass
        return None

    def get_recent_actions(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Récupérer actions récentes"""
        url = f"{self.url}/rest/v1/actions?user_id=eq.{user_id}&order=created_at.desc&limit={limit}"

        try:
            response = httpx.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            st.error(f"Erreur get_recent_actions: {e}")
        return []

    def get_candidatures(self, user_id: str) -> Dict:
        """Récupérer statistiques candidatures"""
        stats = {
            "en_attente": 0,
            "envoyees": 0,
            "reponses": 0,
            "entretiens": 0
        }

        try:
            url = f"{self.url}/rest/v1/candidatures?user_id=eq.{user_id}&select=status"
            response = httpx.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                candidatures = response.json()

                for cand in candidatures:
                    s = (cand.get('status') or '').lower()
                    a_entretien = ('entretien' in s or 'interview' in s)
                    # Une réponse = refus OU invitation entretien
                    a_reponse = (a_entretien or 'repons' in s or 'response' in s
                                 or 'refus' in s or 'reject' in s)
                    # Reçue (accusé de réception) compte comme envoyée.
                    # ⚠️ 'a_envoyer' (approuvée, PAS encore envoyée) ne doit PAS compter.
                    a_envoye = ((('envoyee' in s or 'envoyée' in s) and 'a_envoyer' not in s)
                                or 'sent' in s or 'recu' in s or 'reçu' in s or a_reponse)
                    # Entonnoir cumulatif : Envoyées >= Réponses >= Entretiens
                    if a_envoye:
                        stats["envoyees"] += 1
                    if a_reponse:
                        stats["reponses"] += 1
                    if a_entretien:
                        stats["entretiens"] += 1
                    if not a_envoye:  # pas encore envoyée (en attente / validée)
                        stats["en_attente"] += 1

        except Exception as e:
            st.error(f"Erreur get_candidatures: {e}")

        return stats


# Singleton
@st.cache_resource
def get_supabase_client():
    """Retourne instance Supabase (cached)"""
    return SupabaseClient()
