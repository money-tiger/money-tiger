# -*- coding: utf-8 -*-
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_table
import dash_core_components as dcc
import os
import time
import datetime
from datetime import date
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import normalize
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
import fileupload
from fileupload import PROCESS_DIRECTORY, UPLOAD_DIRECTORY
from app import app
import research
from settings import *

# Globals
MHO = 'klalit'  # medical health organization
MHO_df = pd.DataFrame()
MHO_d2v_df = pd.DataFrame()
current_file = ''
selected_row_id = 0
changes_work_df = pd.DataFrame()  # loaded file
work_df_numeric = pd.DataFrame()  # loaded file with d2v columns
freeze_state_of_work_df = pd.DataFrame()  # saving the state of the last update of the file
MHO_dict = {'klalit': 'כללית', 'meohedet': 'מאוחדת', 'macabi': 'מכבי'}
clusters = list()
file_save_clicks = 0
cluster_lock = False
save_file_lock = True
save_clicks = 0
next_row_id = 0
EPS = 1  # clustering distance parameter
cell_id = 0
t_cols_mapping = dict()
t_cols_preproc = [list(), list()]
PREV_NOT_ANSWERD = 0


class cluster:
    def __init__(self, labels, core_sample_indices_, label, df, df_answers):
        labels = list(labels)
        core_samples_mask = np.zeros_like(labels, dtype=bool)
        core_samples_mask[core_sample_indices_] = True
        self.rows = labels == label
        self.cash = df[money_col[MHO]][self.rows].sum()
        self.N_rows = sum(self.rows)
        cluster_not_answered_indexes = [i for i, e in enumerate(self.rows) if e]
        not_answered_index = [i for i, e in enumerate(freeze_state_of_work_df[REJECT_COL[MHO]].isnull()) if e]
        self.base_idx = not_answered_index[cluster_not_answered_indexes[0]]
        self.base = df[self.rows].iloc[[0]]
        self.df_answers = df_answers
        self.answers = set()

    def __repr__(self):
        return str(self.__dict__)

    def get_close(self):
        temp_base = self.base.copy()
        temp_filename = current_file
        temp_filename = temp_filename.replace("new_", "")
        split = temp_filename.split('_')
        temp_file_name = split[0] + '_' + split[1] + '_' + split[2]
        for i, col in enumerate(t_cols[MHO]):
            temp_base[col] = research.get_column_from_d2v_file(i, 'd2v_files', temp_file_name, [self.base_idx])
        close_answers = research.get_close(MHO_df, self.df_answers, temp_base, (1, 1, 1, 1, 1, 1), MHO)
        ans_list = list(close_answers[REJECT_COL[MHO]].values)
        # ans_list = [a for a in ans_list if a is not None and a is not "" and not isinstance(a, float)]
        self.answers = set(ans_list)

    def update(self, i, price):
        self.N_rows = self.N_rows - 1
        self.cash = self.cash - price
        self.rows[i] = False

    def isEmpty(self):
        return self.N_rows == 0


def create_t_cols():
    """ loading the d2v files at the starting of the system and stoeing them for later use"""
    global t_cols_mapping, t_cols_preproc
    t_cols_mapping[0] = dict()
    t_cols_mapping[1] = dict()
    for file_name in os.listdir('d2v_files'):
        if 't_cols_0' in file_name:
            i = 0
        else:
            i = 1
        parts = file_name.split("_")
        if len(parts) > 4:
            temp_file_name = parts[0] + '_' + parts[1] + '_' + parts[2]
        else:
            temp_file_name = parts[0]
        t_cols_mapping[i][temp_file_name] = len(t_cols_preproc[i])
        t_cols_preproc[i].append(research.get_column_from_d2v_file(i, 'd2v_files', temp_file_name))


create_t_cols()


def get_t_cols(i, filename):
    global t_cols_mapping, t_cols_preproc
    return t_cols_preproc[i][t_cols_mapping[i][filename]]


def create_mho_DB(MHO):
    """ loading the file of the answered past files of the relevant MHO"""
    resultfile = PROCESS_DIRECTORY + MHO + '_processed.xlsx'
    xl = pd.ExcelFile(resultfile)
    return xl.parse(xl.sheet_names[0])


df_klalit = create_mho_DB('klalit')
df_meohedt = pd.DataFrame()  # create_mho_DB('meohedt')
df_macabi = pd.DataFrame()  # create_mho_DB('macabi')
MHO_df = df_klalit # while klalit is the only MHO, it is convenient to make it the default

