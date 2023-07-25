import json
from itertools import product
from pathlib import Path
import pandas as pd
import yaml
from humidifier import humidify
from yawarana_helpers import find_detransitivizer
from yawarana_helpers import glossify
from yawarana_helpers import trim_dic_suff
from writio import load, dump


def write_file(path, content, mode="text"):
    with open(path, "w", encoding="utf-8") as f:
        if mode == "yaml":
            yaml.dump(content, f)
        if mode == "text":
            f.write(content)
        if mode == "json":
            json.dump(content, f, ensure_ascii=False, indent=4)
        return None
    raise ValueError(mode)


def read_file(path, mode="text"):
    with open(path, "r", encoding="utf-8") as f:
        if mode == "yaml":
            return yaml.load(f, yaml.SafeLoader)
        if mode == "text":
            return f.read()
        raise ValueError(mode)

def create_lex_id(rec):
    if rec.get("ID"):
        if len(rec["ID"]) < 15:
            return rec["ID"]
    return humidify(rec["Form"].split(SEP)[0] + " " + rec["Gloss"])

SEP = "; "  # separator between variants of same form
DATA_PATH = Path("src/uniparser_yawarana/data")  # the python package's data folder
DERIV_SEP_PATTERN = f"[{''.join(['+', '-'])}]"
# enriched LIFT export from MCMM
dic = pd.read_csv(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_dictionary/annotated_dictionary.csv",
    keep_default_na=False,
)
# keep only roots
roots = dic[dic["Translation_Root"] != ""]
roots.rename(columns={"Translation_Root": "Translation"}, inplace=True)
roots["Translation"] = roots["Translation"].apply(lambda x: x.replace("-", "_"))
roots = roots.apply(
    lambda x: trim_dic_suff(x, "; "), axis=1
)  # cut off lemma-forming suffixes
roots["Gloss"] = roots["Translation"].apply(
    lambda x: glossify(x.split(SEP)[0])
)  # get a single gloss
roots["Form"] = roots.apply(
    lambda x: SEP.join(list(x["Form"].split(SEP) + x["Variants"].split(SEP))).strip(
        SEP
    ),
    axis=1,
)  # get variants
keep_cols = """ID
Form
Gloss_es
POS
Gloss
Translation
Paradigm
Gramm
Comment
PERT
NPERT
2_Prefix""".split(
    "\n"
)
roots = roots[keep_cols]  # prune columns
manual_roots = pd.read_csv(
    "data/manual_roots.csv", keep_default_na=False
)  # roots manually added to the CLDF dataset for some reason
manual_roots["Gloss"] = manual_roots["Translation"].apply(
    lambda x: glossify(x.split(SEP)[0])
)  # get a single gloss
# manual_roots["Form"] = manual_roots.apply(lambda x: SEP.join(x["Form"]), axis=1)# get variants
roots = pd.concat([roots, manual_roots])  # combine with dictionary roots
roots["ID"] = roots.apply(create_lex_id, axis=1)  # create IDs
roots.set_index("ID", inplace=True, drop=False)  # make retrievable quickly
roots["Etym_Gloss"] = roots[
    "Gloss"
]  # roots cannot have an "etymologizing" (showing derivational structure) gloss
roots.to_csv("var/roots.csv", index=False)
bound_roots = pd.read_csv("data/bound_roots.csv")  #
bound_roots["ID"] = bound_roots.apply(
    lambda x: humidify(f"{x['Form']}-{x['Translation']}"), axis=1
)
bound_roots.set_index("ID", inplace=True)
bound_roots["Etym_Gloss"] = bound_roots["Translation"]
deriv_morphs = pd.read_csv(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana-corpus-cldf/etc/derivation_morphs.csv"
)
deriv_morphs.set_index("ID", inplace=True, drop=False)
# method to read stems identified as being derived from some other stem
def read_deriv(name, pos):
    df = pd.read_csv(f"data/derivations/{name}.csv", keep_default_na=False)
    df["POS"] = pos
    df["Affix_ID"] = name
    return df

