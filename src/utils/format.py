def id_to_name(id: str) -> str:
    return id.replace("_", " ").title().strip()
