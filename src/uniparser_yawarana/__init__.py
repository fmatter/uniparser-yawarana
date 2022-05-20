"""Documentation about uniparser_yawarana"""
import logging
from uniparser_morph import Analyzer


try:
    from importlib.resources import files  # pragma: no cover
except ImportError:  # pragma: no cover
    from importlib_resources import files  # pragma: no cover

logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Florian Matter"
__email__ = "florianmatter@gmail.com"
__version__ = "0.0.3"


class YawaranaAnalyzer(Analyzer):
    def __init__(self, verbose_grammar=False):
        self.base_path = files("uniparser_yawarana") / "data"
        super().__init__(verbose_grammar=verbose_grammar)
        self.lexFile = self.base_path / "lexemes.txt"
        self.paradigmFile = self.base_path / "paradigms.txt"
        self.delAnaFile = self.base_path / "bad_analyses.txt"
        self.cliticFile = self.base_path / "clitics.txt"
        self.load_grammar()

    # def del_seg(self, analyses):
    #     return analyses
    #     pruned_analyses = []
    #     for analysis in analyses:
    #         if (
    #             analysis.wf in self.bad_segmentations
    #             and analysis.wfGlossed in self.bad_segmentations[analysis.wf]
    #         ):
    #             pass
    #         else:
    #             pruned_analyses.append(analysis)
    #     return pruned_analyses

    def analyze_words(
        self, words, cgFile="", format=None, disambiguate=True  # noqa: N803
    ):
        all_analyses = super().analyze_words(
            words,
            cgFile=str(self.base_path / "disambiguation.cg3"),
            format=format,
            disambiguate=disambiguate,
        )
        return all_analyses
