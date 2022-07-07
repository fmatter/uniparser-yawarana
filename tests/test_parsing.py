def parse_1(str, parser):
    return parser.analyze_words(str)[0]



def test_multiple(parser):
    assert len(parser.analyze_words("wïrë tawara rë entë".split(" "))) == 4


def test_bad_parsing(parser):
    assert len(parser.analyze_words("yawë", parser)) == 1
