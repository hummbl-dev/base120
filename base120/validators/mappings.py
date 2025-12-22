def resolve_failure_modes(subclass: str, mappings: dict) -> list[str]:
    return mappings.get("mappings", {}).get(subclass, [])
