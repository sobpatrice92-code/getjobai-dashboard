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
        self.key = os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            try:
                self.url = self.url or st.secrets.get("SUPABASE_URL")
                self.key = self.key or st.secrets.get("SUPABASE_KEY")
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
            response = httpx.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code in [200, 201]:
                # Supabase 201 peut retourner réponse vide - c'est OK
                if response.text and response.text.strip():
                    try:
                        result = response.json()
                        return result[0] if isinstance(result, list) else result
                    except:
                        pass
                # Succès même si pas de JSON retourné
                return {"status": "created", "action_type": agent_name}
            else:
                st.error(f"Erreur HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            st.error(f"Erreur create_action: {e}")
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
                    status = cand.get('status', '').lower()
                    if 'pending' in status or 'attente' in status:
                        stats["en_attente"] += 1
                    elif 'sent' in status or 'envoyée' in status:
                        stats["envoyees"] += 1
                    elif 'response' in status or 'réponse' in status:
                        stats["reponses"] += 1
                    elif 'interview' in status or 'entretien' in status:
                        stats["entretiens"] += 1

        except Exception as e:
            st.error(f"Erreur get_candidatures: {e}")

        return stats


# Singleton
@st.cache_resource
def get_supabase_client():
    """Retourne instance Supabase (cached)"""
    return SupabaseClient()