def add_d2v_columns(df, MHO, filename=''):
    """ adding the necessary columns for the DOC2VEC processing"""
    dff = df[cols[MHO] + [FILTER_COL[MHO]] + [REJECT_COL[MHO]]]
    df_result = pd.DataFrame()
    for i, col in enumerate(t_cols[MHO]):
        df_result[col] = get_t_cols(i, filename)

    for col in cols[MHO] + [FILTER_COL[MHO]] + [REJECT_COL[MHO]]:
        if col not in t_cols[MHO]:
            df_result[col] = dff[col]
    return df_result


# in case of adding MHO copy and adjust the first line
# or follow the insructions in the guide
df_numeric_klalit = add_d2v_columns(df_klalit, 'klalit', 'klalit')
df_numeric_meohedt = pd.DataFrame()  # add_d2v_columns(df_meohedt, 'meohedt')
df_numeric_macabi = pd.DataFrame()  # add_d2v_columns(df_macabi, 'macabi')


def generate_basic_table(dataframe, max_rows=5):
    return html.Table(
        # Header
        [html.Tr([html.Th(col, style={'textAlign': 'right'}) for col in dataframe.columns])] +
        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col], style={'textAlign': 'right'}) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
        , style={'textAlign': 'right'})


def generate_selection_table(dataframe):
    """ this func creates the table for selecting the row to show the relevant answers in the singles tab"""
    return html.Div([
        dash_table.DataTable(
            id='table1',
            data=dataframe.to_dict('rows'),
            columns=[{'id': c, 'name': c} for c in dataframe.columns],
            selected_rows=[0],
            row_selectable='single',
            style_cell={'textAlign': 'center', 'font-family': 'Arial', 'font-size': '12px'},
            style_header={'fontWeight': 'bold'},
            style_table={'width': '700px'},
        ),
    ])


def generate_KNN_results_table(dataframe):
    """ creating the table showing the answers chosen as closest to the current line"""
    return html.Div([
        dash_table.DataTable(
            id='table2',
            data=dataframe.to_dict('rows'),
            columns=[{'id': c, 'name': c} for c in dataframe.columns],
            style_cell={'minWidth': '0px', 'maxWidth': '100px', 'whiteSpace': 'normal', 'text-overflow': 'inherit',
                        'textAlign': 'center', 'font-family': 'Arial', 'font-size': '12px'},
            style_header={'fontWeight': 'bold'},
            css=[{'selector': '.dash-cell div.dash-cell-value',
                  'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;', }],
        ), ], style={"width": '900px'})


def get_days(day, month, year):
    """ returning the number of days left to work on the current file"""
    filedate = date(int(year), int(month), int(day))
    delta = datetime.date.today() - filedate
    return str(90 - delta.days)


def parse_file_name(file_name):
    filename = file_name
    if file_name == '':
        return ''
    file_name = file_name.replace(".xlsx", "").replace("new_", "").replace("finished_", "")
    parts = file_name.split("_")
    # get number of empty lines
    xl = pd.ExcelFile(UPLOAD_DIRECTORY + filename)
    temp_df = xl.parse(xl.sheet_names[0])
    blank_rows = str(len(temp_df[temp_df[REJECT_COL[parts[0]]].isnull()].index))
    date = parts[3].split("-")
    days_left = get_days(date[0], date[1], date[2])
    return MHO_dict[parts[0]] + ' ' + parts[1] + '/' + parts[2][
                                                       2:] + ', ' + blank_rows + ' ' + 'שורה' + ', ' + days_left + ' ' + 'יום'


file_list = [({'label': parse_file_name(fname), 'value': fname} if 'new' in fname else ()) for fname in
             os.listdir(UPLOAD_DIRECTORY)]

