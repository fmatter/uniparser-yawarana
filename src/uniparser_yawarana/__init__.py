"""Documentation about uniparser_yawarana"""
import logging
import yaml
from uniparser_morph import Analyzer


try:
    from importlib.resources import files  # pragma: no cover
except ImportError:  # pragma: no cover
    from importlib_resources import files  # pragma: no cover

log = logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Florian Matter"
__email__ = "fmatter@mailbox.org"
__version__ = "0.0.6"


class YawaranaAnalyzer(Analyzer):
    def __init__(self, etymologize=False, verbose_grammar=False, cache=True):
        super().__init__(verbose_grammar=verbose_grammar)
        self.base_path = files("uniparser_yawarana") / "data"
        self.flattenSubwords = True
        self.paradigmFile = self.base_path / "paradigms.txt"
        self.lexRulesFile = self.base_path / "lex_rules.txt"
        self.lexFile = self.base_path / "lexemes.txt"
        self.delAnaFile = self.base_path / "bad_analyses.txt"
        self.cliticFile = self.base_path / "clitics.txt"
        self.derivFile = self.base_path / "derivations.txt"
        with open(
            files("uniparser_yawarana") / "data" / "etym_lookup.yaml",
            "r",
            encoding="utf-8",
        ) as f:
            self.etym_dict = yaml.load(f, Loader=yaml.SafeLoader)
        self.wfCache = {}
        self.etymologize_mode = etymologize
        self.load_grammar()
        self.initialize_parser()
        self.m.REMEMBER_PARSES = cache

    # def etymologize(self, ana):
    #     etym_ids = []
    #     etym_obj = ana.wfGlossed
    #     etym_gloss = ana.gloss
    #     for k, v in ana.otherData:
    #         if k != "id":
    #             continue
    #         ids = v.split(",")
    #         for _id in ids:
    #             if _id in self.etym_dict:
    #                 etym_info = self.etym_dict[_id]
    #                 etym_ids.extend(etym_info["ids"])
    #                 for orig, repl in etym_info["obj"].items():
    #                     etym_obj = etym_obj.replace(orig, repl)
    #                 for orig, repl in etym_info["gloss"].items():
    #                     etym_gloss = etym_gloss.replace(orig, repl)
    #             else:
    #                 etym_ids.append(_id)
    #     self.wfCache[str(ana)] = [
    #         ("id_etym", ",".join(etym_ids)),
    #         ("wfGlossed_etym", etym_obj),
    #         ("gloss_etym", etym_gloss),
    #     ]

    def analyze_words(  # pylint: disable=redefined-builtin,too-many-arguments
        self,
        words,
        cgFile="",
        format=None,
        disambiguate=True,
        replacementsAllowed=0,
    ):
        all_analyses = super().analyze_words(
            words,
            cgFile=str(self.base_path / "disambiguation.cg3"),
            format=format,
            disambiguate=disambiguate,
        )
        filtered = []
        for ana in all_analyses:
            if isinstance(ana, list):
                dedup = list(dict.fromkeys(ana))
                filtered.append(dedup)
                # if len(dedup) == 1:
                #     filtered.append(dedup[0])
                # else:
                #     filtered.append(dedup)
            else:
                filtered.append(ana)
            # if self.etymologize_mode:
            #     if str(ana) not in self.wfCache:
            #         self.etymologize(ana)
            #     ana.otherData.extend(self.wfCache[str(ana)])
        return filtered

        # if isinstance(all_analyses[0], list):  # filter wrong analyses of -jrama 'PROH'
        #     filtered = []
        #     for analyses in all_analyses:
        #         filtered_analysis = [
        #             x for x in analyses if not ("jrama" in x.wf and "neg" in x.gramm)
        #         ]
        #         if len(filtered_analysis) == 0:
        #             filtered.append(analyses)
        #         else:
        #             filtered.append(filtered_analysis)
        # else:
        #     filtered = [
        #         x for x in all_analyses if not ("jrama" in x.wf and "neg" in x.gramm)
        #     ]
        #     if len(filtered) == 0:
        #         return all_analyses
