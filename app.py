'''Imports'''
import requests 
import calendar
import json
from pandas import Series
from pandas import DataFrame
from pandas import to_datetime
from bokeh.plotting import figure
from bokeh.plotting import show
from bokeh.io import show as ShowIo
from bokeh.models import TextInput
from bokeh.models import Column
from bokeh.models import Button
from bokeh.events import Event
from bokeh.models import CustomJS
from bokeh.models import ColumnDataSource
import sys
from datetime import datetime
from datetime import timedelta
import winreg
'''Variables'''
StartUrl = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol="
MidUrl = "&outputsize=compact&apikey="
DemoUrl = "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=SHOP.TRT&outputsize=compact&apikey=demo"
WelcomeMessage = "Enter a stock symbol to see a graph of last month's closing prices:"
''''''
'''Functions'''
def CleanString(InputString):
    CapString = InputString.upper()
    CleanString = CapString.strip()
    return CleanString
def GetUserEnvironmentVariable(name):
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Environment")
    try:
        return winreg.QueryValueEx(key, name)[0]
    except:
        return "demo"
'''If the user currently has an environment variable for ALPHA_ADVANTAGE_API_KEY set up
   then this will work, else it will just submit demo.  
   That will still return results, just not the results you want:
       The **demo** API key is for demo purposes only. 
       Please claim your free API key at (https://www.alphavantage.co/support/#api-key)
'''
def GetSubmitUrl(InputSymbol):
    UrlSymbol = CleanString(InputSymbol)
    try:
        ApiKey = GetUserEnvironmentVariable("ALPHA_ADVANTAGE_API_KEY")
    except:
        ApiKey = "demo"
    SubmitUrl = StartUrl + UrlSymbol + MidUrl + ApiKey
    return SubmitUrl
''''''
'''Procedure: Get all dates for last month'''
myCalendar = calendar.Calendar()
Today = datetime.today()
OneMonthAgo = Today + timedelta(days=-30)
ThatYear = int(OneMonthAgo.strftime('%Y'))
ThatMonth = int(OneMonthAgo.strftime('%m'))
LastMonthDates = []
for CalDate in myCalendar.itermonthdates(year=ThatYear,month=ThatMonth):
    LastMonthDates.append(str(CalDate))
IbmUrl = GetSubmitUrl("IBM")
'''Functions:'''
def GetStockDataFrame(InputUrl=IbmUrl):
    ClosingPrices = []
    StockDates = []
    try:
        RawResults = requests.get(url=InputUrl)
    except:
        RawResults = requests.get(url=DemoUrl)
    Results = RawResults.json()
    TimeSeries = Results['Time Series (Daily)']
    for Date in LastMonthDates:
        try:
            Close = TimeSeries[Date]["4. close"]
            ClosingPrices.append(Close)
            StockDates.append(Date)
        except:
            pass
    ClosingPricesData = {"Dates": StockDates, "Prices": ClosingPrices}
    ClosingPricesDataFrame = DataFrame(ClosingPricesData,columns=["Dates","Prices"])
    ClosingPricesDataFrame["Prices"] = ClosingPricesDataFrame["Prices"].astype(float)
    ClosingPricesDataFrame["Dates"] = ClosingPricesDataFrame["Dates"].astype('datetime64')
    ClosingPricesDataFrame["Dates"] = to_datetime(ClosingPricesDataFrame["Dates"] )
    return ClosingPricesDataFrame
''''''
DataFrame = GetStockDataFrame(IbmUrl)
source = ColumnDataSource(DataFrame)
InputSymbol = "IBM"
''''''
'''This callback does not currently work :( '''
Callback = CustomJS(args=dict(source=source), code="""
// JavaScript code goes here
// the model that triggered the callback is cb_obj:
// models passed as args are automagically available
    var InputSymbol = cb_obj.value
    var NewData = GetStockDataFrame(GetSubmitUrl(InputSymbol))
    var NewDataSource = ColumnDataSource(NewData)
    var x = NewDataSource.Dates
    var y = NewDataSource.Prices
    source.change.emit();
""")
''''''
PageGraph = figure(title="Last Month's Closing Prices", plot_width = 600, plot_height = 400, x_axis_type = 'datetime')
PageGraph.line(x = DataFrame["Dates"], y = DataFrame["Prices"], line_width = 2)
TextInputObject = TextInput(value="IBM", title=WelcomeMessage)
TextInputObject.js_on_change('value',Callback)
Page = Column(TextInputObject,PageGraph)
ShowIo(Page)