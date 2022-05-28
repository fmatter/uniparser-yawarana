def parse_1(str, parser):
    return parser.analyze_words(str)[0]


def test_se(parser):
    for a, b in [("sujta", "sujtase")]:
        assert parse_1(b, parser).lemma == a


def test_clitics(parser):
    assert parse_1("yatampe", parser).lemma == "yatanë"
    assert parse_1("chawë", parser).lemma == "chi"


def test_multiple(parser):
    assert len(parser.analyze_words("wïrë tawara rë entë".split(" "))) == 4


def test_bad_parsing(parser):
    assert len(parser.analyze_words("yawë", parser)) == 1

def test_noun_inflection(parser):
    for x in ["uyïwïj", "mëyïwïj", "tïwïj"]: # 'house'
        form = parse_1(x, parser)
        assert form.lemma == "ïwïtï"
        assert "house" in form.gloss
        assert "poss" in form.gramm

    for x in ["umukuru", "mëmukuru", "imukuru"]: # 'child'
        form = parse_1(x, parser)
        assert form.lemma == "muku"
        assert "child" in form.gloss
        assert "poss" in form.gramm

    for x in ["unajmori", "anajmori", "inajmori"]: # 'grandmother'
        form = parse_1(x, parser)
        assert form.lemma == "najmo"
        assert "grand.mother" in form.gloss
        assert "poss" in form.gramm

    assert "pert" in parse_1("yëri", parser).gramm
    assert "NPERT" in parse_1("yëtë", parser).gloss