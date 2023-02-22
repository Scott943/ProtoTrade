import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

import datetime
from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
import pandas as pd
from threading import Thread
import os
import _thread

from prototrade.file_manager.file_manager import FileManagerObjects
import csv


REFRESH_INTERVAL = 1500
DATETIME_FORMAT = "%y-%m-%d %H:%M:%S"
DEFAULT_STRATEGY = 0
PORT = 8050

class _Grapher:

   def __init__(self, stop_event, file_manager, file_locks, num_strategies):
      logger.debug("STARTING GRAPHER")

      self._stop_event = stop_event
      self._file_manager = file_manager
      self._file_locks = file_locks
      self._num_strategies = num_strategies
      self.create_file_pointers()

   def run_dash_app(self):
      self.app = Dash(__name__)
      self.set_app_layout()
      self.register_callbacks(self.app)
      self.wait_thread = Thread(target=self.wait_for_stop_event)
      self.wait_thread.start()
      self.app.run_server(debug=False, dev_tools_hot_reload=True, threaded=False, port=PORT)

   def wait_for_stop_event(self):
      self._stop_event.wait()
      self.stop() # once stop event is set -> stop grapher

   def create_file_pointers(self):
      self.pnl_file_pointers = []
      self.pos_file_pointers = []
      for strategy_num in range(self._num_strategies):
         loc = self._file_manager.get_strategy_save_location(strategy_num)
         pnl_fp = open(loc/"PnL.csv", "r")
         self.pnl_file_pointers.append(FileManagerObjects(pnl_fp, csv.writer(pnl_fp), csv.reader(pnl_fp)))

         pos_fp = open(loc/"Positions.csv", "r")
         self.pos_file_pointers.append(FileManagerObjects(pos_fp, csv.writer(pnl_fp), csv.reader(pos_fp)))

   def get_pnl_over_time(self, strategy_num):
      fm_pointers = self.pnl_file_pointers[strategy_num]
      # NEED TO EXPOSE THE PNL_FILE_POINTERS
      pnl_csv_reader = fm_pointers.csv_reader
      pnl_fp = fm_pointers.fp
      lock = self._file_locks[strategy_num].pnl_lock

      lock.acquire()
      pnl_fp.seek(0) # seek to start of file to read all
      pnl_list = list(pnl_csv_reader)

      lock.release()

      if len(pnl_list) == 0:
         return None
      
      for pair in pnl_list:
         pair[0] = datetime.datetime.strptime(pair[0], DATETIME_FORMAT)
         pair[1] = float(pair[1])
         pair.append(strategy_num) # appends the strategy number that the pnl came from

      return pnl_list

   def get_pnl_over_time_for_list(self, strategies_list):
      ret = []
      for strategy_num in strategies_list:
         pnl_for_strat = self.get_pnl_over_time(int(strategy_num))
         if pnl_for_strat:
            ret.extend(pnl_for_strat)
      return ret

   def get_pos_over_time_for_list(self, strategies_list, symbol_filter):
      ret = []
      for strategy_num in strategies_list:
         pos_for_strat = self.get_positions_over_time(int(strategy_num), symbol_filter)
         if pos_for_strat:
            ret.extend(pos_for_strat)
      return ret

   def get_positions_over_time(self, strategy_num, symbol_filter):
      fm_pointers = self.pos_file_pointers[strategy_num]
      pos_csv_reader = fm_pointers.csv_reader
      pos_fp = fm_pointers.fp
      lock = self._file_locks[strategy_num].positions_lock

      lock.acquire()
      pos_fp.seek(0)

      positions = []
      if symbol_filter == "ALL":
         positions = list(pos_csv_reader)
      else:
         for row in pos_csv_reader:
               if row[1] in symbol_filter: 
                  positions.append(row)

      lock.release()
      
      for l in positions:
         l[0] = datetime.datetime.strptime(l[0], DATETIME_FORMAT)
         l[2] = int(l[2])
         l.append(strategy_num) # appends the strategy number that the pnl came from

      return positions

   def set_app_layout(self):

      self.app.layout = html.Div(children=[
         html.H1(children='Prototrade'),
            dcc.Interval(id='interval1', interval=REFRESH_INTERVAL, n_intervals=0),
            html.Div(children=[
               
               html.Label(['Graph Type:'], style={'font-weight': 'bold', "text-align": "center"}),
               dcc.Dropdown(["PnL", "Position"], "Position", id='dropdown-graph'),

               html.Label(['Strategy:'], style={'font-weight': 'bold', "text-align": "center"}),
                  dcc.Checklist(list(range(self._num_strategies)), [DEFAULT_STRATEGY], id='checkbox-strategies-to-include'),
               # html.Label(['Strategies To Include:'], style={'font-weight': 'bold', "text-align": "center"}),
               #    dcc.Dropdown(list(range(self._num_strategies)), DEFAULT_STRATEGY, id='dropdown-strategy-number-positions'),
                  
               html.Span(id="positions-selectors-div", children=[
                  
                  html.Label(['Symbols:'], style={'font-weight': 'bold', "text-align": "center"}),
                  dcc.Checklist([],[], id='checkbox-symbol-positions'),
               ]),

               html.Div(id="pnl-selectors-div", children=[
                  
               ], style = {'padding': '5px'}),

         ], style = {'max-width': '200px', 'padding': '5px'}),
      
         dcc.Graph(id='example-graph')
      ],
      style={'font-family':'monospace'})

   def register_callbacks(self, app):
      @app.callback(
         Output('example-graph', 'figure'),
         Input('dropdown-graph', 'value'),
         Input('checkbox-symbol-positions', 'value'),
         Input('checkbox-strategies-to-include', 'value'),
         Input('interval1', 'n_intervals'),
      )
      def update_selected_stocks(graph_type, symbol_list, strategies_list, _):
         # subfig = make_subplots(specs=[[{"secondary_y": True}]]) 
         if graph_type == "PnL":
            pnl_df = self.get_pnl_df(strategies_list)
            return px.line(pnl_df, x="Timestamp", y="PnL", color="Strategy")
         else:
            pos_df = self.get_positions_df(strategies_list, symbol_list)
            return px.line(pos_df, x="Timestamp", y="Position", color="Symbol", line_dash='Strategy', line_shape='hv')

      @app.callback(
         Output('checkbox-symbol-positions', 'options'),
         Input('checkbox-strategies-to-include', 'value')
      )
      def update_symbol_options(strategy_list):
         # get latest
         pos_df = self.get_positions_df(strategy_list)
         return pos_df['Symbol'].unique()

      @app.callback(
         Output('positions-selectors-div', 'style'),
         Output('pnl-selectors-div', 'style'),
         Input('dropdown-graph', 'value')
      )
      def update_shown_components(graph_type):
         # get latest
         if graph_type == "PnL":
            return [{'display': 'none'}, {'display': 'block'}]

         return [{'display': 'block'}, {'display': 'none'}]


   def get_pnl_df(self, strategies_list):
      return pd.DataFrame(self.get_pnl_over_time_for_list(strategies_list), columns = ['Timestamp', 'PnL', 'Strategy']) # convert to dataframe

   def get_positions_df(self, strategies_list, symbol_list = "ALL"):
      return pd.DataFrame(self.get_pos_over_time_for_list(strategies_list, symbol_list), columns = ['Timestamp', 'Symbol', 'Position', 'Strategy']) # convert to dataframe
      
   def stop(self):
      logger.debug("Try stop dash")

      # this might just release locks in the thread?
      for file_locks_for_strategy in self._file_locks:
         if file_locks_for_strategy.pnl_lock.acquire(False):
            file_locks_for_strategy.pnl_lock.release()

         if file_locks_for_strategy.positions_lock.acquire(False):
            file_locks_for_strategy.positions_lock.release()

      for obj in self.pnl_file_pointers:
         obj.fp.close()

      for obj in self.pos_file_pointers:
         obj.fp.close()

      # close files
      logger.debug("Close dash")
      os._exit(0)

      # func = request.environ.get('werkzeug.server.shutdown')
      # if func is None:
      #    raise RuntimeError('Not running with the Werkzeug Server')
      # func()
      # logger.debug("Stopped Dash server")

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.


# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