# GUI
app.layout = html.Div([
    html.Div(className="row", style={'direction': 'rtl', 'vertical-align': 'middle'}, children=[
        html.Img(src=app.get_asset_url('logo3.png'), style={'width': '25%', 'display': 'inline-block'}),
        html.Div([
            html.Details([
                html.Summary('בחר קובץ:'),
                dcc.Loading(id='load', children=[html.Div(id='div_loading',
                                                          children=[dcc.Dropdown(id='filename',
                                                                                 options=file_list,
                                                                                 value='Select a file...',
                                                                                 style={
                                                                                     'width': '100%',
                                                                                     'display': 'inline-block',
                                                                                     'textAlign': 'right',
                                                                                     'margin': 'auto'},
                                                                                 clearable=False
                                                                                 )]), ], type='graph',
                            fullscreen=True),
                html.Div(html.Button('שמור קובץ', id='file-save-btn'),
                         style={'display': 'inline-block', 'padding-bottom': '10px'}), ]),
            html.Details([
                html.Summary('שינוי פרמטר:'),
                html.Div(dcc.Slider(
                    id='slider-eps', min=0, max=5, step=0.1, marks={0: '0', 1: '1', 2: '2', 3: '3', 4: '4', 5: '5'},
                    value=1),
                    style={"padding-bottom": '20px'})]), ], style={'width': '30%', 'display': 'inline-block'}), ]),
    dcc.Loading(id='load4', children=[html.Div(id='loader4')]),
    dcc.Tabs(id="tabs", value='tab-singles', children=[
        dcc.Tab(label='בודדים', value='tab-singles'),
        dcc.Tab(label='קבוצות', value='tab-clusters'),
        dcc.Tab(label='מענה גורף', value='tab-rules'),
        dcc.Tab(label='ניהול קבצים', value='tab-file-settings'), ]),
    dcc.Loading(id='load2', children=[html.Div(id='loading2')], type='cube', fullscreen=True),
    html.Div(id='msg-confirm-save'),
    html.Div(id='tabs-content')])


@app.callback(Output('loader4', 'children'),
              [Input('current-cluster-table', 'active_cell')],
              [State('current-cluster-table', 'derived_virtual_data'), State('current-cluster-table', 'columns')])
def set_cell(cell, rows, columns):
    "saving the current cell to work on chosen by the user"
    global cell_id
    if columns[cell[1]]['id'] == FILTER_COL[MHO]:
        cell_id = rows[cell[0]][FILTER_COL[MHO]]
    else:
        cell_id = 0
    return ''


@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value'), Input('filename', 'value'), Input('slider-eps', 'value')], )
def render_content(tab, filename, slider_eps):
    " GUI: building the tabs and the components displayed in them"
    global cell_id
    if cell_id == 0:
        input_box = dcc.Input(id='input-id', placeholder='...', type='text', style={'textAlign': 'right'})
    else:
        input_box = dcc.Input(id='input-id', value=cell_id, type='text', style={'textAlign': 'right'})

    if tab == 'tab-singles':
        return html.Div([
            html.Table(
                [html.Tr([html.Th(html.Label('הכנסת תשובה'), style={'textAlign': 'right'}),
                          html.Th(html.Label('בחירת עמודות'), style={'textAlign': 'right'}),
                          html.Th(html.Label('בחירת משקלים'), style={'textAlign': 'right'}),
                          html.Th(html.Label('תעודת זהות'), style={'textAlign': 'right'})])] +
                [html.Tr([
                    html.Td(html.Div(
                        [html.Button('עדכן', id='btn-answer', n_clicks_timestamp=0),
                         dcc.Input(id='input-answer', placeholder='...', type='text',
                                   style={'height': '100px', 'textAlign': 'right'}),
                         dcc.Loading(id='load3', children=[html.Div(id='loader3')], fullscreen=True)])),
                    html.Td(dcc.Dropdown(
                        id='columns',
                        options=[{'label': col_, 'value': col_} for col_ in list(MHO_df.columns.values)],
                        value=[col_ for col_ in cols[MHO]], multi=True, style={'width': '95%'}
                    ), style={"width": '400px', " padding-right": '100px'}),
                    html.Td(html.Div([
                        html.Div(dcc.Slider(id='slider' + str(i_col), min=0, max=5,
                                            step=1, dots=True, marks={2.5: label}, value=1, ),
                                 style={"padding-bottom": '20px'})
                        for i_col, label in enumerate(cols[MHO])
                    ], style={'width': '200px', 'margin': 'auto', "padding-bottom": "5px"})),
                    html.Td(html.Div([input_box, html.Div(id='next-id')])), ])]),
            html.Div(html.Div(id='output-table'), style={'align': 'center', 'direction': 'rtl'}),
            html.Div(html.Button('הצג', id='btn-1', n_clicks_timestamp=0), style={'direction': 'rtl'}),
            html.Div(html.Div(id='knn-out'), style={'margin': 'auto', 'direction': 'rtl'}),
            html.Div(id="row-selection", style={'display': 'none'}),
            dcc.ConfirmDialog(id='3-params')])
    elif tab == 'tab-rules':
        return html.Div(style={'direction': 'rtl'}, children=[
            html.Label('בחר חוק:'),
            dcc.Dropdown(
                id='rules-input',
                # For new rules add {'label': '<rule name>, 'value': <rule number>}
                options=[{'label': 'סכום 0', 'value': 0}, ],
                value='',
                style={'width': '50%', 'textAlign': 'right'}
            ),
            html.Div(id='rule-count'),
            html.Div(id='rule-table'),
            html.Button('עדכן', id='rule-update-btn'),
            dcc.Loading(id='load_rule', children=[html.Div(id="placeholder3")], type='cube', fullscreen=True),
        ])

    elif tab == 'tab-file-settings':
        return fileupload.layout

    elif tab == 'tab-clusters':
        cell_id = 0
        if (current_file == '' or current_file == 'Select a file...'):
            return html.Div(
                [dcc.ConfirmDialog(id='confirm-next-has-file', message='בחר קובץ לעריכה..', displayed=True)])

        else:
            while not save_file_lock:
                time.sleep(0.1)
            return html.Div([
                html.Div(id='answer-label'),
                html.Div(children=[
                    html.Details([
                        html.Summary('בחר מקבץ:'),
                        html.Div(id='table_chose_cluster', children=[clusters_display(clusters)],
                                 style={'display': 'inline-block', 'direction': 'rtl'}),
                    ]),
                    html.Details([
                        html.Summary('צפייה במקבץ:'),
                        html.Div(children=[html.Button('שמור', id='save-btn'),
                                           html.Div(id='table_display_cluster',
                                                    style={'width': '70%', 'display': 'inline-block',
                                                           'height': '500px'}),
                                           html.Details([
                                               html.Summary('צפייה במפתח התשובות:'),
                                               html.Div(id='key_table')],
                                               style={'width': '20%', 'display': 'inline-block'}), ]), ]),
                    html.Details([
                        html.Summary('מענה אחיד למקבץ:'),
                        dcc.Loading(id='load_uniform', children=[html.Div(id='answer_for_all', children=[
                            dcc.Dropdown(id='one_answer_dropdown',
                                         options=[
                                             {'label': i, 'value': i} for i in range(0)],
                                         value='',
                                         style={'width': '60%', 'display': 'inline-block', 'textAlign': 'right',
                                                'margin': 'auto'},
                                         clearable=False), ])]),
                        html.Button('עדכן בחירה', id='update-all-btn'), ]), ]),
            ], style={'direction': 'rtl'})


