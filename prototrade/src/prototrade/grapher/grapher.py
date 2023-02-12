import datetime
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from threading import Thread
from flask import request
import logging
import os
import _thread


DATETIME_FORMAT = "%y-%m-%d %H:%M:%S"
DEFAULT_STRATEGY = 0

class _Grapher:

   def __init__(self, stop_event, file_manager, file_locks, num_strategies):
      logging.debug("STARTING GRAPHER")

      self.pos_over_time = [[
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

      self.pnl_over_time = [[
      [datetime.datetime(2023, 2, 8, 15, 32, 26), 21, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 27), 21, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 28), 8, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 29), 28, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 29), 8, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 30), 28, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 31), 15, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 32), 37, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 32), 15, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 33), 37, 0], 
      [datetime.datetime(2023, 2, 8, 15, 32, 34), 19, 0]],

      [
      [datetime.datetime(2023, 2, 8, 15, 32, 26), 66, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 27), 55, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 28), 12, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 29), 33, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 29), 33, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 30), 33, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 31), 35, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 32), -5, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 32), -8, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 33), 1, 1], 
      [datetime.datetime(2023, 2, 8, 15, 32, 34), 12, 1]]

      ]

      self._stop_event = stop_event
      self._file_manager = file_manager
      self._file_locks = file_locks
      self._num_strategies = num_strategies

   def run_dash_app(self):
      self.app = Dash(__name__)
      self.set_app_layout()
      self.register_callbacks(self.app)
      self.wait_thread = Thread(target=self.wait_for_stop_event)
      self.wait_thread.start()
      self.app.run_server(debug=False, dev_tools_hot_reload=True, threaded=False, port=8061)

   def wait_for_stop_event(self):
      self._stop_event.wait()
      self.stop() # once stop event is set -> stop grapher

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
         pair.append(strategy_num) # appends the strategy number that the pnl came from

      return pnl_list

   def get_pnl_over_time_for_list(self, strategies_list):
      ret = []
      for strategy_num in strategies_list:
         ret.extend(self.get_pnl_over_time(int(strategy_num)))

      return ret

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

   def set_app_layout(self):
      self.app.layout = html.Div(children=[
      html.H1(children='Prototrade'),

      dcc.Dropdown(["PnL", "Position"], "Position", id='dropdown-graph'),

      dcc.Dropdown(list(range(self._num_strategies)), DEFAULT_STRATEGY, id='dropdown-strategy-number-positions'),
      dcc.Checklist([],[], id='checkbox-symbol-positions'),

      dcc.Checklist(list(range(self._num_strategies)), [DEFAULT_STRATEGY], id='checkbox-strategy-number-pnl'),

      dcc.Graph(id='example-graph')
      ],
      style={'font-family':'monospace'})

   def register_callbacks(self, app):
      @app.callback(
         Output('example-graph', 'figure'),
         Input('dropdown-graph', 'value'),
         Input('dropdown-strategy-number-positions', 'value'),
         Input('checkbox-symbol-positions', 'value'),
         Input('checkbox-strategy-number-pnl', 'value'),
      )
      def update_selected_stocks(graph_type, strategy_num, symbol_list, strategies_list):
         # subfig = make_subplots(specs=[[{"secondary_y": True}]]) 
         if graph_type == "PnL":
            pos_df = pd.DataFrame(self.get_pnl_over_time_for_list(strategies_list), columns = ['Timestamp', 'PnL', 'Strategy']) # convert to dataframe
            return px.line(pos_df, x="Timestamp", y="PnL", color="Strategy")
         else:
            pos_df = pd.DataFrame(self.pos_over_time[strategy_num], columns = ['Timestamp', 'Symbol', 'Position']) # convert to dataframe
            filtered_df = pos_df[pos_df['Symbol'].isin(symbol_list)]
            return px.line(filtered_df, x="Timestamp", y="Position", color="Symbol", line_shape='hv')

      @app.callback(
         Output('checkbox-symbol-positions', 'options'),
         Input('dropdown-strategy-number-positions', 'value')
      )
      def update_symbol_options(strategy_number):
         # get latest
         pos_df = pd.DataFrame(self.pos_over_time[strategy_number], columns = ['Timestamp', 'Symbol', 'Position']) # convert to dataframe
         return pos_df['Symbol'].unique()

      @app.callback(
         Output('dropdown-strategy-number-positions', 'style'),
         Output('checkbox-symbol-positions', 'style'),
         Output('checkbox-strategy-number-pnl', 'style'),
         Input('dropdown-graph', 'value')
      )
      def update_shown_components(graph_type):
         # get latest
         if graph_type == "PnL":
            return [{'display': 'none'}, {'display': 'none'}, {'display': 'block'}]

         return [{'display': 'block'}, {'display': 'block'}, {'display': 'none'}]

   def stop(self):
      logging.debug("Try stop dash")
      

      for file_locks_for_strategy in self._file_locks:
         if file_locks_for_strategy.pnl_lock.acquire(False):
            file_locks_for_strategy.pnl_lock.release()

         if file_locks_for_strategy.positions_lock.acquire(False):
            file_locks_for_strategy.positions_lock.release()

      # close files
      logging.debug("Close dash")
      os._exit(0)

      # func = request.environ.get('werkzeug.server.shutdown')
      # if func is None:
      #    raise RuntimeError('Not running with the Werkzeug Server')
      # func()
      # logging.debug("Stopped Dash server")

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
