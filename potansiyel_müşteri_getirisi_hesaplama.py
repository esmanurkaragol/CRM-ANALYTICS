import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 500)
#########################  GÖREV1
#soru1
df = pd.read_csv("datasets/persona.csv")
df.head()
df.tail()
df.shape
df.info()
df.columns
df.index
df.describe().T
df.isnull().values.any()
df.isnull().sum()
#soru2
def get_col_summary(df, col):
    print(f"Eşsiz değerlerin toplam sayısı: {df[col].nunique()}")
    print(f"Her veri için toplam değer sayısı: {df[col].value_counts()}")

get_col_summary(df, "SOURCE")
#soru3
get_col_summary(df, "PRİCE")

#soru4

