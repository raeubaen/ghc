import pandas as pd

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("ghcfile", help="File with output of GHC - bad channels only")
parser.add_argument("stfile", help="File with channel status output from DQM")
args = parser.parse_args()


df_value = pd.read_csv(args.ghcfile, na_values=["N/A"])
df_value = df_value[['iEta', 'iPhi', 'iX', 'iY', 'iZ', 'SM', 'TT', 'PED_ON_RMS_G12', 'Flags']]
df_value = df_value.fillna(0)
df_value["x_phi"] = df_value.iPhi + df_value.iX
df_value["y_eta"] = df_value.iEta + df_value.iY

df_value = df_value.loc[ df_value.Flags.str.contains("LRG12") | df_value.Flags.str.contains("VLRG12") ]
df_value = df_value.loc[ df_value.SM.str.contains("EB") ]

df_value = df_value[['SM', 'TT', "x_phi", "y_eta", 'PED_ON_RMS_G12']]

df_value.columns=['label',  'tt_ccu', 'x_phi', 'y_eta', 'PED_ON_RMS_G12']

df_value["label"] = df_value['label'].str.replace(
    r'(EB[+-])(\d{1})$',
    lambda m: f"{m.group(1)}0{m.group(2)}",  # Add leading 0
    regex=True
)

df_value = df_value.loc[df_value.PED_ON_RMS_G12 > 5]


df_status = pd.read_csv(args.stfile)
df_status = df_status[['label',  'tt_ccu', 'x_phi', 'y_eta', 'status']]

df_status = df_status.loc[ df_status.label.str.contains("EB") ]
df_status = df_status.loc[(df_status.status == 3) | (df_status.status == 4) | (df_status.status == 11)]

merge_keys = ['label', 'tt_ccu', 'x_phi', 'y_eta']

df_status['_source'] = 'status'
df_value['_source'] = 'values'

combined = pd.concat([df_status[merge_keys + ['_source']], df_value[merge_keys + ['_source']]])

counts = combined.groupby(merge_keys)['_source'].agg(list).reset_index()

both = counts[counts['_source'].apply(lambda x: set(x) == {'status', 'values'})]
only_values = counts[counts['_source'].apply(lambda x: x == ['values'])]
only_status = counts[counts['_source'].apply(lambda x: x == ['status'])]

df_both = pd.merge(both[merge_keys], df_status, on=merge_keys)
df_both = pd.merge(df_both, df_value, on=merge_keys, suffixes=('_status', "_values"))

df_only_values = pd.merge(only_values[merge_keys], df_value, on=merge_keys)
df_only_status = pd.merge(only_status[merge_keys], df_status, on=merge_keys)

#print("Both\n", len(df_both), "\n", df_both, "\n\n")
#print("only DQM ch. status\n", len(df_only_status), "\n", df_only_status, "\n\n")

print("only GHC\n", len(df_only_values), "\n", df_only_values, "\n\n")

df_only_values.apply(lambda row: print(f"{{'x_phi':{row.x_phi},'y_eta':{row.y_eta},'SM':'{row.label}'}}, ", end=""), axis=1)
