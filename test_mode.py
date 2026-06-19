"""Garde-fou d'environnement de TEST (dashboard).

TEST_MODE=1 (posé par LANCER_TEST_dashboard) => aucun effet réel externe :
les publications LinkedIn sont simulées. Le reste du flux (lecture/écriture en
base staging) fonctionne normalement.
"""
import os


def est_test() -> bool:
    return str(os.getenv("TEST_MODE", "")).strip().lower() in ("1", "true", "yes", "on")


def banniere() -> str:
    return "[TEST_MODE] envois reels BLOQUES (LinkedIn simule)" if est_test() else ""
