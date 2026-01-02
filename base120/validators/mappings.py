from typing import Mapping, Sequence


def resolve_failure_modes(subclass: str, mappings: Mapping[str, Mapping[str, Sequence[str]]]) -> list[str]:
    return list(mappings.get("mappings", {}).get(subclass, []))
