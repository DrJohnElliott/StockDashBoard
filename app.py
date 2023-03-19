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
from plotly.subplots import make_subplots


fig_height =400
fig_width = 500




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

def process_for_df_ret(date_value, tickers, df_comb):
    #processing all stock files
    # df_comb=pd.read_csv("combined.csv", index_col="Date", parse_dates=True)
    
    df_comb.index=[dt.datetime.strftime(x, "%d-%m-%Y") for x in list(df_comb.index)]
    df_comb.index = pd.to_datetime(df_comb.index, dayfirst = True)
    
    returns ={}

    for ticker in tickers:
        filt = (df_comb["ticker"]==ticker)
        temp_df= df_comb[filt]
        closest_date_index = temp_df.index.get_loc(date_value, method="nearest")
        ref_value_close = temp_df.iloc[closest_date_index,:][3]
        temp_df = temp_df.iloc[closest_date_index:,:]
        value_df = temp_df["Close"]/ref_value_close
        returns.update({ticker: (value_df-1)*100})

    df_ret = pd.DataFrame(returns)
    df_ret = df_ret.reset_index()
    df_ret = df_ret.melt(id_vars=['index'], value_vars=tickers, ignore_index=False)
    df_ret.columns =["Date","Ticker","%Returns"]
    df_ret = df_ret.dropna()
    df_ret = df_ret.set_index("Date")

    return df_ret

def process_for_df_stocks(date_value, tickers, df_comb):
    
    df_comb.index=[dt.datetime.strftime(x, "%d-%m-%Y") for x in list(df_comb.index)]
    df_comb.index = pd.to_datetime(df_comb.index, dayfirst = True)

    df_stocks=pd.DataFrame()
    for ticker in tickers:
        filt = (df_comb["ticker"]==ticker)
        temp_df= df_comb[filt]
        closest_date_index = temp_df.index.get_loc(date_value, method="nearest")
        temp_df = temp_df.iloc[closest_date_index:,:]
        df_stocks =pd.concat([temp_df,df_stocks], axis=0)
        
    return df_stocks


def process_for_df_cov(date_value, tickers, df_comb):
    
    df_comb.index=[dt.datetime.strftime(x, "%d-%m-%Y") for x in list(df_comb.index)]
    df_comb.index = pd.to_datetime(df_comb.index, dayfirst = True)
    
    cov = {}
    for ticker in tickers:
        filt = (df_comb["ticker"]==ticker)
        temp_df= df_comb[filt]
        closest_date_index = temp_df.index.get_loc(date_value, method="nearest")
        ref_value_close = temp_df.iloc[closest_date_index,:][3]
        temp_df = temp_df.iloc[closest_date_index:,:]
        value_df = temp_df["Close"]/ref_value_close
        sd = temp_df[temp_df["ticker"]==ticker]["Close"].std()
        mean = temp_df[temp_df["ticker"]==ticker]["Close"].mean()
        cov.update({ticker: round(sd/mean,2)})

    df_cov = pd.DataFrame.from_dict(cov, orient='index')
    df_cov = df_cov.reset_index()
    df_cov.columns = ["Ticker","COV"]

    return df_cov

#main application

# Customizing the Layout

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0'}]
               )

server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H4("Performance of Stocks from the Date of Ref.", className ="mb-2"),#width=12
                xs=12, sm=12, md=12, lg=5, xl=5
           )
            ],justify="center"
            ),
    
    dbc.Row([
        dbc.Col([
            html.P("Choose Stocks of Interest:", style={"textDecoration":"bold"}),
            dcc.Dropdown(id='stock-type', clearable=False,
                     value=["AAPL"],multi=True,
                     options=[{'label': key, 'value': value} for key, value in
                              stock_tickers.items()]),
                ], #width={'size':6},
                   xs=12, sm=12, md=12, lg=5, xl=5,
            ),
        
        dbc.Col([
            html.P("Choose a Starting Date: ", style={"textDecoration":"bold"}),
            dcc.DatePickerSingle(id='date-picker-single',
                min_date_allowed=date(2000,1, 1),
                max_date_allowed=date(2023,3, 1),
                initial_visible_month= date(2022,1,31),
                date=date(2022,1, 31))
                ], #width ={'size':6}
                xs=12, sm=12, md=12, lg=5, xl=5
        
        )       
            ], justify="center"
            ),

    dbc.Row([
        dbc.Col([dcc.Graph(id="fig1_line", figure={}, style={"pading":10,"border":"dotted"})
                
                ],#width ={'size':12}
                xs=12, sm=12, md=12, lg=5, xl=5
               ),
    
        dbc.Col([dcc.Graph(id="fig_hist", figure={}, style={"pading":10,"border":"dotted"})
                
                ],#width ={'size':12}
                xs=12, sm=12, md=12, lg=5, xl=5
               ),
            ], justify="center"
            ),   
    
    dbc.Row([
        
        dbc.Col([dcc.Graph(id="fig2_line", figure={}, style={"pading":10,"border":"dotted"})
                
                ],#width ={'size':12}
                xs=12, sm=12, md=12, lg=5, xl=5
               ),
            
        dbc.Col([dcc.Graph(id="fig_bar", figure={}, style={"pading":10,"border":"dotted"})
                
                ],#width ={'size':12}
                xs=12, sm=12, md=12, lg=5, xl=5
               ),   
                         
            ], justify="center"
            ),
    
                        ], fluid=False)


# Callback section: connecting the components
# ************************************************************************
# Line chart 1
@app.callback(
    Output('fig1_line', 'figure'),
    Input(component_id="date-picker-single",component_property="date"),
    Input(component_id="stock-type",component_property="value"))

