#BG-NBD ve Gamma-Gamma ile CLTV Prediction

#Verinin Hazırlanması (data preperation)
#retail II veri setini kullanıyoruz yine.
#Bir e ticaret şirketi müşterilerini segmentlere ayırıp bu segmentlere göre pazarlama stratejileri belirlemek istiyor
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


############################## CLTV  TAHMİNİ
#Zaman projeksiyonlu olasılıksal lifetime value tahmini

#Gerekli kütüphane ve fonksiyonlar
#pip install lifetimes
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter
from lifetimes.plotting import plot_period_transactions

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 500)
pd.set_option("display.float_format", lambda x: "%.4f" %x)
#cltv hesaplandıktan sonra bunu 0-1 veya 0-100 gibi değerlere çekmek için bu method kullanılır.
from sklearn.preprocessing import MinMaxScaler

#aykırı değerleri belirle ve onları değiştirmen lazım. bunun için 2 fonkdiyona ihityacın var.
#1. outlier_thresholds fonksiyonu: kendisine girilen değer için eşik değer belirler.
#yani aykırı değerleri belirler. örneğin 40, yaş için normal bir değerken 560 değildir, aykırı değerdir.
#işte bu aykırı değerleri baskılamak için eşik değer(outlier) belirlenmesi lazım.
#outlier belirlemek için %25lik çeyrek değeri ve yüzde 75lik çeyrek değer hesaplanır.
#quartile3 = %25lik çeyrek değeri
#quartile1 =yüzde 75lik çeyrek değer
#ama bu projede 0.01 ile 0.99 arasında aldık çeyrek değerleri.
#2. replace_with_thresholds) fonksiyonu
#outlier fonksiyonunda belirlenen üst ve alt limitler ağrılır ve bunlardan daha küçük veya büyük olanlar buraya atanır.

def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit

def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    #dataframe.loc[(dataframe[variable] < low_limit), variable] = low_limit
    dataframe.loc[(dataframe[variable] > up_limit), variable] = up_limit
import pandas as pd
#Verinin OKunması
df_ = pd.read_excel("C:/Users/esman/PycharmProjects/datasets/online_retail_II.xlsx",
                    sheet_name="Year 2010-2011")
df= df_.copy()
df.describe().T
df.head()
df.isnull().sum()

#Veri Ön İşleme
df.dropna(inplace=True)
df = df[~df["Invoice"].str.contains("C", na=False)]
df = df[df["Quantity"] > 0]
df = df[df["Price"] > 0]

#değişkenlerdeki aykırı değerleri eşik değerlerle değiştirmek istediğim bilgisi için fonksiyonu çağırıyorum. bir df ve değiştirmek istediğin değişken adı girilir.
replace_with_thresholds(df, "Quantity")
replace_with_thresholds(df, "Price")

#faturadaki her bir ÜRÜNE toplam ne kadar bedel ödendiğini öğren
df["TotalPrice"] = df["Quantity"] * df["Price"]

today_date = dt.datetime(2011,12,11)

#LİFETİME VERİ YAPISININ HAZIRLANMASI
#recency = son satın alma ile ilk satın alma arasında geçen zaman. haftalık. (kullanıcı özelinde dinamiktir)
#T: Müşterinin yaşı. haftalık. (analiz tarihinden ne kadar süre önce ilk satın alma yapılmıs)
#frequency: tekrar eden toplam satın alma sayısı (frequency>1)
#monetary_value: satın alma başına ortalama kazanç

cltv_df = df.groupby("Customer ID").agg({"InvoiceDate": [lambda InvoiceDate: (InvoiceDate.max() - InvoiceDate.min()).days,       #recency hesaplanır
                                                         lambda InvoiceDate: (today_date - InvoiceDate.min()).days],           #recency için müşterinin yaşını hesaplar
                                         "Invoice":lambda Invoice: Invoice.nunique(),   #frequency hesaplanır
                                         "TotalPrice": lambda TotalPrice: TotalPrice.sum()
                                        })


#değişken isimlerindeki 0.seviyeyi silmek için:
cltv_df.columns = cltv_df.columns.droplevel(0)
#yeniden isimlendirme yap.
cltv_df.columns = ["recency", "T", "frequency", "monetary"]
#işlem başına ortalama kazanç değrini bulmak için
cltv_df["monetary"] = cltv_df["monetary"] / cltv_df["frequency"]
cltv_df.describe().T

cltv_df = cltv_df[(cltv_df ["frequency"] > 1)]

#haftalık cinse çevir
cltv_df["recency"] = cltv_df["recency"] / 7
cltv_df["T"] = cltv_df["T"] / 7
cltv_df.describe().T

