from complaint_router.text import normalise, tokenize


def test_normalise_redactions_amounts_numbers():
    assert normalise("Paid {$1,200.50} on XX/XX/XXXX to XXXX") == \
        "paid <amount> on <redacted> to <redacted>"
    assert normalise("  Card   ending 4421 ") == "card ending 0"
    assert normalise("$25 fee") == "<amount> fee"


def test_tokenize_keeps_special_tokens_and_punctuation():
    assert tokenize("I can't find my card!! XXXX") == \
        ["i", "can't", "find", "my", "card", "!", "!", "<redacted>"]
    assert tokenize("") == []
