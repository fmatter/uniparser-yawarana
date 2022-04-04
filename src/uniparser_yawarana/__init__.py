"""Documentation about uniparser_yawarana"""
import logging
from pathlib import Path
from uniparser_morph import Analyzer


logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Florian Matter"
__email__ = "florianmatter@gmail.com"
__version__ = "0.0.1"


class YawaranaAnalyzer(Analyzer):
    def __init__(self, verbose_grammar=False):
        base = Path("src/uniparser_yawarana/data")
        super().__init__(verbose_grammar=verbose_grammar)
        self.lexFile = base / "lexemes.txt"
        self.paradigmFile = base / "paradigms.txt"
        # self.cliticsFile = base / "clitics.txt"
        self.load_grammar()

    def analyze_words(self, words, cgFile="", format=None, disambiguate=False):
        return super().analyze_words(words, cgFile=cgFile, format=format, disambiguate=disambiguate)
