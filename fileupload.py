import base64
import datetime
from app import app
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import re
import os
import flask

now = datetime.datetime.now()
year = now.year
UPLOAD_DIRECTORY = 'preprocessed\\'
PROCESS_DIRECTORY = 'process\\'
DOWNLOAD_DIRECTORY = 'preprocessed/'

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

if not os.path.exists(PROCESS_DIRECTORY):
    os.makedirs(PROCESS_DIRECTORY)

if not os.path.exists(DOWNLOAD_DIRECTORY):
    os.makedirs(DOWNLOAD_DIRECTORY)


def build_download_button(uri):
    """Generates a download button for the resource"""
    button = html.Form(
        action=uri,
        method="get",
        children=[
            html.Button(
                className="button",
                type="submit",
                children=[
                    "download"
                ]
            )
        ]
    )
    return button


@app.callback(
    Output("download-area", "children"),
    [
        Input('file-to-download', 'value')
    ]
)
def show_download_button(file_to_download):
    if file_to_download == 'file to download...':
        return
    # turn text area content into file
    print(file_to_download)
    filename = f"preprocessed/{file_to_download}"
    path = f"/{filename}"
    uri = path
    return [build_download_button(uri)]


@app.server.route('/preprocessed/<path:path>')
def serve_static(path):
    root_dir = os.getcwd()
    return flask.send_from_directory(
        os.path.join(root_dir, 'preprocessed'), path, as_attachment=True
    )


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(re.sub("_\d\d-\d\d-\d\d\d\d", '', filename))
    return files


def files_to_download():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(DOWNLOAD_DIRECTORY):
        path = os.path.join(DOWNLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


layout = html.Div([
    html.Details([
        html.Summary('העלאת קובץ:'),
        html.Label('קובץ גמור או חדש?'),
        dcc.Dropdown(
            id='type',
            options=[
                {'label': 'חדש', 'value': 'new'},
                {'label': 'גמור', 'value': 'finished'},
            ],
            value='new',
            style={'width': '50%'},
            clearable=False
        ),
        html.Label('בחירת קופת חולים:'),
        dcc.Dropdown(
            id='Org',
            options=[
                {'label': 'כללית', 'value': 'klalit'},
                {'label': 'מאוחדת', 'value': 'meohedet'},
                {'label': 'מכבי', 'value': 'macabi'},
            ],
            value='klalit',
            style={'width': '50%'},
            clearable=False
        ),
        html.Label('בחירת חודש:'),
        dcc.Dropdown(
            id='month',
            options=[
                {'label': '01', 'value': '01'},
                {'label': '02', 'value': '02'},
                {'label': '03', 'value': '03'},
                {'label': '04', 'value': '04'},
                {'label': '05', 'value': '05'},
                {'label': '06', 'value': '06'},
                {'label': '07', 'value': '07'},
                {'label': '08', 'value': '08'},
                {'label': '09', 'value': '09'},
                {'label': '10', 'value': '10'},
                {'label': '11', 'value': '11'},
                {'label': '12', 'value': '12'},
            ],
            value='01',
            clearable=False,
            style={'width': '50%'}

        ),

        html.Label('בחירת שנה:'),
        dcc.Dropdown(
            id='year',
            options=[
                {'label': year - 2, 'value': year - 2},
                {'label': year - 1, 'value': year - 1},
                {'label': year, 'value': year},

            ],
            value=year,
            clearable=False,
            style={'width': '50%'},

        ),

        html.H2("העלאה:"),
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                ' גרור קובץ או ',
                html.A('בחר קובץ')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },

            multiple=True,
        ),

        dcc.ConfirmDialog(
            id='confirm',
        ),
    ]),

    html.Details([
        html.Summary('מחיקת קובץ:'),
        html.H2('רשימת הקבצים'),
        html.Div(id='file-list'),
        html.Div(id='junk'),

        html.Div([dcc.Checklist(
            id='to-delete',
            options=[{'label': filenameop, 'value': filenameop} for filenameop in uploaded_files()],
            values=[]),

            html.Div(html.Button('מחק', id='del-btn', n_clicks_timestamp=0)),
            html.Div(id='files-removed')
        ]),
    ]),

    html.Details([
        html.Summary('הורדת קובץ:'),
        html.Div(
            className="section",
            children=[
                dcc.Dropdown(
                    id='file-to-download',
                    options=[{'label': filenameop, 'value': filenameop} for filenameop in files_to_download()],
                    placeholder='file to download...',
                    style={'width': '300px'}
                ),
                html.Div(
                    id="download-area",
                    className="block",
                    children=[]
                )
            ]
        )
    ]),
]
    , style={'direction': 'rtl'}

)


@app.callback(
    Output('files-removed', 'children'),
    [Input('del-btn', 'n_clicks')],
    [State('to-delete', 'values')]
)
def remove_files(clicks, files_to_delete):
    if clicks is not None:
        if files_to_delete is not None:
            for file in files_to_delete:
                path = os.path.join(UPLOAD_DIRECTORY, file)
                if os.path.exists(path):
                    os.remove(path)


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


@app.callback(
    Output('junk', 'children'),
    [Input('confirm', 'submit_n_clicks')],
    [State('upload-data', 'contents'),
     State('Org', 'value'), State('month', 'value'), State('year', 'value'), State('type', 'value')]
)
def update_file(agree_click, uploaded_file_contents, org, month, year, type):
    if (agree_click):
        for filename in os.listdir(UPLOAD_DIRECTORY):
            path = os.path.join(UPLOAD_DIRECTORY, filename)
            if os.path.isfile(path):
                newfilename = str(type) + '_' + str(org) + '_' + str(month) + '_' + str(year) + '.' + \
                              filename.split(".")[-1]

                if newfilename == re.sub("_\d\d-\d\d-\d\d\d\d", '', filename):
                    print(uploaded_file_contents[0])
                    save_file(filename, uploaded_file_contents[0])

    return ""


@app.callback(
    Output('file-list', 'children'),
    [Input('upload-data', 'filename'), Input('upload-data', 'contents')],
    [State('Org', 'value'), State('month', 'value'), State('year', 'value'), State('type', 'value')]
)
def update_output(uploaded_filenames, uploaded_file_contents, org, month, year, type):
    """Save uploaded files and regenerate the file list."""

    if uploaded_filenames is not None and uploaded_file_contents is not None:
        for name, data in zip(uploaded_filenames, uploaded_file_contents):
            newfilename = str(type) + '_' + str(org) + '_' + str(month) + '_' + str(
                year) + '_' + "{date:%d-%m-%Y}".format(date=datetime.datetime.now()) + '.' + name.split(".")[-1]
            if (re.sub("_\d\d-\d\d-\d\d\d\d", '', newfilename) not in uploaded_files()):
                save_file(newfilename, data)


@app.callback([Output('confirm', 'displayed'), Output('confirm', 'message')],
              [Input('upload-data', 'filename')],
              [State('Org', 'value'), State('month', 'value'), State('year', 'value'), State('type', 'value')])
def display_confirm(filename, org, month, year, type):
    "displays message when file exists"
    if (filename is not None):
        filename = filename[0]
        newfilename = str(type) + '_' + str(org) + '_' + str(month) + '_' + str(year) + '.' + filename.split(".")[-1]
        if (newfilename in uploaded_files()):
            return True, "האם ברצונך להעלות את הקובץ:  " + newfilename + "    ?"

    return False, newfilename