def update_graph(date_value, tickers):
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%B %d, %Y')


    df_comb = download_stocks(tickers)

    df_ret = process_for_df_ret(date_value,tickers, df_comb)
    
 
    fig1_line = px.line(df_ret, x=df_ret.index, y="%Returns", color="Ticker", template='plotly_white',
                       title="% Returns of Stocks from "+date_string)
    
    fig1_line.update_xaxes(fixedrange=True)
    fig1_line.update_yaxes(fixedrange=True)
    
    fig1_line.update_layout(uniformtext_minsize=14, uniformtext_mode='hide',
                       legend={'x':0,'y':1.05,"orientation":"h"})
    
    fig1_line.update_layout(height=fig_height, width=fig_width,yaxis_title=None, xaxis_title=None)
    
    fig1_line.update_layout(
    margin=dict(
        l=0,
        r=0,
        t=40,
        b=0,
            ))

    
    return fig1_line
    
# Line chart 2
@app.callback(
    Output('fig2_line', 'figure'),
    Input(component_id="date-picker-single",component_property="date"),
    Input(component_id="stock-type",component_property="value"))
    
def update_graph(date_value, tickers):
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%B %d, %Y')
    

    df_comb = download_stocks(tickers)

    df_stocks = process_for_df_stocks(date_value,tickers, df_comb)

    df_close = df_stocks.loc[:,["Close","ticker"]]

    df_close = df_close.rename(columns={'ticker': 'Ticker'})    
    
    
    fig2_line = px.line(df_close, x=df_close.index, y="Close", color="Ticker", log_y=True, template='plotly_white',
                        labels={"Close":"Closing Price","index":"Date"}, title="Closing Price of Stocks from "+date_string)
    
    fig2_line.update_xaxes(fixedrange=True)
    fig2_line.update_yaxes(fixedrange=True)
    
    fig2_line.update_layout(uniformtext_minsize=14, uniformtext_mode='hide',legend={'x':0,'y':1.1,"orientation":"h"})
    
    fig2_line.update_layout(height=fig_height, width=fig_width,yaxis_title=None, xaxis_title=None)
    
    fig2_line.update_layout(
        margin=dict(
            l=0,
            r=0,
            t=40,
            b=0,
                ))
    
    fig2_line.update_layout(showlegend=False)

    return fig2_line


# Histogram
@app.callback(
    Output('fig_hist', 'figure'),
    Input(component_id="date-picker-single",component_property="date"),
    Input(component_id="stock-type",component_property="value"))    
    
def update_graph(date_value, tickers):
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%B %d, %Y')
    

    df_comb = download_stocks(tickers)

    df_ret = process_for_df_ret(date_value,tickers, df_comb) 
    
    Tickers = list(set(df_ret["Ticker"]))

    fig_hist = make_subplots(rows=len(Tickers), cols=1, shared_xaxes=True)
    for i, Ticker in enumerate(Tickers):
        filt = df_ret["Ticker"]==Ticker     
        df_ret_filt = df_ret[filt]
        # fig_hist.append_trace(go.Histogram(x=df_ret_filt["%Returns"], texttemplate="%{x}", textfont_size=8), row=i + 1, col=1)
        fig_hist.append_trace(go.Histogram(x=df_ret_filt["%Returns"]), row=i + 1, col=1)

        fig_hist.update_layout(barmode='group')
    # fig_hist.update_yaxes(title_text='Count')
    fig_hist.update_layout(height=fig_height, width=fig_width, title_text="Distribution of % Returns from "+date_string, template='plotly_white')
    fig_hist.update_layout(showlegend=False)
    fig_hist.update_xaxes(fixedrange=True)
    fig_hist.update_yaxes(fixedrange=True)
    fig_hist.update_traces(textposition="top center", selector=dict(type='scatter'))
    
    fig_hist.update_layout(
        margin=dict(
            l=0,
            r=0,
            t=40,
            b=0,
                ))
    
    
    return fig_hist


# Bar Chart
@app.callback(
    Output('fig_bar', 'figure'),
    Input(component_id="date-picker-single",component_property="date"),
    Input(component_id="stock-type",component_property="value"))

def update_graph(date_value, tickers):
    
    if date_value is not None:
        date_object = date.fromisoformat(date_value)
        date_string = date_object.strftime('%B %d, %Y')
    

    df_comb = download_stocks(tickers)

    df_cov = process_for_df_cov(date_value,tickers, df_comb)  
    
    fig_bar = px.bar(df_cov, x="Ticker", y="COV", color="Ticker", text_auto=True, template='plotly_white')
    
    fig_bar.update_traces(textfont_size=7, textangle=0, textposition="inside", cliponaxis=False)
    
    fig_bar.update_xaxes(fixedrange=True)
    fig_bar.update_yaxes(fixedrange=True)
    
    fig_bar.update_layout(uniformtext_minsize=14, uniformtext_mode='hide',
    legend={'x':0,'y':1.05,"orientation":"h"}, title="Coefficient of Var (SD/Mean) from "+date_string),
    fig_bar.update_layout(height=fig_height, width=fig_width, yaxis_title=None, xaxis_title=None)
    
    fig_bar.update_layout(showlegend=False)
    
    
    fig_bar.update_layout(
    margin=dict(
        l=0,
        r=0,
        t=40,
        b=0,
            ))
    
    return fig_bar
    
        
# Runing the application
if __name__ == '__main__':
    app.run_server(debug=True,use_reloader=False)
