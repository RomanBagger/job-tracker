"""Рейтинг компаний. Модель оценивает по знаниям + web search (Glassdoor, Pracuj, Levels, GoWork, justjoin)."""
import json
import re

import anthropic

from .config import TIER_MODEL, TIER_OVERRIDES

SYSTEM = """Ты оцениваешь работодателей для DevOps/Platform/SRE инженера в Польше.
Критерии: зарплатные вилки в PL (B2B/UoP), рост и техническая сложность, бенефиты, отзывы сотрудников
(Glassdoor, GoWork, Pracuj, Reddit), стабильность, масштаб и зрелость продукта.
Предпочтение: крупные собственные продукты > сильный консалтинг/аутсорс > слабый продукт > слабый консалтинг.
Сильный консалтинг (хорошие деньги, хороший стек, хорошие отзывы) должен быть выше плохого продукта.
category: product | consulting | outsourcing | startup | agency | other
tier: S (топ: FAANG-уровень, топ-финтех/продукты с высокими вилками) | A (сильные) | B (нормальные) | C (средние/слабые) | D (избегать)
Верни ТОЛЬКО JSON-объект: {"tier":..., "category":..., "rationale": "1-2 предложения про зарплату/рост/отзывы"}."""


def overrides():
    return json.loads(TIER_OVERRIDES.read_text()) if TIER_OVERRIDES.exists() else {}


def rate(name):
    client = anthropic.Anthropic()
    kwargs = dict(
        model=TIER_MODEL, max_tokens=1024, system=SYSTEM,
        messages=[{"role": "user", "content": f"Компания: {name}. Рынок: Польша."}],
    )
    try:
        resp = client.messages.create(
            **kwargs, tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}])
    except anthropic.APIError:
        resp = client.messages.create(**kwargs)
    text = "".join(b.text for b in resp.content if b.type == "text")
    m = re.search(r"\{.*\}", text, re.S)
    try:
        d = json.loads(m.group(0))
    except (AttributeError, ValueError):
        return {"tier": "C", "category": "other", "rationale": "не удалось оценить"}
    if d.get("tier") not in list("SABCD"):
        d["tier"] = "C"
    return d
