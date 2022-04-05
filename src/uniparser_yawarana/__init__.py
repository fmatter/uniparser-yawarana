"""Documentation about uniparser_yawarana"""
import logging
from uniparser_morph import Analyzer
import yaml

try:
    from importlib.resources import files  # pragma: no cover
except ImportError:  # pragma: no cover
    from importlib_resources import files  # pragma: no cover

logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Florian Matter"
__email__ = "florianmatter@gmail.com"
__version__ = "0.0.1.dev"


class YawaranaAnalyzer(Analyzer):
    def __init__(self, verbose_grammar=False):
        base = files("uniparser_yawarana") / "data"
        super().__init__(verbose_grammar=verbose_grammar)
        self.lexFile = base / "lexemes.txt"
        self.paradigmFile = base / "paradigms.txt"
        # self.cliticsFile = base / "clitics.txt"
        self.load_grammar()
        badsegs = open(base / "bad_segmentations.yaml", "r").read()
        self.bad_segmentations = yaml.load(badsegs, Loader=yaml.FullLoader)

    def del_seg(self, analyses):
        pruned_analyses = []
        for analysis in analyses:
            if (
                analysis.wf in self.bad_segmentations
                and analysis.wfGlossed in self.bad_segmentations[analysis.wf]
            ):
                pass
            else:
                pruned_analyses.append(analysis)
        return pruned_analyses

    def analyze_words(self, words, cgFile="", format=None, disambiguate=False):
        all_analyses = super().analyze_words(
            words, cgFile=cgFile, format=format, disambiguate=disambiguate
        )
        if type(words) == str:
            pruned_analyses = self.del_seg(all_analyses)
        else:
            pruned_analyses = []
            for analyses in all_analyses:
                pruned_analyses.append(self.del_seg(analyses))
        return pruned_analyses