@app.callback(Output('next-id', 'children'),
              [Input('btn-answer', 'n_clicks'), Input('filename', 'value')])
def next_row(clicks, filename):
    "offers the best row to work on next"
    global next_row_id, changes_work_df, PREV_NOT_ANSWERD
    if (filename != "" and filename != 'Select a file...') or clicks is not None:
        while len(changes_work_df.index) <= 0:
            time.sleep(0.1)
        while not save_file_lock:
            time.sleep(0.1)
        temp_df = changes_work_df[research.ID_COL_NAME[MHO]]
        not_answered_index = [i for i, e in enumerate(changes_work_df[REJECT_COL[MHO]].isnull()) if e]
        next_row_id = temp_df.iloc[not_answered_index[0]]
        while next_row_id == PREV_NOT_ANSWERD:
            not_answered_index = [i for i, e in enumerate(changes_work_df[REJECT_COL[MHO]].isnull()) if e]
            next_row_id = temp_df.iloc[not_answered_index[0]]
        PREV_NOT_ANSWERD = next_row_id
        return html.Div(html.Label("הבא:" + str(next_row_id)))


@app.callback(
    Output('rule-table', 'children'),
    [Input('rules-input', 'value')])
def print_rule(rule_id):
    "prints the result of applying the last used rule"
    if len(changes_work_df.index) <= 0:
        return ''
    if rule_id == 0:
        temp_df = changes_work_df[REJECT_COL[MHO]].isnull()
        zero_rows = changes_work_df[research.money_col[MHO]] == 0
        new_zero_rows = temp_df & zero_rows
        return str(sum(new_zero_rows)) + " הם שורות סכום אפס "
    return ''


rule_clicks = 0


@app.callback(
    Output('placeholder3', 'children'),
    [Input('rule-update-btn', 'n_clicks'), Input('rules-input', 'value')])
def update_rule(clicks, rule_id):
    "applying the rule chosen"
    global changes_work_df, rule_clicks
    if len(changes_work_df.index) <= 0:
        return ''
    if clicks is not None and clicks > rule_clicks:
        rule_clicks = clicks
        # in case of adding new rules update them here according to their number and add their actions
        if rule_id == 0:
            temp_df = changes_work_df[REJECT_COL[MHO]].isnull()
            zero_rows = changes_work_df[research.money_col[MHO]] == 0
            new_zero_rows = temp_df & zero_rows
            zero_rows_index = [i for i, e in enumerate(new_zero_rows) if e]
            number_of_rows = sum(new_zero_rows)
            if number_of_rows > 0:
                changes_work_df[REJECT_COL[MHO]].iloc[zero_rows_index] = 'ערעור 0 ש"ח. אין ערעור כספי.'
                changes_work_df[CHOISE_COL[MHO]].iloc[zero_rows_index] = 'אושר'
    return ''


