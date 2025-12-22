def resolve_errors(fms: list[str], err_registry: list[dict]) -> list[str]:
    errs = []
    for entry in err_registry:
        if any(fm in fms for fm in entry["fm"]):
            errs.append(entry["id"])
    return sorted(set(errs))