kavbz = read_deriv("kavbz", "vt")  # transitive verbalizer -ka
kavbz["Suffix_Gloss"] = "VBZ.TR"
tavbz = read_deriv("tavbz", "vi")  # intransitive verbalizer -ta
tavbz["Suffix_Gloss"] = "VBZ.INTR"
macaus = read_deriv("macaus", "vt")  # causativizer -ma
macaus["Suffix_Gloss"] = "CAUS"
detrz = read_deriv("detrz", "vi")  # detransitivized verbs
detrz["Affix_ID"] = detrz["Form"].apply(find_detransitivizer)
detrz["Prefix_Gloss"] = "DETRZ"
derivations = pd.concat([kavbz, tavbz, macaus, detrz])  # assemble derived stems


def disassemble_stem(rec, stem_dic=None):
    if not stem_dic:
        stem_dic = {}
        for pos in ["Prefix", "Stem", "Suffix"]:
            stem_dic[pos] = {}
            for level in ["ID", "Gloss"]:
                stem_dic[pos][level] = []
    if pd.isnull(rec.Prefix_Gloss):
        filled = "Suffix"
    else:
        filled = "Prefix"
    stem_dic[filled]["ID"].append(rec["Affix_ID"])
    stem_dic[filled]["Gloss"].append(rec[f"{filled}_Gloss"])
    if rec.Base_Stem in roots.index:  # morphologically simple stem
        stem_dic["Stem"]["ID"] = [rec.Base_Stem]
        stem_dic["Stem"]["Gloss"] = [roots.loc[rec.Base_Stem]["Gloss"]]
        return stem_dic
    if rec.Base_Stem in derivations.index:  # morphologically complex stem base
        return disassemble_stem(derivations.loc[rec.Base_Stem], stem_dic)
    stem_dic["Stem"]["ID"] = []
    stem_dic["Stem"]["Gloss"] = []
    return stem_dic


def process_stem(rec):
    disassemble_stem(rec)
    return rec


# function for processing morphologically complex stems
positions = ["Prefix", "Stem", "Suffix"]  # positions


derivations["Gloss"] = derivations["Translation"].apply(glossify)
derivations["Name"] = derivations["Form"].apply(
    lambda x: x.split(SEP)[0].replace("+", "").replace("-", "")
)
derivations["ID"] = derivations.apply(
    lambda x: humidify(f"{x['Name']}-{x['Translation']}"), axis=1
)  # generate IDs
derivations.set_index("ID", inplace=True, drop=False)  # make quickly retrievable
derivations = derivations.apply(process_stem, axis=1)

# misc derivations
misc = pd.read_csv("data/derivations/misc_derivations.csv", keep_default_na=False)
misc["Form"] = misc["Form"].apply(lambda x: x.replace("+", "").replace("-", ""))
misc["Gloss"] = misc["Translation"].apply(glossify)
misc["ID"] = misc.apply(create_lex_id, axis=1)

# assemble all stems (called lexemes in the uniparser context)
lexemes = pd.concat([roots, derivations, misc])
lexemes = lexemes.fillna("")


# the etymological gloss is based on the gloss of the base
# and the gloss of the derivational affix
def add_etym_gloss(rec):
    if rec["Prefix_Gloss"] != "":
        if rec["Base_Stem"] in lexemes:
            rec["Etym_Gloss"] = (
                rec["Prefix_Gloss"] + "-" + lexemes.loc[rec["Base_Stem"]]["Etym_Gloss"]
            )
        elif rec["Base_Stem"] in bound_roots:
            rec["Etym_Gloss"] = (
                rec["Prefix_Gloss"]
                + "-"
                + bound_roots.loc[rec["Base_Stem"]]["Etym_Gloss"]
            )
    elif rec["Suffix_Gloss"] != "":
        if rec["Base_Stem"] in lexemes:
            rec["Etym_Gloss"] = (
                lexemes.loc[rec["Base_Stem"]]["Etym_Gloss"] + "-" + rec["Suffix_Gloss"]
            )
        elif rec["Base_Stem"] in bound_roots:
            rec["Etym_Gloss"] = (
                bound_roots.loc[rec["Base_Stem"]]["Etym_Gloss"]
                + "-"
                + rec["Suffix_Gloss"]
            )
    return rec