research_clicks = 0


@app.callback(
    Output('loader3', 'children'),
    [Input('btn-answer', 'n_clicks')],
    [State('input-id', 'value'), State('input-answer', 'value')])
def update_answer(clicks, id, answer):
    """ stets the answer entered to the line"""
    global changes_work_df, research_clicks, research_lock
    if len(changes_work_df.index) <= 0:
        return ''
    if clicks is not None and clicks > research_clicks:
        research_clicks = clicks
        id_rows = changes_work_df[FILTER_COL[MHO]] == int(id)
        changed_row = [i for i, e in enumerate(id_rows) if e][selected_row_id]
        changes_work_df[REJECT_COL[MHO]].iloc[[changed_row]] = answer
        changes_work_df[CHOISE_COL[MHO]].iloc[[changed_row]] = 'נדחה'
    return ''


@app.callback(Output('confirm-save', 'displayed'),
              [Input('confirm-save', 'submit_n_clicks')])
def display_confirm(clicks):
    if clicks is not None:
        return False


@app.callback(Output('confirm-next-has-file', 'displayed'),
              [Input('tabs', 'value'), Input('confirm-next-has-file', 'submit_n_clicks')])
def display_confirm_next(tab, clicks):
    global current_file
    if clicks is not None:
        return False


@app.callback(
    [Output('div_loading', 'children'), Output('msg_confirm-save', 'children')],
    [Input('file-save-btn', 'n_clicks')])
def save_file(clicks):
    """saving the work done on the current file"""
    global file_save_clicks, current_file, save_file_lock, file_list
    if clicks is None:
        return dcc.Dropdown(id='filename',
                            options=file_list,
                            value='Select a file...',
                            style={'width': '100%', 'display': 'inline-block', 'textAlign': 'right', 'margin': 'auto'},
                            clearable=False), ""

    while not save_file_lock:
        time.sleep(0.1)
    if current_file == '':
        return dcc.Dropdown(id='filename',
                            options=file_list,
                            value='Select a file...',
                            style={'width': '100%', 'display': 'inline-block', 'textAlign': 'right', 'margin': 'auto'},
                            clearable=False), ""
    if clicks is not None and clicks > file_save_clicks:
        file_save_clicks = clicks
        changes_work_df.to_excel(UPLOAD_DIRECTORY + current_file, index=False)
        create_clusters_aux()
        file_list = [({'label': parse_file_name(fname), 'value': fname} if 'new' in fname else ()) for fname in
                     os.listdir(UPLOAD_DIRECTORY)]
    return dcc.Dropdown(id='filename',
                        options=file_list,
                        value=current_file,
                        style={'width': '100%', 'display': 'inline-block', 'textAlign': 'right', 'margin': 'auto'},
                        clearable=False), \
           html.Div(dcc.ConfirmDialog(
               id='confirm-save', message='השינויים נשמרו', displayed=True))


@app.callback(
    Output('output-table', 'children'),
    [Input('input-id', 'value'), Input('columns', 'value')])
def display_selection_table(visit_id, columns):
    if len(changes_work_df.index) <= 0:
        return ''
    if cell_id != 0:
        return generate_selection_table(changes_work_df[changes_work_df[FILTER_COL[MHO]] == cell_id][columns])
    if (visit_id is None) or (not visit_id.isdigit()):
        return "הכנס מספר תז"
    else:
        return generate_selection_table(changes_work_df[changes_work_df[FILTER_COL[MHO]] == int(visit_id)][columns])


@app.callback(
    Output('row-selection', 'children'),
    [Input('table1', "selected_rows")])
def set_selected_rows(selected_rows):
    global selected_row_id
    if selected_rows is not None and len(selected_rows) > 0:
        selected_row_id = selected_rows[0]
    else:
        selected_row_id = 0
    return ''


@app.callback(
    [Output('knn-out', 'children'), Output('3-params', 'displayed'), Output('3-params', 'message')],
    [Input('input-id', 'value'),
     Input('columns', 'value'),
     Input('btn-1', 'n_clicks')],
    [State('3-params', 'displayed'), State('slider0', 'value'), State('slider1', 'value'), State('slider2', 'value'),
     State('slider3', 'value'),
     State('slider4', 'value'), State('slider5', 'value')])
