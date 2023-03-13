def parse_1(str, parser):
    return parser.analyze_words(str)[0]


def test_noun_inflection(parser):
    for i, x in enumerate(["uyïwïj", "mëyïwïj", "tïwïj"]):  # 'house'
        form = parse_1(x, parser)
        assert form.lemma == "iwiti-house"
        assert "house" in form.gloss
        assert "poss" in form.gramm
        assert str(i + 1) in form.gloss
        assert "pst" in parse_1(x+"jpë", parser).gramm
    assert "npert" in parse_1("ëjtë", parser).gramm
    assert "pl" in parse_1("uyïwïjjne", parser).gramm

    for i, x in enumerate(["umukuru", "mëmukuru", "imukuru"]):  # 'child'
        form = parse_1(x, parser)
        assert form.lemma == "muku-child"
        assert "child" in form.gloss
        assert "poss" in form.gramm
        assert str(i + 1) in form.gloss
        assert "pst" in parse_1(x+"jpë", parser).gramm
    assert "pl" in parse_1("mukuton", parser).gramm
    assert "pl" in parse_1("mukutomojne", parser).gramm

    for i, x in enumerate(["unajmori", "anajmori", "inajmori"]):  # 'grandmother'
        form = parse_1(x, parser)
        assert form.lemma == "najmo-grandmother"
        assert "grandmother" in form.gloss
        assert "poss" in form.gramm
        assert str(i + 1) in form.gloss
        assert "pst" in parse_1(x+"jpë", parser).gramm

    for i, x in enumerate(["uyawori", "ayawori", "tawori"]): # 'uncle / father in law'
        form = parse_1(x, parser)
        assert form.lemma == "awo-uncle"
        assert "uncle" in form.gloss
        assert "poss" in form.gramm
        assert str(i+1) in form.gloss
        assert "pst" in parse_1(x+"jpë", parser).gramm
    assert "lk" in parse_1("yawori", parser).gramm


    for i, x in enumerate(["uyejweti", "mëyejweti", "tejweti"]): # 'uncle / father in law'
        form = parse_1(x, parser)
        assert form.lemma == "ejwe-hammock"
        assert "hammock" in form.gloss
        assert "poss" in form.gramm
        assert str(i+1) in form.gloss
        assert "pst" in parse_1(x+"jpë", parser).gramm
    assert "lk" in parse_1("yejweti", parser).gramm
    assert "npert" in parse_1("ëjwatë", parser).gramm

    

def test_postp_inflection(parser):
    for i, x in enumerate(["upoye", "mëpoye", "ipoye"]):
        form = parse_1(x, parser)
        assert "poye-above" == form.lemma
        assert str(i+1) in form.gramm


def test_verb_inflection(parser):
    for lemma, gloss, gramm, verb_set in [
        ("yerema-feed", "feed", "ipfv", ["uyeremari", "mëyeremari", "tayeremari"]),
        ("senejka-stay", "stay", "ipfv", ["usenejkari", "mësenejkari", "senejkari"]),
    ]:
        for i, x in enumerate(verb_set):
            forms = parser.analyze_words(x)
            for form in forms:
                if gramm not in form.gramm:
                    continue
                assert form.lemma == lemma
                assert gloss in form.gloss
                assert gramm in form.gramm


def test_tam_suffixes(parser):
    for form, lemma, gloss, gramm, bad_tag in [
        ("tainija", "ini-see", "3P-see-NEG", "neg,3P,vt", ""),
        ("tainiri", "ini-see", "3P-see-IPFV", "ipfv,3P,vt", "n"),
        ("inijpë", "ini-see", "see-PST", "pst,vt", "n"),
        ("inisapë", "ini-see", "see-PFV", "pfv,vt", "n"),
        ("initojpe", "ini-see", "see-FUT", "fut,vt", "adv"),
        ("inche", "ini-see", "see-PST", "pst,vt", "adv"),
        ("tasarë", "taro-say", "say-IMN", "imn,vt", "adv"),
        ("yaruwatëpëkë", "yaruwa-laugh", "laugh-PROG.INTR", "prog,vi", ""),
        ("tapëkë", "taro-say", "say-PROG.TR", "prog,vt", ""),
        ("yaruwarijra", "yaruwa-laugh", "laugh-IPFV-NEG", "ipfv,vi,neg", "n"),
        # ("yaruwajrama", "yaruwa-laugh", "laugh-PROH", "vi,proh", ""), # todo: disambiguate
    ]:
        analyses = parser.analyze_words(form)
        for analysis in analyses:
            if bad_tag in analysis.gramm.split(","):
                continue
            assert analysis.lemma == lemma
            assert analysis.gloss == gloss
            assert set(analysis.gramm.split(",")) == set(gramm.split(","))
