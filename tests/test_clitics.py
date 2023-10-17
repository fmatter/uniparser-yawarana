def test_jra(parser):
    for ana in parser.analyze_words("yaruwarijra"):
        assert ana.gramm.endswith("=part,neg")