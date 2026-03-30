from src.doc_extract import merge_results

def test_merge_ignores_null():
    base = {"email": None}
    new = {"email": "null"}
    result = merge_results(base, new)
    assert result["email"] is None

def test_merge_doesnt_overwrite():
    base = {"email": "joe@bloggs.com"}
    new = {"email": "newjoe@bloggs.com"}
    result = merge_results(base, new)
    assert result["email"] is "joe@bloggs.com"