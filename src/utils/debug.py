def collect_first_elements(obj):
    results = []

    if isinstance(obj, dict):
        for value in obj.values():
            results.extend(collect_first_elements(value))

    elif isinstance(obj, list):
        if obj:  # non-empty list
            first = obj[0]
            results.append(first)
            results.extend(collect_first_elements(first))

    return results
