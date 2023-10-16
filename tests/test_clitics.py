from uniparser_yawarana import YawaranaAnalyzer

a = YawaranaAnalyzer(etymologize=False)
print(a.analyze_words("tasarë".split(" ")))
