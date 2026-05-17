MESSAGES: dict[str, dict[str, str]] = {
    "ru": {
        "critical_shortage": "Критический дефицит по SKU",
        "critical_overstock": "Критический избыток по SKU",
        "expiry_warning": "Срок годности истекает менее чем через 7 дней",
    },
    "en": {
        "critical_shortage": "Critical shortage for SKU",
        "critical_overstock": "Critical overstock for SKU",
        "expiry_warning": "Expiry date is less than 7 days away",
    },
}


def t(language: str, key: str) -> str:
    lang = language if language in MESSAGES else "en"
    return MESSAGES.get(lang, {}).get(key, key)