##########BG-NBD MODELİNİN KURULMASI !!!!!!!!!
#betageofitter fonskiyonu: oluşturduğu model nesnesi aracılığıyla receny, t, frequency değerleri verince ilgili modeli kurar.
#beta ve gama dağılımlarının parametrelerini bulur.
#tahmin yapabilmemiz için ilgili modeli oluşturmaktadır.

#penalizer_coef = 0.001  : her değişkene uygulanacak katsayı
bgf = BetaGeoFitter(penalizer_coef = 0.001)
bgf.fit(cltv_df["frequency"],
        cltv_df["recency"],
        cltv_df["T"])

#1hafta içinde en çok satın alma beklediğimiz 10 müşteri kimdir?
#1 haftalık tahmin yapmasını istediğimiz için 1 yazıyoruz
bgf.conditional_expected_number_of_purchases_up_to_time(1,
                                                        cltv_df["frequency"],
                                                        cltv_df["recency"],
                                                        cltv_df["T"]).sort_values(ascending=False).head(10)
#yukarıdaki fonksiyonun adı çok uzun onun yerine predict fonksiyonu kullanabilirsin,
# ancak bu fonksiyon bg-nbd modeli için geçerli iken gamma-gamma için geçerli değildir.
bgf.predict(1,
            cltv_df["frequency"],
            cltv_df["recency"],
            cltv_df["T"]).sort_values(ascending=False).head(10)

#tüm müşteriler için 1 haftalık beklediğimiz satın almaları yazdırıp bunu cltv df ekle.
cltv_df["expected_purc_1_week"] = bgf.predict(1,
                                              cltv_df["frequency"],
                                              cltv_df["recency"],
                                              cltv_df["T"])

#1ay (4hafta) içinde en çok satın alma beklediğimiz 10 müşteri kimdir.
bgf.predict(4,
            cltv_df["frequency"],
            cltv_df["recency"],
            cltv_df["T"]).sort_values(ascending=False).head(10)


cltv_df["expected_purc_1_month"] = bgf.predict(4,
                                              cltv_df["frequency"],
                                              cltv_df["recency"],
                                              cltv_df["T"])

#1Aylık sürenin sonunda şirketin beklediği toplam satış sayısı için sum() al
bgf.predict(4,
            cltv_df["frequency"],
            cltv_df["recency"],
            cltv_df["T"]).sum()

#3 ayda (12 hafta) tüm şirketin beklenen satış sayısı nedir?
bgf.predict(4 * 3 ,
            cltv_df["frequency"],
            cltv_df["recency"],
            cltv_df["T"]).sum()

#yürütülen tahmin sonuçlarının değerlendirilmesi
#basit bir grafik üzerinden gözlemleyebilirsin
plot_period_transactions(bgf)
plt.show()

#GAMMA-GAMMA MODELİNİN KURULMASI
#model nesnesini çağırarak model kurmasını istiyorum
from lifetimes import BetaGeoFitter

ggf = GammaGammaFitter(penalizer_coef=0.01)
ggf.fit(cltv_df["frequency"], cltv_df["monetary"])

#average profiti modellemeye çalışıyoruz gamma gamma ile
ggf.conditional_expected_average_profit(cltv_df["frequency"],             #toplam işlem sayısını gönderdik
                                        cltv_df["monetary"]).head(10)     # işlem başına ortalama değerleri gönderdik
#azalan bir şekilde gözlemlemek istersen sort_values kullan
ggf.conditional_expected_average_profit(cltv_df["frequency"],
                                        cltv_df["monetary"]).sort_values(ascending=False).head(10)

cltv_df["expected_average_profit"] = ggf.conditional_expected_average_profit(cltv_df["frequency"],
                                                                             cltv_df["monetary"])

cltv_df.sort_values("expected_average_profit",ascending=False).head(10)


#BG-NBD ve GAMA GAMA Modeli ile CLTV hesaplanması
#customer_lifetime_value methoduna bg-nbg ve gammagamma modeli verilir. bunula birlikte r, f,m,t değerlerinide göster.
#bir zaman periyodu (time girlir, kaç aylık cltv hesaplanmasını istiyorsan)
#zaman içeriisnde ürünlere indirim yapmak istersem onun oranını da gir (discount_rate).

cltv = ggf.customer_lifetime_value(bgf,
                                   cltv_df["frequency"],
                                   cltv_df["recency"],
                                   cltv_df["T"],
                                   cltv_df["monetary"],
                                   time=3, #time aylık değerdir. burada 3aylık
                                   freq="W",  #T nin frekans bilgisi
                                   discount_rate = 0.01
                                   )
