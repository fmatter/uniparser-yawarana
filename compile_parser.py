import pandas as pd
from humidifier import humidify
import yaml
import sys
from pathlib import Path
from itertools import product, chain
import json
import re

SEP = "; "  # separator between variants of same form
DATA_PATH = Path("src/uniparser_yawarana/data")  # the python package's data folder
DERIV_SEP_PATTERN = cogseppattern = f"[{''.join(['+', '-'])}]"
# enriched LIFT export from MCMM
dic = pd.read_csv(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_dictionary/annotated_dictionary.csv",
    keep_default_na=False,
)
# keep only roots
roots = dic[dic["Translation_Root"] != ""]
roots.rename(columns={"Translation_Root": "Translation"}, inplace=True)


def trim_suff(row):
    if row["POS"] in ["vt", "vi", "n"]:
        forms = row["Form"].split(SEP)
        treated_forms = []
        for form in forms:
            for suff in ["ri", "ru"]:
                if form.endswith(suff):
                    form = "".join(form.rsplit(suff, 1))
                    if form not in treated_forms:
                        treated_forms.append(form)
                    break
            if form not in treated_forms:
                treated_forms.append(form)
        row["Form"] = SEP.join(treated_forms)
    return row


roots = roots.apply(trim_suff, axis=1)  # cut off lemma-forming suffixes
roots["Gloss"] = roots["Translation"].apply(
    lambda x: x.split(SEP)[0].replace(" ", "_")
)  # get a single gloss
roots["Form"] = roots.apply(
    lambda x: SEP.join(
        [y for y in x["Form"].split(SEP) + x["Variants"].split(SEP)]
    ).strip(SEP),
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
manual_roots["Translation"] = manual_roots["Gloss"]
# manual_roots["Form"] = manual_roots.apply(lambda x: SEP.join(x["Form"]), axis=1)# get variants
roots = pd.concat([roots, manual_roots])  # combine with dictionary roots
roots["ID"] = roots.apply(
    lambda x: humidify(x["Form"].split(SEP)[0] + " " + x["Gloss"]), axis=1
)  # create IDs
roots.set_index("ID", inplace=True, drop=False)  # make retrievable quickly
roots["Etym_Gloss"] = roots[
    "Gloss"
]  # roots cannot have an "etymologizing" (showing derivational structure) gloss
roots.to_csv("var/roots.csv", index=False)

lost_roots = pd.read_csv("data/etym_lexemes.csv")  #
lost_roots["ID"] = lost_roots.apply(
    lambda x: humidify(f"{x['Form']}-{x['Translation']}"), axis=1
)
lost_roots.set_index("ID", inplace=True)
lost_roots["Etym_Gloss"] = lost_roots["Translation"]

deriv_morphs = pd.read_csv(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana-sketch-cldf/etc/derivation_morphs.csv"
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

# method for finding out which detransitivizer is in a stem
def find_detransitivizer(s):
    if s.startswith("s"):
        return "dt2"
    elif s.startswith("ëj"):
        return "dt1"
    elif s.startswith("at"):
        return "dt3"
    elif s.startswith("a"):
        return "dt4"
    else:
        raise ValueError
        sys.exit(1)


detrz = read_deriv("detrz", "vi")  # detransitivized verbs
detrz["Affix_ID"] = detrz["Form"].apply(find_detransitivizer)
detrz["Prefix_Gloss"] = "DETRZ"

derivations = pd.concat([kavbz, tavbz, macaus, detrz])  # assemble derived stems


def disassemble_stem(rec, stem_dic=None):
    if not stem_dic:
        stem_dic = {}
        for pos in ["Prefix", "Stem", "Suffix"]:
            stem_dic[pos] = {}
            for level in ["ID", "Parts", "Gloss"]:
                stem_dic[pos][level] = []
    if pd.isnull(rec.Prefix_Gloss):
        empty = "Prefix"
        filled = "Suffix"
        stemparts, affparts = re.split(DERIV_SEP_PATTERN, rec.Form)
    else:
        empty = "Suffix"
        filled = "Prefix"
        affparts, stemparts = re.split(DERIV_SEP_PATTERN, rec.Form)
    stem_dic[filled]["ID"].append(rec["Affix_ID"])
    stem_dic[filled]["Gloss"].append(rec[f"{filled}_Gloss"])
    stem_dic[filled]["Parts"].append(affparts)
    if rec.Base_Stem in roots.index:  # morphologically simple stem
        stem_dic["Stem"]["ID"] = [rec.Base_Stem]
        stem_dic["Stem"]["Parts"] = [stemparts]
        stem_dic["Stem"]["Gloss"] = [roots.loc[rec.Base_Stem]["Gloss"]]
        return stem_dic
    elif rec.Base_Stem in derivations.index:  # morphologically complex stem base
        return disassemble_stem(derivations.loc[rec.Base_Stem], stem_dic)
    stem_dic["Stem"]["ID"] = []
    stem_dic["Stem"]["Parts"] = [stemparts]
    stem_dic["Stem"]["Gloss"] = []
    return stem_dic


# function for processing morphologically complex stems
stem_morphs = []  # morphological components of stems
positions = ["Prefix", "Stem", "Suffix"]  # positions


def process_stem(rec):
    stemid = rec["ID"]
    stem_dic = disassemble_stem(rec)
    ids = chain(*[stem_dic[pos]["ID"] for pos in positions])
    parts = chain(*[stem_dic[pos]["Parts"] for pos in positions])
    glosses = chain(*[stem_dic[pos]["Gloss"] for pos in positions])
    for idx, (m_id, gloss) in enumerate(zip(ids, glosses)):
        stem_morphs.append(
            {
                "ID": f"{stemid}-{idx}",
                "Morph_ID": m_id,
                "Stem_ID": stemid,
                "Index": idx,
                "Gloss": gloss,
            }
        )
    rec["Parts"] = " ".join(parts)
    return rec


derivations["Gloss"] = derivations["Translation"].apply(
    lambda x: x.replace(" ", ".")
)  # todo: use proper glossifying function
derivations["Name"] = derivations["Form"].apply(
    lambda x: x.replace("+", "").replace("-", "")
)
derivations["ID"] = derivations.apply(
    lambda x: humidify(f"{x['Name']}-{x['Translation']}"), axis=1
)  # generate IDs
derivations.set_index("ID", inplace=True, drop=False)  # make quickly retrievable
derivations = derivations.apply(process_stem, axis=1)
stem_morphs = pd.DataFrame.from_dict(stem_morphs)
derivations["Form"] = derivations["Name"]

stem_morphs.to_csv("var/stemparts.csv", index=False)
derivations.to_csv("var/stems.csv", index=False)

# assemble all stems (called lexemes in the uniparser context)
lexemes = pd.concat([roots, derivations])
lexemes = lexemes.fillna("")
# the etymological gloss is based on the gloss of the base
# and the gloss of the derivational affix
def add_etym_gloss(rec):
    if rec["Prefix_Gloss"] != "":
        if rec["Base_Stem"] in lexemes:
            rec["Etym_Gloss"] = (
                rec["Prefix_Gloss"] + "-" + lexemes.loc[rec["Base_Stem"]]["Etym_Gloss"]
            )
        elif rec["Base_Stem"] in lost_roots:
            rec["Etym_Gloss"] = (
                rec["Prefix_Gloss"]
                + "-"
                + lost_roots.loc[rec["Base_Stem"]]["Etym_Gloss"]
            )
    elif rec["Suffix_Gloss"] != "":
        if rec["Base_Stem"] in lexemes:
            rec["Etym_Gloss"] = (
                lexemes.loc[rec["Base_Stem"]]["Etym_Gloss"] + "-" + rec["Suffix_Gloss"]
            )
        elif rec["Base_Stem"] in lost_roots:
            rec["Etym_Gloss"] = (
                lost_roots.loc[rec["Base_Stem"]]["Etym_Gloss"]
                + "-"
                + rec["Suffix_Gloss"]
            )
    return rec


lexemes = lexemes.apply(lambda x: add_etym_gloss(x), axis=1)
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
        add_to_etym_dict(
            x.name,
            (x["Form"].replace("+", ""), x["Form"].replace("+", "-")),
            (x["Gloss"], x["Etym_Gloss"]),
            [x["Base_Stem"], x["Affix_ID"]],
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
lexemes["Form"] = lexemes["Form"].apply(lambda x: x[0])

with open("data/manual_lexemes.txt", "r") as f:
    lexemes_str.append(f.read())

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
paradigms_str = manual_noun_paradigms + "\n\n" + "\n\n".join(noun_paradigms)
other_paradigms = open("data/paradigms.yaml", "r").read()

# write for uniparser-morph
with open(DATA_PATH / "paradigms.txt", "w") as f:
    f.write(paradigms_str + "\n\n\n\n" + other_paradigms)

# copy 1-to-1 files
for fname in ["lex_rules.txt", "disambiguation.cg3", "derivations.txt", "clitics.txt"]:
    data = open(Path("data") / fname).read()
    with open(DATA_PATH / f"{fname}", "w") as f:
        f.write(data)

# bad analyses are stored as yaml
# convert to uniparser-yaml
with open("data/bad_analyses.yaml", "r") as f:
    bad_analyses = yaml.load(f, yaml.SafeLoader)
with open(DATA_PATH / "bad_analyses.txt", "w") as f:
    json.dump(bad_analyses, f, ensure_ascii=False, indent=4)