def selected_id_knn(visit_id, columns, clicks, error_msg, sld0, sld1, sld2, sld3, sld4, sld5):
    """performs KNN on the selected row according to the selected weight parameters """
    if error_msg:
        return "בחר שורה", True, "לפחות 3 פרמטרים חייבים להיות עם משקל גדול מאפס"
    weights = (sld0, sld1, sld2, sld3, sld4, sld5)
    if sum(a > 0 for a in weights) <= 2:
        return "בחר שורה", True, "לפחות 3 פרמטרים חייבים להיות עם משקל גדול מאפס"
    if clicks is None:
        return "בחר שורה", False, ""
    if visit_id is None or (not isinstance(visit_id, int) and not visit_id.isdigit()):
        return "בחר שורה", False, ""
    else:
        row = changes_work_df[changes_work_df[FILTER_COL[MHO]] == int(visit_id)]
        idx = changes_work_df.index[changes_work_df[FILTER_COL[MHO]] == int(visit_id)].tolist()
        temp_filename = current_file
        temp_filename = temp_filename.replace("new_", "")
        split = temp_filename.split('_')
        temp_file_name = split[0] + '_' + split[1] + '_' + split[2]
        for i, col in enumerate(t_cols[MHO]):
            row[col] = research.get_column_from_d2v_file(i, 'd2v_files', temp_file_name, idx)
        columns_extended = columns + [REJECT_COL[MHO]] + [FILTER_COL[MHO]]
        selected_row = row.iloc[[selected_row_id]]
        results = research.get_close(MHO_df, MHO_d2v_df, selected_row, weights, MHO)[columns_extended]
        return generate_KNN_results_table(results[results[FILTER_COL[MHO]] != int(visit_id)]), False, ""


@app.callback(Output('loading2', 'children'),
              [Input('filename', 'value'), Input('slider-eps', 'value')], [State('tabs', 'value')])
def file_change(filename, slider_eps, tab):
    """switching files"""
    global changes_work_df, MHO, current_file, work_df_numeric, save_file_lock, EPS, clusters, MHO_df, MHO_d2v_df
    if filename != 'Select a file...' and filename != current_file and EPS == slider_eps:
        while not save_file_lock:
            time.sleep(0.1)
            save_file_lock = False
        current_file = filename
        xl = pd.ExcelFile(UPLOAD_DIRECTORY + filename)
        changes_work_df = xl.parse(xl.sheet_names[0])
        file_name = filename.replace("new_", "").replace("finished_", "")
        split = file_name.split('_')
        MHO = split[0]
        fileupload.MHO = MHO
        temp_file_name = split[0] + '_' + split[1] + '_' + split[2]
        if MHO == 'klalit':
            MHO_df = df_klalit
            MHO_d2v_df = df_numeric_klalit
        elif MHO == 'meohedet':
            MHO_df = df_meohedt
            MHO_d2v_df = df_numeric_meohedt
        elif MHO == 'macabi':
            MHO_df = df_macabi
            MHO_d2v_df = df_numeric_macabi
        work_df_numeric = add_d2v_columns(changes_work_df, MHO, temp_file_name)
        save_file_lock = True
        create_clusters_aux()
        if tab == 'tab-clusters':
            clusters_display(clusters)

    elif EPS != slider_eps and filename != 'Select a file...' and tab == 'tab-clusters':
        EPS = slider_eps
        create_clusters_aux()
        clusters_display(clusters)
    return ""


def clusters_display(clusters_arr):
    """ showing the table of info on all the clusters found sorted by heuristics"""
    array = []
    for cluster in clusters_arr:
        row = str(cluster.base['קוד ערעור'].get_values()[0]) + "," + \
              str(cluster.base['מחלקה'].get_values()[0]) + "," + str(
            cluster.base['תאור ערעור'].get_values()[0]) + "\n" + \
              "  מספר שורות: " + str(cluster.N_rows) + "\n" + \
              "  סכום: " + str(cluster.cash)
        array.append(row)

    temp = pd.Series(array).to_frame()

    return html.Div([
        dash_table.DataTable(
            id='table_clusters',
            data=temp.to_dict('records'),
            columns=[{'id': c, 'name': c} for c in temp.columns],
            n_fixed_rows=1,
            selected_rows=[0],
            row_selectable='single',
            style_as_list_view=True,
            style_cell={'white-space': 'pre', 'textAlign': 'right', 'font-size': '14px'},
            style_header={'display': 'none'},
            style_table={'height': '500px'},
        ), ])


@app.callback(
    [Output('answer_for_all', 'children'),
     Output('table_display_cluster', 'children'),
     Output('key_table', 'children')],
    [Input('table_clusters', "selected_rows")])
