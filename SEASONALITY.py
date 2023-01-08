import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime
from xbbg import blp
from datetime import timedelta
from configparser import ConfigParser
from dateutil.relativedelta import relativedelta
import math
import os

#Read config.ini file
config_object = ConfigParser()

# #Assume we need 2 sections in the config file
# config_object["Securities - Dates"] = {
#     "Securities": "USGG10YR Index, USGG5YR Index, USGG2YR Index",
#     "Dates": "2021-05-27, 2019-02-24, 2017-12-24",
#     "Plus-Minus Days": 50,
#     "Frequencies": "W, M, Q"
# }

# config_object["Dates - Securities"] = {
#     "Securities": "USGG10YR Index, USGG5YR Index, USGG2YR Index",
#     "Dates": "2021-05-27, 2019-02-24, 2017-12-24",
#     "Plus-Minus Days": 50,
#     "Frequencies": "W, M, Q"
# }

# config_object["Box-Plot by Securties"] = {
#     "Securities": "USGG10YR Index, USGG5YR Index, USGG2YR Index",
#     "Dates": "2021-05-27, 2019-02-24, 2017-12-24",
#     "Plus-Minus Days": 50,
#     "Frequencies": "W, M, Q"
# }

# #Write the above sections to config.ini file
# with open('Z:\Seasonality/config.ini', 'w') as conf:
#     config_object.write(conf)
        
config_object.read("Z:\Seasonality/config.ini")
now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
today = datetime.datetime.now().strftime("%Y-%m-%d")

sec_date = config_object["Dates Analysis"]
if sec_date["Status"] == "On":
    for sec in sec_date["Securities"].split(", "):
        for i in range(len(sec_date["Frequencies"].split(", "))):
            
            indiv_sec = []
            for date in sec_date["Dates"].split(", "):
                dated = datetime.datetime.strptime(date, "%Y-%m-%d")
                
                #get data by Freq
                if sec_date["Frequencies"].split(", ")[i] == "D":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - timedelta(days=int(sec_date["Periods"].split(", ")[i]))), 
                                  end_date=(dated + timedelta(days=int(sec_date["Periods"].split(", ")[i]))))
                if sec_date["Frequencies"].split(", ")[i] == "W":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - timedelta(weeks=int(sec_date["Periods"].split(", ")[i]))), 
                                  end_date=(dated + timedelta(weeks=int(sec_date["Periods"].split(", ")[i]))))
                if sec_date["Frequencies"].split(", ")[i] == "M":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - relativedelta(months=int(sec_date["Periods"].split(", ")[i]))), 
                                  end_date=(dated + relativedelta(months=int(sec_date["Periods"].split(", ")[i]))))
                if sec_date["Frequencies"].split(", ")[i] == "Q":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - relativedelta(months=int(sec_date["Periods"].split(", ")[i])*3)), 
                                  end_date=(dated + relativedelta(months=int(sec_date["Periods"].split(", ")[i])*3)))
    
                df = df.droplevel(0, axis=1)
                df.index = pd.to_datetime(df.index)
                df["Security"] = sec
                df["Date_0"] = str(date)
                
                #if given date is hol/weekends, then take prev workday
                if date not in df.index:
                    date = list(df.index[df.index < date])[-1].strftime("%Y-%m-%d")
    
                df.reset_index(inplace = True)
                df.rename(columns = {'index':'Dates'}, inplace = True)
                df["Days"] = (df["Dates"] - pd.to_datetime(date)).dt.days
    
                df["pct_chg"] = df["last_price"]/df["last_price"][df["Dates"] == date].values[0] - 1
                df["diff"] = 100* (df["last_price"] - df["last_price"][df["Dates"] == date].values[0])
    
                     
                if sec_date["Frequencies"].split(", ")[i] == "Q":
                    df["Period"] = (df["Dates"] - pd.to_datetime(date))/np.timedelta64(3,"M")
                    
                else:
                    df["Period"] = (df["Dates"] - pd.to_datetime(date))/np.timedelta64(1,sec_date["Frequencies"].split(", ")[i])
                    
                df["Period"] = df["Period"].round(0).astype(int)
                
                df.drop(index = df[df["Period"] == 0][df["diff"] != 0].index, inplace = True)
                df.drop_duplicates(subset=['Period'], inplace = True)
    
                indiv_sec.append(df)
    
            secur_data = pd.concat(indiv_sec, axis = 0)
            
            # fig_line_pc = px.line(secur_data, x="Period", y="pct_chg", color = "Date_0",
            #                       labels=dict(pct_chg="BPS CHANGE (%)", Date_0="Base Date"))
            # fig_line_pc.add_hline(y=0, line_width=1, line_dash="dash")
            # fig_line_pc.add_vline(x=0, line_width=1, line_dash="dash")
            # fig_line_pc.update_layout(title_text=str(sec) + '_Pct Change_' + str(sec_date["Period"].split(", ")[i]) + str(sec_date["Frequencies"].split(", ")[i]), title_x=0.5)
    
            fig_line_diff = px.line(secur_data, x="Period", y="diff", color = "Date_0",
                                    labels=dict(diff="BPS DIFF", Date_0="Base Date"))
            fig_line_diff.add_hline(y=0, line_width=1, line_dash="dash")
            fig_line_diff.add_vline(x=0, line_width=1, line_dash="dash")
            fig_line_diff.update_layout(title_text= str(sec) + '_Diff_' + str(sec_date["Period"].split(", ")[i]) + str(sec_date["Frequencies"].split(", ")[i]), title_x=0.5)
            
            if os.path.exists(r"Z:\Seasonality/" + str(today)):
                
                #with open(r"Z:\Seasonality/"+ str(today)+"/Date_Analysis_" + str(now) + ".html", 'a') as f:
                with open(r"Z:\Seasonality/"+ str(today)+"/" + str(sec_date["Output_name"]) + ".html", 'a') as f:
                    # f.write(fig_line_pc.to_html(full_html=False, include_plotlyjs='cdn'))
                    f.write(fig_line_diff.to_html(full_html=False, include_plotlyjs='cdn'))
                    
            else:
                os.mkdir(r"Z:\Seasonality/" + str(today))
                with open(r"Z:\Seasonality/"+ str(today)+"/" + str(sec_date["Output_name"]) + ".html", 'a') as f:
                    # f.write(fig_line_pc.to_html(full_html=False, include_plotlyjs='cdn'))
                    f.write(fig_line_diff.to_html(full_html=False, include_plotlyjs='cdn'))
    
