import os

# path = "/Users/pkar/Documents/Documents - Parag’s MacBook Pro/parag_qc_files/2022/2022_11_26_New_Data_Processing/Python_Finance/out"
# os.chdir(path)

stock_tickers = {"Nokia": "NOK","Apple":"AAPL","Qualcomm": "QCOM","Google": "GOOG","Facebook":"META",
                 "Netflix": "NFLX","Reliance": "RELIANCE.NS","Nvidia":"NVDA","Amazon": "AMZN",
                 "Airtel":"BHARTIARTL.BO","MediaTek":"2454.TW","Cisco":"CSCO", "Tesla":"TSLA",
                "Microsoft":"MSFT","TSMC":"TSM","Tencent":"0700.HK", "Samsung":"005930.KS", "Broadcom":"AVGO",
                "ASML Holding":"ASML", "Oracle":"ORCL", "Alibaba":"BABA", "Salesforce":"CRM", "Texas Inst":"TXN",
                "Adobe":"ADBE","SAP":"SAP","AMD":"AMD"}

myKeys = list(stock_tickers.keys())
myKeys.sort()
stock_tickers = {i: stock_tickers[i] for i in myKeys}

#procesing dataframe based on chosen value of date

from datetime import date
from dash import Dash, html, dcc
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.offline import init_notebook_mode, iplot
import dash_bootstrap_components as dbc 
import os
import glob
import dash 
import dash_core_components as dcc
from dash import html
import datetime
import yfinance as yf
import datetime as dt

def download_stocks(tickers):
    df_comb=pd.DataFrame()
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="10y")
            df["ticker"]=ticker
            df_comb=pd.concat([df,df_comb], axis=0)

        except:
            pass
    return df_comb


def processed_data(date_value, tickers, df_comb):
    #processing all stock files
    # df_comb=pd.read_csv("combined.csv", index_col="Date", parse_dates=True)
    
    df_comb.index=[dt.datetime.strftime(x, "%d-%m-%Y") for x in list(df_comb.index)]
    df_comb.index = pd.to_datetime(df_comb.index, dayfirst = True)
    

    returns ={}
    cov = {}
    # volume = {}
    df_stocks=pd.DataFrame()
    for ticker in tickers:
        filt = (df_comb["ticker"]==ticker)
        temp_df= df_comb[filt]
        closest_date_index = temp_df.index.get_loc(date_value, method="nearest")
        ref_value_close = temp_df.iloc[closest_date_index,:][3]
        temp_df = temp_df.iloc[closest_date_index:,:]
        value_df = temp_df["Close"]/ref_value_close
        returns.update({ticker: (value_df-1)*100})
        sd = temp_df[temp_df["ticker"]==ticker]["Close"].std()
        mean = temp_df[temp_df["ticker"]==ticker]["Close"].mean()
        df_stocks =pd.concat([temp_df,df_stocks], axis=0)
        cov.update({ticker: round(sd/mean,2)})

    df_ret = pd.DataFrame(returns)
    df_ret = df_ret.reset_index()
    df_ret = df_ret.melt(id_vars=['index'], value_vars=tickers, ignore_index=False)
    df_ret.columns =["Date","Ticker","%Returns"]
    df_ret = df_ret.dropna()
    df_ret = df_ret.set_index("Date")
    df_cov = pd.DataFrame.from_dict(cov, orient='index')
    df_cov = df_cov.reset_index()
    df_cov.columns = ["Ticker","COV"]

    return df_ret, df_cov, df_comb, df_stocks

#main application

# Customizing the Layout

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H3("Performance of Selected Stocks from the Chosen Date of Reference", style={"textAlign":"left"}),
    html.Hr(),
    html.P("Choose Stocks of Interest:"),
    html.Div(html.Div([
        dcc.Dropdown(id='stock-type', clearable=False,
                     value=["AAPL"],multi=True,
                     options=[{'label': key, 'value': value} for key, value in
                              stock_tickers.items()]),
    ],className="two columns"),className="row"),
    html.P("Choose a Starting Date: "),
    html.Div(html.Div([
        dcc.DatePickerSingle(
        id='date-picker-single',
        min_date_allowed=date(2000,1, 1),
        max_date_allowed=date(2023,3, 10),
        initial_visible_month= date(2022,1,31),
        date=date(2022,1, 31))
    ],className="two columns"),className="row"),

    html.Div(id="output-div", children=[]),
])


