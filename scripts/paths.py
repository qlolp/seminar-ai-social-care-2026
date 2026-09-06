# -*- coding: utf-8 -*-
"""Корень сборки: репозиторий, legacy-путь агента или SEMINAR_BASE."""
import os
from pathlib import Path

LEGACY = Path('/mnt/agents/output/seminar_ai_2026')


def resolve_base() -> Path:
    env = os.environ.get('SEMINAR_BASE')
    if env:
        return Path(env).expanduser().resolve()
    if LEGACY.is_dir() and (LEGACY / 'chapters').is_dir():
        return LEGACY
    return Path(__file__).resolve().parent.parent