lexemes = lexemes.apply(add_etym_gloss, axis=1)
# this dict links stem IDs of morphologically complex stems to
# dicts of non-etymologizing to etymologizing segmentations, glossings, and morph IDs
# for example: (YAML)
# sujta-urinate:
#   obj:
#     sujta: suj-ta
#   gloss:
#     urinate: urine-VBZ.INTR
#   ids:
#     - suku-urine
#     - tavbz
etym_dict = {}


def add_to_etym_dict(lexeme_id, obj_tuple, gloss_tuple, ids):
    etym_dict[lexeme_id] = {
        "obj": dict([obj_tuple]),
        "gloss": dict([gloss_tuple]),
        "ids": ids,
    }


# add "etymologizing" information to dict
def add_deriv_etym(x):
    if x["Affix_ID"] != "":
        for f in x["Form"].split(SEP):
            add_to_etym_dict(
                x.name,
                (f.replace("+", ""), f.replace("+", "-")),
                (x["Gloss"], x["Etym_Gloss"]),
                [x["Base_Stem"], x["Affix_ID"]],
            )


lexemes.apply(add_deriv_etym, axis=1)
# dump to yaml for uniparser-yawarana to read

write_file(DATA_PATH / "etym_lookup.yaml", etym_dict, "yaml")

# mapping POS to paradigms
par_dic = {
    "qpro": "uninfl",
    "part": "uninfl",
    "postp": "postp",
    "coord": "uninfl",
    "intj": "uninfl",
    "adv": ["adv", "adv_deriv"],
    "aux": "aux",
    "propn": "uninfl",
    "vt": ["v_tr", "v_tr_nmlz", "vt_aspect"],
    "n": ["noun", "n_deriv"],
    "pn": "pro",
    "vi": ["v_intr", "v_intr_nmlz", "vi_aspect"],
    "ideo": "uninfl",
    "rel": "uninfl",
    "dem": "uninfl",
}
# different POS have different paradigms, nouns are more complex
def get_paradigms(key):
    if isinstance(par_dic[key], list):
        return par_dic[key]
    return [par_dic[key]]


def get_noun_paradigms(rec):
    for val, default in [("NPERT", "0"), ("2_Prefix", "new")]:
        if rec[val] == "":
            rec[val] = default
    if rec["PERT"] == "":
        if rec["Form"][0][-1] == "u":
            rec["PERT"] = "ru"
        else:
            rec["PERT"] = "ri"
    if rec["Form"][0][0] in ["a", "e", "i", "o", "u", "ï", "ë"]:
        seg = "v"
    else:
        seg = "c"
    paradigm_str = f"""noun_{seg}_{rec["2_Prefix"]}_{rec["PERT"]}_{rec["NPERT"]}"""
    return [paradigm_str, "n_deriv"]


# generate a uniparser-morph readable lexicon entry from a record
def create_lexeme_entry(data, paradigms=None, deriv_links=None):
    paradigms = paradigms or []
    deriv_links = deriv_links or []
    lex_str = ["-lexeme"]
    if "Stem" not in data:
        form_string = "|".join(["." + x + "." for x in data["Form"]])
    else:
        form_string = data["Stem"]
    fields = {
        "lex": data["Lexeme_ID"],
        "stem": form_string,
        "trans_en": data["Translation"],
        "gloss": data["Gloss"],
        "gramm": ",".join(data["POS"].split(",") + data["Gramm"].split(",")).strip(","),
        "std": data["Form"][0],
    }
    fields["id"] = data["ID"]
    for field, value in fields.items():
        lex_str.extend([f" {field}: {value}"])
    for paradigm in paradigms:
        lex_str.extend([f" paradigm: {paradigm}"])
    for derivlink in deriv_links:
        lex_str.extend([f" deriv-link: {derivlink}"])
    return "\n".join(lex_str)


