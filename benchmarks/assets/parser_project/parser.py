def load_rows(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        headers = handle.readline().strip().split(",")
        for line in handle:
            values = line.strip().split(",")
            rows.append(dict(zip(headers, values)))
    return rows
