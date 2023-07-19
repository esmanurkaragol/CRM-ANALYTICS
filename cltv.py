#Veri Seti: retail II , ingiltere merkezli online bir satış mağazasına ait.
#C:\Users\esman\Downloads\crmAnalytics-221211-021237.zip\crmAnalytics\datasets

#Veri setinde yer alan değişkenler;
#InoviceNo: Fatura numarası. Her işleme yani faturaya ait eşsiz numara. Cile başlıyorsa iptal edilen işlem.
#StockCode: Her bir ürün için eşsiz numara.
#Description: Ürün ismi
#Quantity: Ürün adedi. Faturalardaki ürünlerden kaçar tane satıldığını ifade edmektedir.
#InoviceDate: Fatura tarihi ve zaman
#UnitPrice: Ürün fiyatı (sterlin cinsinden)
#CustomerID: Eşsiz müşteri numarası
#Country: Müşterinin yaşadığı ülkenin ismi

#cltv değerlerini hesaplayıp segmentlere ayıracağız

import pandas as pd
from sklearn.preprocessing import MinMaxScaler
pd.set_option("display.max_columns", None)
#pd.set_option("display.max_rowns", None)
pd.set_option("display.float_format", lambda x: "%.3f" %x)
df_ = pd.read_excel("C://Users/esman/PycharmProjects/datasets/online_retail_II.xlsx", sheet_name="Year 2009-2010")
df =df_.copy()
df.head()
df.isnull().sum()
df = df[~df["Invoice"].str.contains("C", na=False)]
df.describe().T
df = df[(df["Quantity"] > 0)]
df.dropna(inplace=True)
df["TotalPrice"] = df["Quantity"] * df["Price"]
df.head()

#cltv hesaplamak için işlemleri yap.
cltv_c = df.groupby("Customer ID").agg({ "Invoice" : lambda x: x.nunique(), #her müşterinin eşsiz fatura sayısını verir (Total Transaction )
                                         "Quantity": lambda x: x.sum(),
                                         "TotalPrice": lambda x: x.sum()
                                        })
#Ortalama Sipariş Değeri (Average Order Value) =total price/ total_transaction
cltv_c.head()

cltv_c.columns =["total_transaction", "total_unit", "total_price"]
#recency=total_transaction
#monetary = total_price


cltv_c["average_order_value] = cltv_c["total_price"]/ cltv_c["total_transaction"]

#Satın Alma Sıklığı (Purchase Frequency)
cltv_c.head()
cltv_c["purchase_frequency] = cltv_c["total_transaction"] / cltv_c.shape[0]
#satırlar eşsiz müşteri temsil ediyordu o zaman 0.indexine bak
cltv_c.shape[0]

#Tekrarlama Oranı(Repeat Rate)= birden fazla alışveriş yapan müşteri sayısı/tüm müşteriler
#öncelikle olarak birden fazla alışveriş yapann müşterileri bul
cltv_c[cltv_c["total_transaction"] >1].shape[0]
#tüm müşterilere erişmek için
cltv_c.shape[0]
#repeat rate
repeat_rate = cltv_c[cltv_c["total_transaction"] >1].shape[0]  /  cltv_c.shape[0]

# Kaybetme Oranı (Churn Rate)
churn_rate = 1 - repeat_rate

#profit margin (kar marjı) = total_price * 0.10
cltv_c["profit_margin"] = cltv_c ["total_price"] * 0.10

#customer value = average_order_value * purchase_frequency
cltv_c["customer_value"] = cltv_c["average_order_value"] * cltv_c["purchase_frequency"]

#CLTV = (customer_value / churn_rate) * profit_margin
#churn rate sabit olduğu için bir df içinden çağırmana gerek yok.
cltv_c["cltv"] = (cltv_c["customer_value"] / churn_rate) * cltv_c["profit_margin"]

#cltv ye göre sırala ve azalan şekilde olsun diye false diyorum
cltv_c.sort_values(by= "cltv", ascending=False).head()
cltv_c.describe().T

#segmentlerin oluşturulması
#by="cltv" cltv ye göre sırala
cltv_c.sort_values(by= "cltv", ascending=False).head().tail()
cltv_c["segment"] = pd.qcut(cltv_c["cltv"],4, labels= ["D", "C", "B", "A"])
cltv_c.sort_values(by= "cltv", ascending=False).head()

cltv_c.groupby("segment").agg({"count", "mean", "sum"})

#cltv_c dosyasını dışarı aktar
cltv_c.to_csv("cltv_c.csv")

#Tüm İşlemlerin Fonksiyonlaştırılması
def create_cltv_c(dataframe, profit=0.1):
    #veriyi hazırlama
    dataframe = dataframe[~datafraame["Invoice"].str.contains("C",na=False)]
    dataframe=  dataframe[(dataframe["Quantity"] > 0)]
    dataframe.dropna(inplace=True)
    dataframe["TotalPrice"] = dataframe["Quantity"] * dataframe["Price"]
    cltv_c = dataframe.groupby("Customer ID").agg({ "Invoice" : lambda x: x.nunique(),
                                                    "Quantity": lambda x: x.sum(),
                                                    "TotalPrice": lambda x: x.sum()
                                                  })
    cltv_c.columns = ["total_transection", "total_unit", "total_price"]

    #avg_order_value
    cltv_c["avg_order_value"] = cltv_c["total_price"] / cltv_c["total_transaction"]

    #purchase_frequency
    cltv_c["purchase_frequency"] = cltv_c["total_transection"] / cltv_c.shape[0]

    #repeat_rate
    repeat_rate = cltv_c[cltv_c["total_transaction"] > 1].shape[0] / cltv_c.shape[0]

    #churn_rate
    churn_rate = 1 - repeat_rate

    # profit margin
    cltv_c["profit_margin"] = cltv_c["total_price"] * profit

    # customer value = average_order_value * purchase_frequency
    cltv_c["customer_value"] = cltv_c["avg_order_value"] * cltv_c["purchase_frequency"]

    # CLTV = (customer_value / churn_rate) * profit_margin
    # churn rate sabit olduğu için bir df içinden çağırmana gerek yok.
    cltv_c["cltv"] = (cltv_c["customer_value"] / churn_rate) * cltv_c["profit_margin"]

    #segment
    cltv_c["segment"] = pd.qcut( cltv_c["cltv"], 4, labels=["D", "C", "B", "A"] )

    return cltv_c

df = df_.copy()
clv = create_cltv_c(df)
