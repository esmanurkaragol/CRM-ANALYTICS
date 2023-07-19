# 1.İŞ PROBLEMİ (Business Problem)
#Bir e-ticaret şirketi müşterilerini segmentlere ayırıp bu segmentlere göre pazarlama stratejisi belirlemek istiyor.
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

# 2.Veriyi Anlama(Data Understanding)
import datetime as dt
import pandas as pd
#bütün sutünları gösterir.
pd.set_option("display.max_columns", None)
#tüm satırları gösterir.
#pd.set_option("display.max_rows", None)
# sayısal değişkenlerin virgülden sonra 3 basamağını göstersin diyorum
pd.set_option("display.float_format", lambda x: "%.3f" % x)

df_ = pd.read_excel("C://Users/esman/PycharmProjects/datasets/online_retail_II.xlsx", sheet_name="Year 2009-2010")
df = df_.copy()
df.head()
#veri setinin boyutu (gözlem birimi, değişken bilgisi verir)
df.shape
#eksik değerlere bak
df.isnull().sum()

#Eşsiz ürün-değer sayısı için:
df["Description"].nunique()
#hangi üründen kaçar tane var (stok)?
df["Description"].value_counts().head()
#hangi üründen kaçar tane sipariş edilmiş?
df.groupby("Description").agg({"Quantity": "sum"}).head()
#Quantityleri büyükten küçüğe sıralayalım.
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending = False).head()
#eşsiz invoice sayısı, toplamda kesilen fatura sayısı
df["Invoice"].nunique()
#Fatura başına toplam kaç para kazanılmıştır. bunun için total price değişkeni oluştur.
df["TotalPrice"] = df["Quantity"] * df["Price"]
#invoice (fatura) başına toplam kaç para ödendiğini öğrenmek için
df.groupby("Invoice").agg({"TotalPrice" :"sum"}).head()


########### VERİYİ HAZIRLAMA (Data Preparation)
df.head()
df.shape()
df.isnull().sum()
#verideki eksik değerleri silmek için, değişikliğin kalıcı olması için inplace=true
df.dropna(inplace=True)
df.describe().T
#iade edilen faturaları veri setinden çıkaralım
#~ işaret bunun dışında kalanları seç demektir
#str.contains("C", na=false) --> Başında C olanları getir.
df = df[~df["Invoice"].str.contains("C", na=False)]

#RFM METRİKLERİNİN HESAPLANMASI (Recency, Frequency, Monetary)
df.head()
#burada veriler 2009- 2010 yıllarına ait
# veri seti içinde işlem yapılan son tarihi öğren
df["InvoiceDate"].max()
# o tarih üzerine 2 gün koy ve o gün anlaiz yapılmış gibi kabul et
today_date = dt.datetime(2010,12,11)
type(today_date)
# bu tarih üzerinden R değerleri hesaplanır.
#agg fonksiyonunun key kısmında değişkenleri; value kısımda bu değişkenlere uygulanacak işlemler yazılır. bu da sözlük yapısı içeriisnde olur.
rfm = df.groupby("Customer ID").agg({"InvoiceDate": lambda date: (today_date - date.max()).days,
                                      "Invoice": lambda num: num.nunique(),
                                      "TotalPrice": lambda TotalPrice: TotalPrice.sum()
                                    })
rfm.head()

rfm.columns = ["recency", "frequency", "monetary"]
rfm.describe().T
#monetry 0 olamaz bunları uçur.
rfm = rfm[rfm["monetary"] > 0]
#veri setindeki müşteri sayısı, değişken sayısını verir.
rfm.shape

#####RFM SKORLARININ HESAPLANMASI
#qcut fonksiyonu; verilen değişkendeki değerleri küçükten büyüğe sıralar.
# kaç parçaya ayırmak istiyorsan ona ayırır (,5,).
# ve ayırdıktan sonrada labelları söyle ki ona göre bölümleri isimlendirsin
rfm["recency_score"] = pd.qcut(rfm["recency"], 5, labels=[5,4,3,2,1])

#aynı #işlemi monetary içinde yap
rfm["monetary_score"] = pd.qcut(rfm["monetary"], 5, labels=[1,2,3,4,5])

#frequency
#rfm["frequency_score"] = pd.qcut(rfm["frequency"], 5, labels=[1,2,3,4,5])
#yukarıdaki kod satırında almış olduğumuz hatanın nedeni tekrar eden çok fazla değerin olmasıdır.
#bu problemi çözmek için rank fonksiyonu yazılır, ilk gördüğünü ilk sınıfa ata işlemini yapar.
rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method = "first"), 5, labels=[1,2,3,4,5])
rfm.head()
#2boyutlu grafiği hatırla sadece R ve F değerleri yazıyordu. bu nedenle bu ikisini bir araya getir.
rfm["RFM_SCORE"] = (rfm["recency_score"].astype(str) +
                    rfm["frequency_score"].astype(str))