def display_current_cluster(selected_row):
    global clusters
    if len(freeze_state_of_work_df.index) <= 0:
        return '', '', ''
    if selected_row is not None and len(selected_row) > 0:
        selected_row_id = selected_row[0]
    else:
        selected_row_id = 0

    work_df_no_answer = freeze_state_of_work_df[freeze_state_of_work_df[REJECT_COL[MHO]].isnull()][
        cols[MHO] + [FILTER_COL[MHO]]].copy()
    temp = work_df_no_answer[cols[MHO] + [FILTER_COL[MHO]]].copy()
    temp = temp[clusters[selected_row_id].rows]
    clusters[selected_row_id].get_close()
    answer_list = list(clusters[selected_row_id].answers)
    answer_df = pd.DataFrame(
        [{'תשובה': a, ' מספר': str(i)} for a, i in zip(answer_list, list(range(len(answer_list))))])
    num_of_answers = 5
    return html.Div(dcc.Dropdown(id='one_answer_dropdown',
                                 options=[{'label': answer_list[i], 'value': answer_list[i]} for i in
                                          range(min(len(answer_list), num_of_answers))],
                                 value='',
                                 style={'width': '60%', 'display': 'inline-block', 'textAlign': 'right',
                                        'margin': 'auto'},
                                 clearable=False
                                 ), ), \
           html.Div(generate_table_dropdown(clusters[selected_row_id], temp), style={'height': '500px'}), \
           html.Div(generate_basic_table(answer_df))


def create_clusters_aux():
    # creating the clusters on the rows that have no answers, using DBSCAN.
    global clusters, freeze_state_of_work_df, EPS
    freeze_state_of_work_df = changes_work_df.copy()
    not_answered_rows = freeze_state_of_work_df[REJECT_COL[MHO]].isnull()
    not_answered_df = freeze_state_of_work_df[not_answered_rows]
    df_one_hot = work_df_numeric[not_answered_rows][cols[MHO]].copy()

    df_one_hot = pd.get_dummies(df_one_hot, columns=catagory_cols[MHO], prefix=['o_h1', 'o_h2', 'o_h3'])
    scaler = MinMaxScaler()
    df_one_hot[money_col[MHO]] = scaler.fit_transform(np.array(df_one_hot[money_col[MHO]].values).reshape(-1, 1))
    d2v_1 = df_one_hot[t_cols[MHO][0]].values
    d2v_2 = df_one_hot[t_cols[MHO][1]].values
    d2v_1_ = [np.array(a) for a in d2v_1]
    d2v_2_ = [np.array(a) for a in d2v_2]
    d2v_1_ = np.array(d2v_1_)
    d2v_2_ = np.array(d2v_2_)

    for i in range(50):
        df_one_hot['d2v_1_' + str(i)] = pd.Series(d2v_1_[:, i], index=df_one_hot.index[:len(d2v_1_)])
        df_one_hot['d2v_2_' + str(i)] = pd.Series(d2v_2_[:, i], index=df_one_hot.index[:len(d2v_2_)])
    del df_one_hot[t_cols[MHO][0]]
    del df_one_hot[t_cols[MHO][1]]

    db = DBSCAN(EPS, min_samples=10).fit(df_one_hot)
    labels = db.labels_
    unique_labels = set(labels)
    unique_labels = [a for a in unique_labels if a != -1]
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True

    n_core_arr = np.zeros(len(unique_labels))
    n_border_arr = np.zeros(len(unique_labels))
    scores_arr = np.zeros(len(unique_labels))
    price_arr = np.zeros(len(unique_labels))
    variance_arr = np.zeros(len(unique_labels))

    for i, k in enumerate(unique_labels):
        class_member_mask = (labels == k)
        n_core_arr[i] = sum(class_member_mask & core_samples_mask)
        n_border_arr[i] = sum(class_member_mask & ~core_samples_mask)
        scores_arr[i] = 1
        price_arr[i] = not_answered_df[money_col[MHO]][class_member_mask].sum()
        variance_arr[i] = 1 if not_answered_df[class_member_mask][CODE_COL[MHO]].iloc[0] == HARD_CODE else 0
    # nurmalize each arr
    n_core_arr = normalize(n_core_arr[:, np.newaxis], axis=0).ravel()
    n_border_arr = normalize(n_border_arr[:, np.newaxis], axis=0).ravel()
    scores_arr = normalize(scores_arr[:, np.newaxis], axis=0).ravel()
    price_arr = normalize(price_arr[:, np.newaxis], axis=0).ravel()
    variance_arr = normalize(variance_arr[:, np.newaxis], axis=0).ravel()
    final_score_arr = price_arr / 32 + n_core_arr + scores_arr + n_border_arr / 2 - variance_arr
    sorted_scores, sorted_labels = zip(*sorted(zip(final_score_arr, unique_labels)))

    clusters = list()
    labels = db.labels_

    for label in sorted_labels:
        clusters.append(cluster(labels, db.core_sample_indices_, label, not_answered_df, MHO_d2v_df))
    clusters.reverse()


