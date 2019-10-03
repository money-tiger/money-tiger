MHO_dict = {'klalit':'כללית',
             'meohedet':'מאוחדת',
             'macabi':'מכבי',
             }


cols = {'klalit': ['סכום ערעור', 'מחלקה', 'קוד שירות','תאור שירות', 'קוד ערעור', 'תאור ערעור'],
        'meohedet': [], 'macabi': []}

money_col = {'klalit': 'סכום ערעור','meohedet': '', 'macabi': ''}

VISIT_ID_COL_NAME = {'klalit':'מספר ביקור/אשפוז',
                         'meohedet':'',
                         'macabi':'',
                         }
ID_COL_NAME = {'klalit':'מספר ת.ז. פיקטיבי',
                         'meohedet':'',
                         'macabi':'',
                         }
FILTER_COL = ID_COL_NAME
REJECT_COL = {'klalit':'סיבת דחייה/הערות',
              'meohedet': '',
              'macabi': '',
              }
CHOISE_COL = {'klalit':'אושר/נדחה/חלקי',
              'meohedet': '',
              'macabi': '',
              }

cols_index = {'klalit':{
                        'סכום ערעור':0,
                        'מחלקה':1,
                        'קוד שירות':2,
                        'תאור שירות':3,
                        'קוד ערעור':4,
                        'תאור ערעור':5
                        },
             'meohedet':'',
             'macabi':'',
             }
t_cols = {'klalit':['תאור שירות', 'תאור ערעור'],
             'meohedet':[],
             'macabi':[],
             }

catagory_cols = {'klalit':['קוד שירות', 'מחלקה', 'קוד ערעור'],
                 'meohedet':[],
                 'macabi':[],}

CODE_COL = {'klalit':'קוד ערעור','macabi':'','meohedet':''}
HARD_CODE = 'H180'