# Allowing Callback to interact with components

@app.callback(
    Output(component_id="output-div", component_property="children"),
    Input(component_id="date-picker-single",component_property="date"),
    Input(component_id="stock-type",component_property="value"))

def make_graphs(date_value, tickers):
    #Processing Dataframes for plotting
    
    df_comb = download_stocks(tickers)
    
    
    df_ret, df_cov, df_comb, df_stocks = processed_data(date_value,tickers, df_comb)
    
    # df_close=temp_df[:,["Close","Ticker"]]
    
    df_close = df_stocks.loc[:,["Close","ticker"]]
    
                           
    
    #Line Charts Returns 
 
    fig1_line = px.line(df_ret, x=df_ret.index, y="%Returns", color="Ticker", height=500, template='plotly_white')
    
    fig1_line.update_xaxes(fixedrange=True)
    fig1_line.update_yaxes(fixedrange=True)
    
    fig1_line.update_layout(uniformtext_minsize=14, uniformtext_mode='hide',
                       legend={'x':0,'y':1.1,"orientation":"h"}),
    
    fig2_line = px.line(df_close, x=df_close.index, y="Close", color="ticker", height=500, log_y=True, template='plotly_white',
                        labels={"Close":"Closing Price","index":"Date"})
    
    fig2_line.update_xaxes(fixedrange=True)
    fig2_line.update_yaxes(fixedrange=True)
    
    fig2_line.update_layout(uniformtext_minsize=14, uniformtext_mode='hide',
                   legend={'x':0,'y':1.1,"orientation":"h"}),
    

    #Bar Chart
    
    fig_bar = px.bar(df_cov, x="Ticker", y="COV", color="Ticker", text_auto=True, height=300, template='plotly_white')
    
    fig_bar.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)
    
    fig_bar.update_xaxes(fixedrange=True)
    fig_bar.update_yaxes(fixedrange=True)
    
    fig_bar.update_layout(uniformtext_minsize=14, uniformtext_mode='hide',
               legend={'x':0,'y':1.2,"orientation":"h"}),

    # string_prefix = 'You have selected: '
    # if date_value is not None:
    #     date_object = date.fromisoformat(date_value)
    #     date_string = date_object.strftime('%B %d, %Y')
    #     date_string = "Selected Reference Date is -> "+date_string
    return [
        html.H4("Selected Stock's %Return on Investments from the Chosen Date of Reference", style={"textAlign":"left"}),
        html.Hr(),
        html.Div([
            html.Div([dcc.Graph(figure=fig1_line)], className="twelve columns"),
            # html.Div([dcc.Graph(figure=fig_bar)], className="six columns"),
        ], className="row"),
        html.H4("Selected Stock's Closing Price trends from the Chosen Date of Reference", style={"textAlign":"left"}),
        html.Hr(),
        html.Div([
            html.Div([dcc.Graph(figure=fig2_line)], className="twelve columns"),
            # html.Div([dcc.Graph(figure=fig_bar)], className="six columns"),
        ], className="row"),
        html.H4("Selected Stock's Coefficient of Variation (Standard Deviation / Mean)", style={"textAlign":"left"}),
        html.Hr(),
        html.Div([
            html.Div([dcc.Graph(figure=fig_bar)], className="twelve columns"),
            # html.Div([dcc.Graph(figure=fig_ecdf)], className="six columns"),
        ], className="row"),
        # html.Div([
        #     html.Div([dcc.Graph(figure=fig_line)], className="twelve columns"),
        # ], className="row"),
    ]
        
# Runing the application
if __name__ == '__main__':
    app.run_server(debug=True,use_reloader=False)