@app.callback(
    Output('table_chose_cluster', 'children'),
    [Input('save-btn', 'n_clicks'), Input('update-all-btn', 'n_clicks')])
def clusters_create(clicks, uniform_clicks):
    global clusters, save_clicks, cluster_lock, EPS
    if (clicks is not None and clicks > save_clicks) or (uniform_clicks is not None):
        save_clicks = clicks
        while not cluster_lock:
            time.sleep(0.1)
        cluster_lock = False
    return clusters_display(clusters)


uniform_answer_clicks = 0
not_uniform_clicks = 0


@app.callback(
    Output('answer-label', 'children'),
    [Input('save-btn', 'n_clicks'), Input('update-all-btn', 'n_clicks')],
    [State('current-cluster-table', 'derived_virtual_data'),
     State('table_clusters', 'seleced_row'),
     State('one_answer_dropdown', 'value')])
def save_answers(clicks, uniform_clicks, rows, selected_row, uniform_answer):
    """saving all the rows that got answers after the work on the current cluster"""
    global clusters, cluster_lock, save_file_lock, not_uniform_clicks, uniform_answer_clicks
    save_file_lock = False
    if selected_row is not None and len(selected_row) > 0:
        selected_row_id = selected_row[0]
    else:
        selected_row_id = 0

    if clicks is not None and clicks > not_uniform_clicks:
        not_uniform_clicks = clicks
        cluster_not_answered_indexes = [i for i, e in enumerate(clusters[selected_row_id].rows) if e]
        not_answered_index = [i for i, e in enumerate(freeze_state_of_work_df[REJECT_COL[MHO]].isnull()) if e]
        for row, i in zip(rows, cluster_not_answered_indexes):
            if row['answer'] != '':
                changes_work_df[REJECT_COL[MHO]].iloc[not_answered_index[i]] = row['answer']
                changes_work_df[CHOISE_COL[MHO]].iloc[not_answered_index[i]] = 'נדחה'
                clusters[selected_row_id].update(i, row[money_col[MHO]])
        if clusters[selected_row_id].isEmpty():
            clusters.remove(clusters[selected_row_id])
    elif uniform_clicks is not None and uniform_clicks > uniform_answer_clicks:
        uniform_answer_clicks = uniform_clicks
        cluster_not_answered_indexes = [i for i, e in enumerate(clusters[selected_row_id].rows) if e]
        not_answered_index = [i for i, e in enumerate(freeze_state_of_work_df[REJECT_COL[MHO]].isnull()) if e]
        for row, i in zip(rows, cluster_not_answered_indexes):
            if uniform_answer != '':
                changes_work_df[REJECT_COL[MHO]].iloc[not_answered_index[i]] = uniform_answer
                changes_work_df[CHOISE_COL[MHO]].iloc[not_answered_index[i]] = 'נדחה'
        clusters.remove(clusters[selected_row_id])

    cluster_lock = True
    save_file_lock = True


def generate_table_dropdown(cluster, dataframe):
    """ displaying the answers table of the current cluster"""
    dataframe['answer'] = ''
    return html.Div([
        dash_table.DataTable(
            id='current-cluster-table',
            data=dataframe.to_dict('rows'),
            columns=[{'id': c, 'name': c, 'presentation': 'dropdown'} if c == 'answer' else {'id': c, 'name': c} for c
                     in dataframe.columns],
            editable=True,
            column_static_dropdown=[
                {'id': 'answer',
                 'dropdown': [
                     {'label': str(i), 'value': i}
                     for i in range(min(len(list(cluster.answers)), 5))],
                 'style': {'text-overflow': 'inherit'}}],
            style_cell={
                'minWidth': '0px', 'maxWidth': '100px', 'whiteSpace': 'normal', 'text-overflow': 'inherit',
                'textAlign': 'center', 'font-family': 'Arial', 'font-size': '12px'},
            style_header={'fontWeight': 'bold'},
            css=[{
                'selector': '.dash-cell div.dash-cell-value',
                'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;', }],
            style_table={
                'maxHeight': '300', 'height': '300px',
                'overflowY': 'scroll',
            }, ), ])


if __name__ == '__main__':
    app.run_server(debug=True)