date_sec = config_object["Securities Analysis"]
if date_sec["Status"] == "On":
    for date in date_sec["Dates"].split(", "):
        for i in range(len(date_sec["Frequencies"].split(", "))):
        
            indiv_date = []
            for sec in date_sec["Securities"].split(", "):
                dated = datetime.datetime.strptime(date, "%Y-%m-%d")
                if date_sec["Frequencies"].split(", ")[i] == "D":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - timedelta(days=int(date_sec["Periods"].split(", ")[i]))), 
                                  end_date=(dated + timedelta(days=int(date_sec["Periods"].split(", ")[i]))))
                if date_sec["Frequencies"].split(", ")[i] == "W":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - timedelta(weeks=int(date_sec["Periods"].split(", ")[i]))), 
                                  end_date=(dated + timedelta(weeks=int(date_sec["Periods"].split(", ")[i]))))
                if date_sec["Frequencies"].split(", ")[i] == "M":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - relativedelta(months=int(date_sec["Periods"].split(", ")[i]))), 
                                  end_date=(dated + relativedelta(months=int(date_sec["Periods"].split(", ")[i]))))
                if date_sec["Frequencies"].split(", ")[i] == "Q":
                    df = blp.bdh(tickers=sec, flds=['last_price'], start_date=(dated - relativedelta(months=int(date_sec["Periods"].split(", ")[i])*3)), 
                                  end_date=(dated + relativedelta(months=int(date_sec["Periods"].split(", ")[i])*3)))
    
                df = df.droplevel(0, axis=1)
                df.index = pd.to_datetime(df.index)
                df["Security"] = sec
                df["Date_0"] = str(date)
      
                if date not in df.index:
                    date = list(df.index[df.index < date])[-1].strftime("%Y-%m-%d")
      
                df.reset_index(inplace = True)
                df.rename(columns = {'index':'Dates'}, inplace = True)
                df["Days"] = (df["Dates"] - pd.to_datetime(date)).dt.days
                
                df["pct_chg"] = df["last_price"]/df["last_price"][df["Dates"] == date].values[0] - 1
                df["diff"] = 100* (df["last_price"] - df["last_price"][df["Dates"] == date].values[0])
              
                if date_sec["Frequencies"].split(", ")[i] == "Q":
                    df["Period"] = (df["Dates"] - pd.to_datetime(date))/np.timedelta64(3,"M")
                else:
                    df["Period"] = (df["Dates"] - pd.to_datetime(date))/np.timedelta64(1,date_sec["Frequencies"].split(", ")[i])
    
                df["Period"] = df["Period"].round(0).astype(int)
                df.drop(index = df[df["Period"] == 0][df["diff"] != 0].index, inplace = True)
                df.drop_duplicates(subset=['Period'], inplace = True)
    
                indiv_date.append(df)
                    
            date_data = pd.concat(indiv_date, axis = 0)
            
            # fig_line_pc = px.line(date_data, x="index", y="pct_chg", color = "Security",
            #                       labels=dict(pct_chg="BPS CHANGE (%)"))
            # fig_line_pc.add_hline(y=0, line_width=1, line_dash="dash")
            # fig_line_pc.add_vline(x=date, line_width=1, line_dash="dash")
            # fig_line_pc.update_layout(title_text=str(date) + '_Pct Change' + str(date_sec["Period"].split(", ")[i]) + str(date_sec["Frequencies"].split(", ")[i]), title_x=0.5)
            
            fig_line_diff = px.line(date_data, x="Dates", y="diff", color = "Security",
                                    labels=dict(diff="BPS DIFF"))
            fig_line_diff.add_hline(y=0, line_width=1, line_dash="dash")
            fig_line_diff.add_vline(x=date, line_width=1, line_dash="dash")
            fig_line_diff.update_layout(title_text=str(date) + '_Diff_' + str(date_sec["Period"].split(", ")[i]) + str(date_sec["Frequencies"].split(", ")[i]), title_x=0.5)
            
            if os.path.exists(r"Z:\Seasonality/" + str(today)):
                
                with open(r"Z:\Seasonality/"+ str(today)+"/" + str(date_sec["Output_name"]) + ".html", 'a') as f:
                    # f.write(fig_line_pc.to_html(full_html=False, include_plotlyjs='cdn'))
                    f.write(fig_line_diff.to_html(full_html=False, include_plotlyjs='cdn'))
                    
            else:
                os.mkdir(r"Z:\Seasonality/" + str(today))
                with open(r"Z:\Seasonality/"+ str(today)+"/" + str(date_sec["Output_name"]) + ".html", 'a') as f:
                    # f.write(fig_line_pc.to_html(full_html=False, include_plotlyjs='cdn'))
                    f.write(fig_line_diff.to_html(full_html=False, include_plotlyjs='cdn'))
   
