def eliminate_analysis(anas, bad_glosses):
    for ana in anas:
        for gloss in bad_glosses:
            if gloss in ana.gloss:
                continue
        return ana


def test_se(parser):
    for ana in parser.analyze_words("sujtase"):
        if ana.lemma == "sujta&septcp":
            assert "adv" in ana.gramm.split(",")
        elif ana.lemma == "sujta-urinate":
            assert "vi" in ana.gramm.split(",")
        else:
            raise ValueError(ana)




def pick_analysis(anas, good_gloss):
    for ana in anas:
        if good_gloss in ana.gloss:
            print(f"good analysis for {good_gloss}:", ana,)
            return ana
    return None





def run_polysemy_test(forms, parser):
    for form, data in forms:
        analyses = parser.analyze_words(form)
        for gloss, tag in data.items():
            analysis = pick_analysis(analyses, gloss)
            assert tag in analysis.gramm.split(",")

def test_tojpe(parser):
    run_polysemy_test(
        forms=[
            ("ijmokatojpe", {"PURP": "adv", "FUT": "vt"}),
            ("tawejkatojpe", {"PURP": "adv", "FUT": "vi"}),
        ],
        parser=parser,
    )


def test_ri(parser):
    run_polysemy_test(
        forms=[
            ("yaruwari", {"ACNNMLZ": "n", "IPFV": "vi"}),  # intransitive 'laugh'
            ("iniri", {"ACNNMLZ": "n", "IPFV": "vt"}),  # transitive 'see'
            ("ini", {"ACNNMLZ": "n", "IPFV": "vt"}),  # transitive 'see'
        ],
        parser=parser,
    )


def test_ptcp(parser):
    run_polysemy_test(
        forms=[
            (
                "wïnïjse",
                {"SUP": "adv", "PTCP": "adv", "PST": "vi"},
            ),  # intransitive 'sleep'
            (
                "këyamase",
                {"SUP": "adv", "PTCP": "adv", "PST": "vt"},
            ),  # transitive 'create'
            ("inche", {"SUP": "adv", "PTCP": "adv", "PST": "vt"}),  # transitive 'see'
        ],
        parser=parser,
    )


def test_sapë(parser):
    run_polysemy_test(forms=[("asamosapë", {"PFV": "vi", "NMLZ": "n"})], parser=parser)


def test_jpë(parser):
    for ana in parser.analyze_words("tujpë"):
        if "PST.ACNNMLZ" in ana.gloss:
            assert "n" in ana.gramm.split(",")
        else:
            assert "vt" in ana.gramm.split(",")

def test_unamb_derivs(parser):
    forms = [
        ("asamonë", {"INF": "n"}),
        ("tuni", {"AGTNMLZ": "n"}),
        ("yarikatopo", {"NMLZ": "n"}),
        ("wejtane", {"CNCS": "adv"}),
    ]
    run_polysemy_test(forms, parser)
    forms = [("munemï", {"NMLZ": "n"}), ("mïjnano", {"NMLZ": "n"})]
    run_polysemy_test(forms, parser)
