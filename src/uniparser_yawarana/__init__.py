"""Documentation about uniparser_yawarana"""
import logging
from uniparser_morph import Analyzer


try:
    from importlib.resources import files  # pragma: no cover
except ImportError:  # pragma: no cover
    from importlib_resources import files  # pragma: no cover

log = logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Florian Matter"
__email__ = "florianmatter@gmail.com"
__version__ = "0.0.5.dev"


class YawaranaAnalyzer(Analyzer):
    def __init__(self, etymologize = False, verbose_grammar=False):
        if etymologize:
            mode = "etym"
        else:
            mode = "default"
        self.base_path = files("uniparser_yawarana") / "data" / mode
        super().__init__(verbose_grammar=verbose_grammar)
        self.lexFile = self.base_path / "lexemes.txt"
        self.paradigmFile = self.base_path / "paradigms.txt"
        self.delAnaFile = self.base_path / "bad_analyses.txt"
        self.cliticFile = self.base_path / "clitics.txt"
        self.derivFile = self.base_path / "derivations.txt"
        self.load_grammar()

    def analyze_words(
        self, words, cgFile="", format=None, disambiguate=True  # noqa: N803
    ):
        all_analyses = super().analyze_words(
            words,
            cgFile=str(self.base_path / "disambiguation.cg3"),
            format=format,
            disambiguate=disambiguate,
        )
        all_analyses = [x for x in all_analyses if not ("jrama" in x.wf and "neg" in x.gramm)]
        for x in all_analyses:
            pass
            # print("jrama" in x.wf and "proh" in x.gramm)
            # if "=" in x.wfGlossed:
            #     x.lemma = x.lemma.replace("+", ",")
        return all_analyses