sec_change = config_object["Box-Plot by Securties"]
if sec_change["Status"] == "On":
    for sec in sec_change["Securities"].split(", "):
        for i in range(len(sec_change["Frequencies"].split(", "))):
    
            sec_box = blp.bdh(tickers=sec, flds=['last_price'], start_date=sec_change["date_range"].split(" to ")[0], 
                          end_date=sec_change["date_range"].split(" to ")[1])

            sec_box = sec_box.droplevel(0, axis=1).reset_index()
            sec_box['index'] = pd.to_datetime(sec_box['index'])

            sec_box["pct_chg"] = sec_box["last_price"].pct_change(1)
            sec_box["diff"] = sec_box["last_price"].diff(periods = 1)*100
            # sec_box = sec_box[1:]

            if sec_change["Frequencies"].split(", ")[i] == "W":
                sec_box["W"] = sec_box['index'].dt.week
            elif sec_change["Frequencies"].split(", ")[i] == "M":
                sec_box["M"] = sec_box['index'].dt.month
            elif sec_change["Frequencies"].split(", ")[i] == "Q":
                sec_box["Q"] = sec_box['index'].dt.quarter

            sec_box.sort_values(by = str(sec_change["Frequencies"].split(", ")[i]), inplace = True)

            # fig_line_pc = px.box(sec_box_data, x=str(sec_change["Frequencies"].split(", ")[i]), y="pct_chg", points="all",
            #                       labels=dict(index="Periods", pct_chg="BPS CHANGE (%)"))
            # fig_line_pc.add_hline(y=0, line_width=1, line_dash="dash")
            # fig_line_pc.update_layout(title_text=str(sec) + '_Pct Change_' + str(sec_change["Frequencies"].split(", ")[i]), title_x=0.5)
            
            fig_line_diff = px.box(sec_box, x=str(sec_change["Frequencies"].split(", ")[i]), y="diff", points="all",
                                    labels=dict(index="Periods", diff="BPS DIFF"))
            fig_line_diff.add_hline(y=0, line_width=1, line_dash="dash")
            fig_line_diff.update_layout(title_text=str(sec) + '_Diff_' + str(sec_change["Frequencies"].split(", ")[i]), title_x=0.5)
            
            if os.path.exists(r"Z:\Seasonality/" + str(today)):
                
                with open(r"Z:\Seasonality/"+ str(today)+"/" + str(sec_change["Output_name"]) + ".html", 'a') as f:
                    # f.write(fig_line_pc.to_html(full_html=False, include_plotlyjs='cdn'))
                    f.write(fig_line_diff.to_html(full_html=False, include_plotlyjs='cdn'))
                    
            else:
                os.mkdir(r"Z:\Seasonality/" + str(today))
                with open(r"Z:\Seasonality/"+ str(today)+"/" + str(sec_change["Output_name"]) + ".html", 'a') as f:
                    # f.write(fig_line_pc.to_html(full_html=False, include_plotlyjs='cdn'))
                    f.write(fig_line_diff.to_html(full_html=False, include_plotlyjs='cdn'))
