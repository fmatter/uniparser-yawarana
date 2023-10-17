"""Documentation about uniparser_yawarana"""
import logging
import yaml
from uniparser_morph import Analyzer
from writio import load
import re

try:
    from importlib.resources import files  # pragma: no cover
except ImportError:  # pragma: no cover
    from importlib_resources import files  # pragma: no cover

log = logging.getLogger(__name__).addHandler(logging.NullHandler())

__author__ = "Florian Matter"
__email__ = "fmatter@mailbox.org"
__version__ = "0.0.7.dev"


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
        clitic_str = load(self.base_path / "clitics.txt") + "\n\n" + load(self.base_path / "pseudoclitics.txt")
        self.clitics = []
        for clitic in clitic_str.split("\n\n"):
            cldict = {l.split(": ")[0].strip(): l.split(": ")[1] for l in clitic.split("\n")[1::]}
            if cldict["type"] == "en":
                cldict["form"] = "="+cldict["stem"]
            else:
                cldict["form"] = cldict["stem"]+"="
            cldict["gramm"] = cldict["gramm"].split(",")
            self.clitics.append(cldict)
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

    def fix_clitic(self, wf):
        if "=" in wf.wfGlossed:
            wf.lemma = wf.lemma.replace("+", "=")
            wf.gramm = wf.gramm.split(",")
            add_data = dict(wf.otherData)
            add_data["id"] = add_data["id"].split(",")
            if "trans_en" in add_data:
                add_data["trans_en"] = add_data["trans_en"].split("; ")
            while "=" in wf.wfGlossed:
                # print(f"Sorting clitics in {wf.wfGlossed}")
                proclitics = []
                enclitics = []
                for clitic in self.clitics:
                    if clitic["type"] == "en" and wf.wfGlossed.endswith(clitic["form"]):
                        wf.wfGlossed = re.sub(f'{clitic["form"]}$', "", wf.wfGlossed)
                        # print(clitic)
                        # print(wf)
                        for grm in clitic["gramm"]:
                            if grm in wf.gramm:
                                wf.gramm.remove(grm)
                        for k, v in add_data.items():
                            if clitic[k] in v:
                                v.remove(clitic[k])
                        if clitic["lex"] not in wf.lemma:
                            wf.lemma += "=" + clitic["lex"]
                        enclitics.append(clitic)
                    elif clitic["type"] == "pro" and wf.wfGlossed.startswith(clitic["form"]):
                        wf.wfGlossed = re.sub(f'^{clitic["form"]}', "", wf.wfGlossed)
                        for grm in clitic["gramm"]:
                            wf.gramm.remove(grm)
                        for k, v in add_data.items():
                            v.remove(clitic[k])
                        proclitics.append(clitic)
            wf.gramm = ",".join(wf.gramm)
            for k in add_data:
                add_data[k] = ",".join(add_data[k])
            for clitic in proclitics:
                wf.wfGlossed = clitic["form"] + wf.wfGlossed
                wf.gramm = ",".join(clitic["gramm"]) + "=" + wf.gramm
                for k in add_data:
                    add_data[k] = clitic[k] + "=" + add_data[k]
            for clitic in enclitics:
                wf.wfGlossed += clitic["form"]
                wf.gramm = wf.gramm + "=" + ",".join(clitic["gramm"])
                for k in add_data:
                    add_data[k] += "=" + clitic[k]
            wf.otherData = list(add_data.items())
        return wf


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
                ana = [self.fix_clitic(x) for x in ana]
                # dedup = list(dict.fromkeys(ana))
                filtered.append(ana)
                # if len(dedup) == 1:
                #     filtered.append(dedup[0])
                # else:
                #     filtered.append(dedup)
            else:
                filtered.append(self.fix_clitic(ana))
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
