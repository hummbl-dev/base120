def resolve_errors(fms: list[str], err_registry: list[dict]) -> list[str]:
    # FM30 dominance: escalation suppresses all other errors
    if "FM30" in fms:
        return sorted(
            entry["id"]
            for entry in err_registry
            if "FM30" in entry["fm"]
        )

    errs = []
    for entry in err_registry:
        if any(fm in fms for fm in entry["fm"]):
            errs.append(entry["id"])
    return sorted(set(errs))
