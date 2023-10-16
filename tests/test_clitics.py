from uniparser_yawarana import fix_clitic

def test_jra(parser):
    print(fix_clitic(parser.analyze_words("tejporejra")[0]))