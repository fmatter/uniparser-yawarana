import pandas as pd
from humidifier import humidify

SEP = "; "
df = pd.read_csv(
    "/home/florianm/Dropbox/research/cariban/yawarana/yawarana_dictionary/annotated_dictionary.csv",
    keep_default_na=False,
)
df = df[df["Translation_Root"] != ""]
df.rename(columns={"Translation_Root": "Translation"}, inplace=True)

for c in ["Paradigm", "Gramm"]:
    if c not in df.columns:
        df[c] = ""

# cut off lemma-forming suffixes
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


roots = df.apply(trim_suff, axis=1)

roots["Gloss"] = roots["Translation"].apply(lambda x: x.split(SEP)[0])
roots["Form"] = roots.apply(lambda x: SEP.join(
        [y for y in x["Form"].split(SEP) + x["Variants"].split(SEP)]
    ).strip(SEP), axis=1)
roots["ID"] = roots.apply(lambda x: humidify(x["Form"].split(SEP)[0] + " " + x["Gloss"]), axis=1)
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
roots = roots[keep_cols]
roots.to_csv("data/roots.csv", index=False)
