# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler
from settings import *


src = np.zeros(50)
src_str = ""


def get_column_from_d2v_file(i, folder, filename, idx=[-1]):
    temp_filename = filename
    temp_filename = temp_filename.replace('.xlsx','')
    t_cols = pd.read_csv(folder + "/" + temp_filename + "_t_cols_"+str(i)+".csv", low_memory=False, header=None)
    if -1 not in idx:
        t_cols = t_cols.iloc[idx]
    res = list()
    for j in range(len(t_cols.index)):
        vec = list()
        for k in range(len(t_cols.columns)):
            vec.append(t_cols.iloc[j][k])
        res.append(np.array(vec))
    return res


def replace_emptys(cell):
    if isinstance(cell, float) or cell == '' or cell is None or pd.isnull(cell):
        return u'ריק'
    return cell


def d2v_distance(cell):
    diff = cell - src
    x = np.sqrt(np.sum(diff ** 2))
    return x


def give_distance(cell):
    if src_str == cell:
        return 0
    else:
        return 1


def get_close(df, df2, row, weights, MHO):
    global src, src_str
    # print(row[money_col[MHO]].values[0])
    #if row[money_col[MHO]].values[0] != 0:
    #    df = df[df[money_col[MHO]] != 0]
     #   df2 = df2[df2[money_col[MHO]] != 0]

    df_score = pd.DataFrame()
    for col in t_cols[MHO]:
        src = (row[col].values)[0]
        if weights[cols_index[MHO][col]] != 0:
            df_score[col] = df2[col].apply(d2v_distance)

    for col in cols[MHO]:
        if col not in t_cols[MHO]:
            src_str = (row[col].values)[0]
            if weights[cols_index[MHO][col]] != 0:
                df_score[col] = df2[col].apply(give_distance)



    neigh = NearestNeighbors(n_neighbors=10)
    scaler = MinMaxScaler()
    df_score[df_score.columns] = scaler.fit_transform(df_score[df_score.columns])
    for col in cols[MHO]:
        col_weight = weights[cols_index[MHO][col]]
        if col_weight != 0 :
            df_score[col] = df_score[col].apply(lambda x: x * (1/col_weight))
    neigh.fit(df_score)
    res = neigh.kneighbors(np.zeros(sum(a > 0 for a in weights)).reshape(1, -1))
    return df.loc[res[1][0]]


