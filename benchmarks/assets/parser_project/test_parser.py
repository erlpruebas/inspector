from parser import load_rows


def test_load_rows_handles_quoted_commas():
    rows = load_rows("sample.csv")
    assert rows[0]["name"] == "Ana Lopez"
    assert rows[0]["notes"] == "cliente prioritario, renovar"
    assert rows[1]["city"] == "Valencia"
