from src.doc_extract import regex_pre_extract

def test_return_expected_keys():
    text = "Piece of text"

    result = regex_pre_extract(text)

    expected_keys = {
        "bank_account_name",
        "investor_email",
        "bank_sort_code",
        "bank_account_number",
        "bank_name",
        "commitment_amount",
        "commitment_currency",

    }



    assert set(result.keys()) == expected_keys

