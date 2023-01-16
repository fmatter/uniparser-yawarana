import pandas as pd
from humidifier import humidify
import yaml
import sys
from pathlib import Path
from itertools import product
import json

SEP = "; "
DATA_PATH = Path("src/uniparser_yawarana/data")

# roots from the FLEx dictionary
roots = pd.read_csv("data/roots.csv", keep_default_na=False, index_col=0)
# roots manually added to the CLDF dataset for some reason
manual_roots = pd.read_csv("data/manual_roots.csv", keep_default_na=False)
roots = pd.concat([roots, manual_roots])

roots["Etym_Gloss"] = roots["Gloss"]
roots["ID"] = roots.apply(lambda x: humidify(x["Form"] + "-" + x["Gloss"]), axis=1)


# this dict links stem IDs of morphologically complex stems to
# "etymologizing" segmentations, glossings, and morph IDs
# example:
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


# read stems identified as being derived from some other stem
def read_deriv(name, pos):
    df = pd.read_csv(f"data/derivations/{name}.csv", keep_default_na=False)
    df["POS"] = pos
    df["Affix_ID"] = name
    return df


# transitive verbalizer -ka
kavbz = read_deriv("kavbz", "vt")
kavbz["Suffix_Gloss"] = "VBZ.TR"

# intransitive verbalizer -ta
tavbz = read_deriv("tavbz", "vi")
tavbz["Suffix_Gloss"] = "VBZ.INTR"


def find_detransitivizer(s):
    if s.startswith("s"):
        return "dt2"
    elif s.startswith("ëj"):
        return "dt1"
    elif s.startswith("at"):
        return "dt3"
    else:
        raise ValueError
        sys.exit(1)


# detransitivized verbs
detrz = read_deriv("detrz", "vi")
detrz["Affix_ID"] = detrz["Form"].apply(find_detransitivizer)
detrz["Prefix_Gloss"] = "DETRZ"

# assemble derivations, generate human-readable IDs and set as index
derivations = pd.concat([kavbz, tavbz, detrz])
derivations["Form_Bare"] = derivations["Form"].apply(lambda x: x.replace("+", ""))
derivations["Gloss"] = derivations["Translation"].apply(lambda x: x.replace(" ", "."))
derivations["ID"] = derivations.apply(
    lambda x: humidify(f"{x['Form_Bare'].split(SEP)[0]}-{x['Translation']}"), axis=1
)
derivations.set_index("ID", inplace=True)

# todo DELETE THIS AND FIX
# for now, leave out derivations whose base is not found in roots
derivations = derivations[derivations["Base_Lexeme"].isin(roots.index)]
# assemble all lexemes
lexemes = pd.concat([roots, derivations])


# the etymological gloss is based on the gloss of the base
# and the gloss of the derivational affix
def add_etym_gloss(rec):
    if not pd.isnull(rec["Prefix_Gloss"]):
        rec["Etym_Gloss"] = (
            rec["Prefix_Gloss"] + "-" + lexemes.loc[rec["Base_Lexeme"]]["Etym_Gloss"]
        )
    elif not pd.isnull(rec["Suffix_Gloss"]):
        rec["Etym_Gloss"] = (
            lexemes.loc[rec["Base_Lexeme"]]["Etym_Gloss"] + "-" + rec["Suffix_Gloss"]
        )
    return rec


lexemes = lexemes.apply(lambda x: add_etym_gloss(x), axis=1)


# add "etymologizing" information to dict
def add_deriv_etym(x):
    if not pd.isnull(x["Affix_ID"]):
        add_to_etym_dict(
            x["ID"],
            (x["Form"].replace("+", ""), x["Form"].replace("+", "-")),
            (x["Gloss"], x["Etym_Gloss"]),
            [x["Base_Lexeme"], x["Affix_ID"]],
        )


lexemes.apply(
    lambda x: add_deriv_etym(x),
    axis=1,
)

# dump to yaml for uniparser-yawarana to read
with open(DATA_PATH / "etym_lookup.yaml", "w") as f:
    yaml.dump(etym_dict, f)


# mapping POS to paradigms
par_dic = {
    "qpro": "uninfl",
    "part": "uninfl",
    "postp": "postp",
    "coord": "uninfl",
    "intj": "uninfl",
    "adv": ["adv"],
    "aux": "aux",
    "propn": "uninfl",
    "vt": ["v_tr", "v_tr_nmlz"],
    "n": ["noun", "n_deriv"],
    "pn": "pro",
    "vi": ["v_intr", "v_intr_nmlz"],
    "ideo": "uninfl",
    "rel": "uninfl",
    "det": "uninfl",
}


# different POS have different paradigms, nouns are more complex
def get_paradigms(key):
    if isinstance(par_dic[key], list):
        return par_dic[key]
    return [par_dic[key]]


def get_noun_paradigms(rec):
    for val, default in [("PERT", "ri"), ("NPERT", "0"), ("2_Prefix", "new")]:
        if rec[val] == "":
            rec[val] = default
    if rec["Form"][0][0] in ["a", "e", "i", "o", "u", "ï", "ë"]:
        seg = "v"
    else:
        seg = "c"
    paradigm_str = f"""noun_{seg}_{rec["2_Prefix"]}_{rec["PERT"]}_{rec["NPERT"]}"""
    return [paradigm_str, "n_deriv"]


# generate a uniparser-morph readable lexicon entry from a record
def create_lexeme_entry(data, paradigms=[], deriv_links=[]):
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
    lex["Form"] = lex["Form"].split(SEP)
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

# uniparser-morph txt file for lexemes
with open(DATA_PATH / "lexemes.txt", "w") as f:
    f.write("\n\n".join(lexemes_str))

# paradigms are largely defined manually,
# but the cross-cutting inflectional classes in nouns
# are generated. four parameters defining inflectional classes:
# * initial segment
# * pertensive suffix
# * non-pertensive suffix
# * old or new second person marker
noun_class_parameters = [["c", "v"], ["ri", "ti", "0"], ["të", "0"], ["old", "new"]]


pert_dict = {
    "ri": """ -flex: <.>.ru<.>//<.>.ri<.>//<.>.0<.>
  gloss: PERT
  gramm: pert
  id: rupert""",
    "ti": """ -flex: <.>.ti<.>
  gloss: PERT
  gramm: pert
  id: tipert""",
    "0": """ -flex: <.>.<.>
  gramm:""",
}


npert_dict = {
    "të": """ -flex: .të
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
with open("data/noun_paradigms.yaml", "r") as f:
    manual_noun_paradigms = f.read()

# manually coded other paradigms
paradigms_str = manual_noun_paradigms + "\n\n".join(noun_paradigms)
other_paradigms = open("data/paradigms.yaml", "r").read()

# write for uniparser-morph
with open(DATA_PATH / "paradigms.txt", "w") as f:
    f.write(paradigms_str + "\n\n\n\n" + other_paradigms)

# copy 1-to-1 files
for fname in ["lex_rules.txt", "disambiguation.cg3", "derivations.txt"]:
    data = open(Path("data") / fname).read()
    with open(DATA_PATH / f"{fname}", "w") as f:
        f.write(data)

# bad analyses are stored as yaml
# convert to uniparser-yaml
with open("data/bad_analyses.yaml", "r") as f:
    bad_analyses = yaml.load(f, yaml.SafeLoader)
with open(DATA_PATH / "bad_analyses.txt", "w") as f:
    json.dump(bad_analyses, f, ensure_ascii=False, indent=4)