cltv.head()
#indexlerde customerID'ler var.  bunu değişkene çevirmek istiyorum bu nednele;
cltv = cltv.reset_index()

#cltv_df ile cltv birlşetir (merge) ve hangi değişkene göre("customerID") birleştirecekse bunlarıda gir..
cltv_final = cltv_df.merge(cltv, on="Customer ID", how= "left")
cltv_final.sort_values(by="clv", ascending=False).head(10)

#3aylık satın alma değerinide ekle.

cltv_df["expected_purc_3_month"] = bgf.predict(4 * 3 ,
                                      cltv_df["frequency"],
                                      cltv_df["recency"],
                                      cltv_df["T"])
cltv_final = cltv_df.merge(cltv, on="Customer ID", how= "left")
cltv_final.sort_values(by="clv", ascending=False).head(10)

#düzenli olarak satın alım yapan müşterinin recency değeri artıkça müşterinin satın alma olasılığı artıyordur.

#CLTV' ye göre Segmentlerin Oluşturulması
cltv_final["segment"] = pd.qcut(cltv_final["clv"], 4, lables= ["D", "C", "B", "A"])

cltv_final.sort_values(by="clv", ascending=False).head(50)

cltv_final.groupby("segment").agg({"count",
                                   "mean",
                                  "sum"})


########################################################################################################################
#  Çalışmanın Fonksiyonlaştırılması

def create_cltv_p(dataframe, month=3):
    #veriyi ön işleme
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C",na=False)]
    dataframe=  dataframe[(dataframe["Quantity"] > 0)]
    dataframe=  dataframe[(dataframe["Price"] > 0)]
    replace_with_thresholds(dataframe, "Quantity")
    replace_with_thresholds(dataframe, "Price")
    dataframe["TotalPrice"] = dataframe["Quantity"] * dataframe["Price"]
    today_date = dt.datetime(2011,12,11)


    cltv_df = dataframe.groupby("Customer ID").agg(
        { "InvoiceDate" : [lambda InvoiceDate: (InvoiceDate.max() - InvoiceDate.min()).days,
                           lambda InvoiceDate: (today_date - InvoiceDate.min()).days],

        "Invoice" : lambda Invoice: Invoice.nunique(),
        "TotalPrice": lambda TotalPrice: TotalPrice.sum()
        })

    cltv_df.columns = cltv_df.columns.droplevel( 0 )
    cltv_df.columns = ["recency", "T", "frequency", "monetary"]
    cltv_df["monetary"] = cltv_df["monetary"] / cltv_df["frequency"]
    cltv_df = cltv_df[(cltv_df["frequency"] > 1)]
    cltv_df["recency"] = cltv_df["recency"] / 7
    cltv_df["T"] = cltv_df["T"] / 7

    bgf = BetaGeoFitter( penalizer_coef=0.001 )
    bgf.fit( cltv_df["frequency"],
             cltv_df["recency"],
             cltv_df["T"] )

    cltv_df["expected_purc_1_week"] = bgf.predict( 1,
                                                   cltv_df["frequency"],
                                                   cltv_df["recency"],
                                                   cltv_df["T"] )

    cltv_df["expected_purc_1_month"] = bgf.predict( 4,
                                                    cltv_df["frequency"],
                                                    cltv_df["recency"],
                                                    cltv_df["T"] )
    cltv_df["expected_purc_3_month"] = bgf.predict( 12,
                                                    cltv_df["frequency"],
                                                    cltv_df["recency"],
                                                    cltv_df["T"] )

    ggf = GammaGammaFitter( penalizer_coef=0.01 )
    ggf.fit( cltv_df[frequency], cltv_df["monetary"] )

    cltv_df["expected_average_profit"] = ggf.conditional_expected_average_profit( cltv_df["frequency"],
                                                                                  cltv_df["monetary"] )

    cltv = ggf.customer_lifetime_value( bgf,
                                        cltv_df["frequency"],
                                        cltv_df["recency"],
                                        cltv_df["T"],
                                        cltv_df["monetary"],
                                        time=3,
                                        freq="W",
                                        discount_rate=0.01
                                        )
    cltv = cltv.reset_index()
    cltv_final = cltv_df.merge(cltv, on="Customer ID", how= "left")
    cltv_final["segment"] = pd.qcut(cltv_final["clv"], 4, lables= ["D", "C", "B","A"])

    return cltv_final

df = df_.copy()
cltv_final2 = create_cltv_p(df)

#elde ettiğin sonuçları bir csv dosyasında tutmak istersen
cltv_final2.to_csv("cltv_prediction.csv")
















