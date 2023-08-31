# Veri setinde yer alan değişkenler;
# master_id : Eşsiz müşteri numarası
# order_channel: alışveriş yapılan platformaait hangi kanalın kullanıldığı (Android, İOS, Desktop, Mobile)
# last_order_channel: en son alışverişin yapıldığı kanal
# firs_order_date: müşterinin yaptığı ilk alışveriş tarihi
# last_order_date: müşterinin yaptığı son alışveriş tarihi
# last_order_date_offline: Müşterinin offline platformda yaptığı son alışveriş tarihi
# order_num_total_ever_online: müşterinin online platformda yaptığı toplam alışveriş sayısı
# order_num_total_ever_offline: müşterinin oflineda yaptığı toplam alışveriş sayısı
# customer_value_total_ever_offline: müşterinin offline alışverişlerde ödediği toplam ücret
# customer_value_total_ever_online: müşterinin online alışverişlerinde ödediği toplam ücret
# interested_in_categories_12: müşterinin son 12 ayda alışveriş yaptığı kategorilerin listesi

#GÖREV 1
############### ADIM1
import datetime as dt
import pandas as pd

pd.set_option( "display.max_columns", None )
pd.set_option( "display.float_format", lambda x: "%.3f" % x )
pd.set_option( "display.width", 1000 )
df_ = pd.read_csv( "C:/Users/esman/PycharmProjects/datasets/flo_data_20k.csv" )
df = df_.copy()
################# ADIM 2
df.head(10)
#veri setindeki değişkenleri en yukarıda tanımladım
df.shape
df.columns
df.describe().T
df.isnull().sum()
df.info()
df["order_channel"].nunique()
df["order_channel"].value_counts().head()
df["last_order_channel"].value_counts().head()

############## ADIM 3
#toplam alışveriş sayısı
df["order_num_total"] = df["order_num_total_ever_online"] + df["order_num_total_ever_offline"]
#toplam harcamalar
df["customer_value_total"] = df["customer_value_total_ever_online"] + df["order_num_total_ever_offline"]
df.head()

############# ADIM 4
df.info()
date_columns = df.columns[df.columns.str.contains("date")]
df[date_columns] = df[date_columns].apply(pd.to_datetime)
df.info()

############ADIM 5:
#alışveriş kanallarındaki müşteri sayısını, ürün sayısını ve toplam harcamaların dağılımı
df.groupby("order_channel").agg({"master_id": lambda master_id: master_id.count(),
                                 "order_num_total": lambda order_num_total: order_num_total.sum(),
                                 "customer_value_total": lambda customer_value_total: customer_value_total.sum()
})

############### ADIM6
df.sort_values("customer_value_total", ascending=False)[:10]

########### ADIM7
df.sort_values("order_num_total", ascending=False)[:10]

##############ADIM 8
def data_prep(dataframe):
    df["order_num_total"] = df["order_num_total_ever_online"] + df["order_num_total_ever_offline"]
    df["customer_value_total"] = df["customer_value_total_ever_online"] + df["order_num_total_ever_offline"]
    date_columns = dataframe.columns[dataframe.columns.str.contains("date")]
    dataframe[date_columns] = dataframe[date_columns].apply(pd.to_datetime)
    return df

#GÖREV 2
#ADIM1
df["last_order_date"].max() #son alışveriş tarihi
analysis_date = dt.datetime(2021, 6,1)

#adım2,3,4
rfm = pd.DataFrame()
rfm["customer_id"] = df["master_id"]
rfm["recency"] = (analysis_date - df["last_order_date"]).astype("timedelta64[D]") #gün cinsinden istediğim için; timedelta64[D].
rfm["frequency"] = df["order_num_total"] #ürün sayısı
rfm["monetary"] = df["customer_value_total"] #toplam harcama miktarı
rfm.head()

##GÖREV 3
#ædım1
rfm["recency_score"] = pd.qcut(rfm["recency"], 5, labels = [5, 4, 3, 2, 1])
#rank(method = "first"): ilk bulduğun sınıfı ilk segemente at
rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method = "first"), 5, labels = [1, 2, 3, 4, 5])
rfm["monetary_score"] = pd.qcut(rfm["monetary"], 5, labels= [1, 2, 3, 4, 5])
rfm.head()
#adım2
rfm["RF_SCORE"]=(rfm["recency_score"].astype(str) + rfm["frequency_score"].astype(str))
rfm.head()
#adım3
rfm["RFM_SCORE"] = (rfm["recency_score"].astype(str) + rfm["frequency_score"].astype(str) + rfm["monetary_score"].astype(str))
rfm.head()

#GÖREV 4
#adım1,2
seg_map = {
    r"[1-2][1-2]": "hibernating",
    r"[1-2][3-4]": "at_Risk",
    r"[1-2]5": "cant_loose",
    r"3[1-2]": "about_to_sleep",
    r"33": "need_attention",
    r"[3-4][4-5]": "loyal_customers",
    r"41": "promising",
    r"51": "new_customers",
    r"[4-5][2-3]": "potential_loyalists",
    r"5[4-5]": "champions",
}
rfm["segment"] = rfm["RFM_SCORE"].replace( seg_map, regex=True )
rfm = rfm[["recency", "frequency", "monetary", "segment"]]

#görev5
#adım1: segmentlerin r,f,m ortalamalarını incele
rfm[["seegment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count", "sum"])

#adım 2
# sadık ve kadın kategorisinden kişileri yeni csv dosyasında kaydet
target_segments_customer_ids = rfm[rfm["segment"].isin(["champions", "loyal_customers"])]["customer_id"]
cust_ids = df[(df["master_id"].isin(target_segments_customer_ids)) & (df["interested_in_categories_12"].str.contains("KADIN"))]["master_id"]
cust_ids.to_csv("yeni-marla-hedef-müşteri_id.csv", index=False)
cust_ids.shape

rfm.head()

#erkek çocuk ürünlerinde %40a yakın indirim bulunmaktadır. bu indirimle ilgili kategorilerle ilgilenen geçmişte iyi müşterilerden olan ama
#uzun süredir alışveriş yapmayan ve yeni gelen müşteriler özel olarak hedef alınmak isteniliyor.
#uygun profildeki müşterilerin is' lerini csv dosyasını "indirim" olarak kaydedin.

target_segments_customer_ids = rfm[rfm["segment"].isin(["cant_loose", "atrisk", "hibernating", "new_customers"])]["customer_id"]
cust_ids = df[(df["master_id"].isin(target_segments_customer_ids)) & ((df["interested_in_categories_12"].str.contains("ERKEK")) | (df["interested_in_categories_12"].str.contains("COCUK")))]["master_id"]
cust_ids.to_csv("indirim-hedef-müşteri_ids.csv", index=False)
