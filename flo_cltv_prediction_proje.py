#GÖREV1
import datatime as dt
import pandas as pd
import matplotlib.pyplot as plt
from lifetimes import BetaGeoFitter
from lifetimes import GammaGammaFitter
from lifetimes.plotting import plot_period_transactions

pd.set_option( "display.max_columns", None )
pd.set_option( "display.float_format", lambda x: "%.3f" % x )
pd.set_option( "display.width", 1000 )

#ADIM1
df_ = pd.read_csv( "C:/Users/esman/PycharmProjects/datasets/flo_data_20k.csv" )
df = df_.copy()
#ADIM2
df.dropna(inplace=True)


def outlier_thresholds(dataframe, variable):
    quartile1 = dataframe[variable].quantile(0.01)
    quartile3 = dataframe[variable].quantile(0.99)
    interquantile_range = quartile3 - quartile1
    up_limit = quartile3 + 1.5 * interquantile_range
    low_limit = quartile1 - 1.5 * interquantile_range
    return low_limit, up_limit

def replace_with_thresholds(dataframe, variable):
    low_limit, up_limit = outlier_thresholds(dataframe, variable)
    dataframe.loc[(dataframe[variable] < low_limit), variable] = round(low_limit,0)
    dataframe.loc[(dataframe[variable] > up_limit), variable] = round(up_limit,0)

#ADIM3
columns = ["order_num_total_ever_online", "order_num_total_ever_online", "customer_vale_total_ever_offline", "customer_value_total_ever_online"]
for col in columns:
    replace_with_thresholds(df,col)

#ADIM4
df["order_num_total"] = df["order_num_total_ever_online"] + df["order_num_total_ever_offline"]
df["customer_value_total"] = df["customer_value_total_ever_online"] + df["customer_value_total_ever_offline"]

#adım5
date_columns = df.columns[df.columns.str..contains("date")]
df[date_columns] = df[date_columns].apply(pd.to_datatime)
df.info()

########################GÖREV2
#adım1
df["last_order_late"].max()
analysis_date = dt.datetime(2021,6, 1)
#adım2
cltv_df = pd.DataFrame()
cltv_df["customer_id"] = df["master_id"]
cltv_df["recency_cltv_weekly"] = ((df["last_order_date"] - df["first_order_date"]).astype("timedelta64[D]")) / 7
cltv_df["T_weekly"] = ((analysis_date - df["first_order_date"]).astype("timedelta64[D")) / 7
cltv_df["frequency"] = df["order_num_total"]
cltv_df["monetary_cltv_avg"] = df["customer_value_total"] / df["order_num_total"]

cltv_df.head()

#GÖREV3
#adım1
bgf = BetaGeoFitter(penalizer_coef=0.001)
bgf.fit(cltv_df["frequency"],
        cltv_df["recency_cltv_weekly"],
        cltv_df["T_weekly"])


cltv_df["exp_sales_3_month"] = bgf.predict(4*3,
                                           cltv_df["frequency"],
                                           cltv_df["recency_cltv_weekly"],
                                           cltv_df["T_weekly"])

cltv_df["exp_sales_6_month"] = bgf.predict (4*6,
                                            cltv_df["frequency"],
                                            cltv["recency_cltv_weekly"],
                                            cltv_df["T_weekly"])
cltv_df[["exp_sales_3_month", "exp_sales_6_month"]]

cltv_df.sort_values("exp_Sales_3_month", ascending=False) [:10]
cltv_df.sort_values("exp_Sales_6_month", ascending=False) [:10]

#adım2
ggf = GammaGammaFitter(penalizer_coef=0.01)
ggf.fit(cltv_df[frequency], cltv_df["monetary_cltv_avg"])
cltv_df["exp_average_value"] = ggf.conditional_expected_average_profit(cltv_df["frequency"],
                                                                       cltv_df["monetary_cltv_avg"])
cltv_df.head()

#adım3
cltv=ggf.customer_lifetime_value(bgf,
                                  cltv_df["frequency"],
                                  cltv_df["recency_cltv_weekly"],
                                  cltv_df["T_weekly"],
                                  cltv_df["monetary_cltv_avg"],
                                  time=6,
                                  freq="W",
                                 discount_rate =0.01)
cltv_df["cltv"] = cltv

cltv_df.sort_values("cltv", ascending=False) [:20]

#GÖREV 4
#adım1
cltv_df["cltv_segment"] = pd.qcut(cltv_df["cltv"], 4, labels=["D", "C", "B", "A"])
cltv_df.head()