rfm.head()
rfm.describe().T
#ŞAMPİYON GRUBUNU LİSTELEMEK İÇİN
rfm[rfm["RFM_SCORE"]== "55"]
#ÖNEMİ DÜŞÜK MÜŞTERİLER
rfm[rfm["RFM_SCORE"]== "11"]

#RFM SEGMENTLERİNİN OLUŞTURULMASI VE ANALİZ EDİLMESİ
#regex kullanımı (r)
#RFM İSİMLENDİRİLMESİ
seg_map = {
    r"[1-2][1-2]" : "hibernating",
    r"[1-2][3-4]": "at_Risk",
    #birinci elemanında 1 ya da 2, ikinci elmanında 5 görürsen cant_loose isimlendirmesi yap
    r"[1-2]5": "cant_loose",
    r"3[1-2]": "about_to_sleep",
    #birinci elemanında 3, ikinci elemanında 3 görürsen neeed_attention isimlendirmesi yap.
    r"33": "need_attention",
    r"[3-4][4-5]": "loyal_customers",
    r"41": "promising",
    r"51": "new_customers",
    r"[4-5][2-3]": "potential_loyalists",
    r"5[4-5]": "champions",
}

#regex=true ile skorlar birleştirlmiş olunur
#replace et ---> değiştir
rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)

rfm[["segment", "recency", "frequency", "monetary"]].groupby("segment").agg(["mean", "count"])

rfm[rfm["segment"] == "need_attention"].head()
rfm[rfm["segment"] == "need_attention"].index

#yeni bir df oluştur ve içerisine yeni müşterileri at
new_df = pd.DataFrame()
new_df["new_customer_id"] = rfm[rfm["segment"] == "new_customers"].index
#id lerdeki ondalığı atmak için astype ekle
new_df["new_customer_id"]  = new_df["new_customer_id"].astype(int)
#csv formunda verileri dışarı aktaralım
new_df.to_csv("new_customers.csv")
#rfm.csv dışarı çıkar
rfm.to_csv("rfm.csv")

#Tüm Sürecin Fonksiyonlaştırılması (FUNCTİONALİZATİON)
#create_rfm fonksiyonu yaz, argümanı dataframe.
def create_rfm(dataframe, csv=False):
    #veriyi hazırlama
    dataframe["TotalPrice"] = dataframe["Quantity"] * dataframe["Price"]
    dataframe.dropna(inplace= True) #eksik değerleri uçur
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]

    #RFM METRİKLERİNİN HESAPLANMASI
    today_date = dt.datatime(2011,12,11)
    rfm = dataframe.groupby("Customer ID").agg({"InvoiceDate":  lambda date: (today_date - date.max()).days,
                                                "Invoice" : lambda num: num.nunique(),
                                                "TotalPrice": lambda price: price.sum()
                                                })
    rfm.columns = ["recency", "frequency", "monetary"]
    rfm = rfm[(rfm["monetary"] > 0)]

    #RFM Skorlarının Hesaplanması
    rfm["recency_score"] = pd.qcut(rfm["recency"], 5, labels=[5,4,3,2,1])
    rfm["frequency_score"] = pd.qcut(rfm["frequency"], 5, labels=[1,2,3,4,5])
    rfm["monetary_score"] = pd.qcut(rfm["monetary"], 5, labels=[1,2,3,4,5])

    #cltv_df skorları kategorik değere dönüştürüp df'e eklendi
    rfm["RFM_SCORE"] = (rfm["recency_score"].astype(str) +
                        rfm["frequency_score"].astype(str))

    #segmentlerin isimlendirilmesi
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
    rfm["segment"] = rfm["RFM_SCORE"].replace(seg_map, regex=True)
    rfm = rfm[["recency", "frequency", "monetary", "segment"]]
    rfm.index = rfm.index.astype(int)
    #fonksiyonun başında csv argümanının ön tanımlı değerini false girmiştik
    if csv:
        rfm.to_csv("rfm.csv")

    return rfm

#veri setini en baştaki haline getir.
df = df_.copy()

rfm_new = create_rfm(df, csv=True)

#Müşteri Yaşam Boyu Değeri (Customer Lifetime Value)
#bir müşterinin bir şirketle kurmuş olduğu ilişki-iletişim süresince bu şirkete kazandıracağı parasal değerdir.
#müşterilerin bizimle kuracağı ilişki süresince bize bırakacağı değerin tahmini yapılır