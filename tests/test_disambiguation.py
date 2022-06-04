def parse_ambig(ambig, parser):
    return (
        parser.analyze_words(ambig.split(" ")),
        parser.analyze_words(ambig.split(" "), disambiguate=False),
    )


# def test_wejsapë(parser):
#     anas, anas2 = parse_ambig("yaka wejsapë", parser)
#     assert len(anas[1]) == 1
#     assert len(anas2[1]) == 3


# def test_taro(parser):
#     anas, anas2 = parse_ambig("wïrë taro", parser)
#     assert len(anas[1]) == 2
#     assert len(anas2[1]) == 3


# def test_të(parser):
#     anas, anas2 = parse_ambig("ana të", parser)
#     assert len(anas[1]) == 2
#     assert len(anas2[1]) == 3


def test_ma(parser):
    anas = parser.analyze_words("tawara ma".split(" "))
    assert len(anas[1]) == 1


# def test_ta(parser):
#     for exp in ["yojtë ta", "asamo ta"]:
#         anas = parser.analyze_words(exp.split(" "))
#         assert len(anas[1]) == 1
