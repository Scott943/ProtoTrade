import datetime

DATETIME_FORMAT = "%y-%m-%d %H:%M:%S"

class _Grapher:

   def __init__(self, file_manager, file_locks):
      self._file_manager = file_manager
      self._file_locks = file_locks

   def get_pnl_over_time(self, strategy_num):
      self._file_locks[strategy_num].pnl_lock.acquire()
      self.pnl_file.seek(0) # seek to start of file to read all
      
      pnl_list = list(self.csv_reader_pnl)

      if len(pnl_list) == 0:
         self._file_locks.pnl_lock.release()
         return None
      
      self._file_locks[strategy_num].pnl_lock.release()

      for pair in pnl_list:
         pair[0] = datetime.datetime.strptime(pair[0], DATETIME_FORMAT)
         pair[1] = float(pair[1])

      return pnl_list

   def get_positions_over_time(self, strategy_num, symbol_filter = None):
      positions = []

      self._file_locks[strategy_num].positions_lock.acquire()
      self.positions_file.seek(0)

      if symbol_filter:
         for row in self.csv_reader_positions:
               if row[1] == symbol_filter: 
                  positions.append(row)
      else:
         positions = list(self.csv_reader_positions)

      for l in positions:
         l[0] = datetime.datetime.strptime(l[0], DATETIME_FORMAT)
         l[2] = int(l[2])

      self._file_locks[strategy_num].positions_lock.release()
      return positions


# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd

app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

pos_over_time = [[
[datetime.datetime(2023, 2, 8, 15, 32, 26), 'AAPL', 21], 
[datetime.datetime(2023, 2, 8, 15, 32, 26), 'AAPL', 21], 
[datetime.datetime(2023, 2, 8, 15, 32, 26), 'PLTR', 8], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'AAPL', 26], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'PLTR', 8], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'AAPL', 26], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'PLTR', 11], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'AAPL', 37], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'PLTR', 11], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'AAPL', 37], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'PLTR', 19]],

[[datetime.datetime(2023, 2, 8, 15, 32, 26), 'MSFT', 21], 
[datetime.datetime(2023, 2, 8, 15, 32, 26), 'MSFT', 21], 
[datetime.datetime(2023, 2, 8, 15, 32, 26), 'AAPL', 8], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'MSFT', 28], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'AAPL', 8], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'MSFT', 28], 
[datetime.datetime(2023, 2, 8, 15, 32, 29), 'AAPL', 15], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'MSFT', 37], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'AAPL', 15], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'MSFT', 37], 
[datetime.datetime(2023, 2, 8, 15, 32, 32), 'AAPL', 19]]]


app.layout = html.Div(children=[
    html.H1(children='Prototrade'),

    dcc.Dropdown([0, 1], 1, id='strategy-selector'),
    dcc.Checklist(['PLTR', 'AAPL'],['PLTR', 'AAPL'], id='symbol-checkboxes'),

    dcc.Graph(
        id='example-graph',
    )
])

@app.callback(
    Output('example-graph', 'figure'),
    Input('strategy-selector', 'value'),
    Input('symbol-checkboxes', 'value'),
)
def update_selected_stocks(strategy_num, symbol_list):
    print(symbol_list)
    strategy_num = int(strategy_num)
    pos_df = pd.DataFrame(pos_over_time[strategy_num], columns = ['Timestamp', 'Symbol', 'Position']) # convert to dataframe
    filtered_df = pos_df[pos_df['Symbol'].isin(symbol_list)]
    return px.line(filtered_df, x="Timestamp", y="Position", color="Symbol", line_shape='hv')

@app.callback(
    Output('symbol-checkboxes', 'options'),
    Input('strategy-selector', 'value')
)
def update_symbol_options(strategy_number):
    # get latest
    print(pos_over_time[strategy_number])
    pos_df = pd.DataFrame(pos_over_time[strategy_number], columns = ['Timestamp', 'Symbol', 'Position']) # convert to dataframe
    return pos_df['Symbol'].unique()


if __name__ == '__main__':
    app.run_server(debug=True, dev_tools_hot_reload=True)