# list of lexicon entries
lexemes_str = []
# determine the proper paradigms for a lexicon entry and add it to the list
def add_paradigms(lex):
    lex["Form"] = [y.replace("+", "").replace("-", "") for y in lex["Form"].split(SEP)]
    lex["Lexeme_ID"] = lex["ID"]
    if lex["Paradigm"] == "":
        paradigms = []
        if lex["POS"] == "n":
            paradigms.extend(get_noun_paradigms(lex))
        else:
            for x in lex["POS"].split("; "):
                paradigms.extend(get_paradigms(x))
    else:
        paradigms = lex["Paradigm"].split("; ")
    lexemes_str.append(create_lexeme_entry(lex, paradigms))


lexemes.apply(add_paradigms, axis=1)
lexemes["Form"] = lexemes["Form"].apply(lambda x: x[0])
lexemes_str.append(read_file("data/manual_lexemes.txt"))
# uniparser-morph txt file for lexemes
write_file(DATA_PATH / "lexemes.txt", "\n\n".join(lexemes_str))

# paradigms are largely defined manually,
# but the cross-cutting inflectional classes in nouns
# are generated. four parameters defining inflectional classes:
# * initial segment
# * pertensive suffix
# * non-pertensive suffix
# * old or new second person marker
noun_class_parameters = [
    ["c", "v"],
    ["ri", "ru", "ti", "i", "0"],
    ["të", "0"],
    ["old", "new"],
]
pert_dict = {
    "ri": """ -flex: <.>.ri<.>//<.>.0<.>//<.>.rï<.>
  gloss: PERT
  gramm: pert
  id: rupert""",
    "ru": """ -flex: <.>.ru<.>//<.>.0<.>
  gloss: PERT
  gramm: pert
  id: rupert""",
    "i": """ -flex: <.>.i<.>
  gloss: PERT
  gramm: pert
  id: ipert""",
    "ti": """ -flex: <.>.ti<.>//<.>.j<.>
  gloss: PERT
  gramm: pert
  id: tipert""",
    "0": """ -flex: <.>.<.>
  gramm:""",
}
npert_dict = {
    "të": """ -flex: .të<.>
  gloss: NPERT
  gramm: npert
  id: tenpert
  paradigm: noun_plural""",
    "0": """ -flex: .<.>
  gramm:
  paradigm: noun_plural""",
}
# get all possible combinations of these four parameters
# and create combined paradigms
noun_paradigms = []
for comb in product(*noun_class_parameters):
    paradigm_name = f"noun_{comb[0]}_{comb[-1]}_{comb[1]}_{comb[2]}"
    out = f"-paradigm: {paradigm_name}"
    out += "\n" + pert_dict[comb[1]]
    out += f"\n  paradigm: noun_pref_{comb[-1]}_{comb[0]}"
    out += "\n" + npert_dict[comb[2]]
    noun_paradigms.append(out)
# manually coded noun paradigms
manual_noun_paradigms = read_file("data/noun_paradigms.yaml")
# manually coded other paradigms
paradigms_str = manual_noun_paradigms + "\n\n" + "\n\n".join(noun_paradigms)
other_paradigms = read_file("data/paradigms.yaml")
# write for uniparser-morph
write_file(DATA_PATH / "paradigms.txt", paradigms_str + "\n\n\n\n" + other_paradigms)
# copy 1-to-1 files
for fname in ["lex_rules.txt", "derivations.txt", "clitics.txt", "disambiguation.cg3"]:
    data = read_file(Path("data") / fname)
    write_file(DATA_PATH / f"{fname}", data)
# bad analyses are stored as yaml
# convert to uniparser-yaml
dump(load("data/bad_analyses.yaml"), DATA_PATH / "bad_analyses.txt", mode="json")
