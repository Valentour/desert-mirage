#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
desert_mirage_lib.py:
This file provides general functions and classes for the desert mirage module.
Copyright (c) Jan 2017 Nicholas Valentour
"""

from sys import exit
import os
import json as json
import numpy as np
import pandas as pd
from functools import partial
from glob import glob
import math
import heapq
import random
from numpy import random
import string
from datetime import timedelta as td
from datetime import date
import re

# JSON utilities.
def json_config(jfile, jobj_hook=None, jwrite_obj=None, jappend=None):
    """
    Simple interface to json library functions. Reads JSON data into object
    dictionary or appends json data to existing file.
    See the json library documentation for  more info.
    `json <https://docs.python.org/3/library/json.html>`_

    Parameters
    ----------
    jfile : str
        json file path.
    jobj_hook : function (default: None)
        Decoder. If None, decodes to dict.
    jwrite_obj : obj (default: None)
        Obj to write to existing json file ``jfile``. 
        Evaluated before ``jappend``.
    jappend : obj (default: None)
        New data to append to existing json file ``jfile``.
    """
    # write if file does not exist.
    if jwrite_obj is not None:
        # Write `jwrite_obj` if file does not exist.
        if not any([os.path.isfile(jfile),
                    os.path.isfile(os.path.abspath(jfile)),
                    jwrite_obj]):
            print('writing `jwrite_obj` to new json `jfile`.')
            with open(jfile, 'w') as f:
                json.dump(jwrite_obj, f, sort_keys=True, ensure_ascii=False)
        else:
            print('No json in path provided.')
        return
    if jappend is not None:
        with open(jfile, 'r+') as f:
            json_dict = json.load(f, object_hook=None)
            json_dict.update(jappend)
            f.seek(0)
            f.truncate()  # todo: Improve to only truncate if needed.
            # print(len(f.readlines()))
            json.dump(json_dict, f, sort_keys=True, indent=4)
            f.close()
        return
    with open(jfile) as f:
        if jobj_hook is not None:
            return json.load(f, object_hook=jobj_hook)
        return json.load(f)

class JsonDict(object):
    """
    Contains object hook for ``json_config`` for reading object in as dictionary.
    """
    def __init__(self, json_obj):
        self.__dict__ = json_obj
    
    def items_(self):
        for key in self.__dict__:
            setattr(self, key, self.__dict__[key])
    
    def __repr__(self):
        return "<JsonDict: %s>"%self.__dict__

class DictAsObject(object):
    """
    Converts a dictionary to an object with items as attributes.
    """
    
    def __init__(self, dictionary):
        for key in dictionary:
            if not key.startswith('__'):
                setattr(self, key, dictionary[key])
    
    def __repr__(self):
        return "<DictAsObject: %s>"%self.__dict__


def file_to_string_w_replace(afile, old, new=', ', occurrence=None):
    """
    Notes
    -----
    Adopted and/or modified from reference(s):
    http://stackoverflow.com/questions/2556108/
    """
    with open(afile, 'r+') as afl:
        fs = afl.read().replace('\n', '')
    if occurrence is not None:
        news = fs.rsplit(old, occurrence)
        return new.join(news)
    news = fs.rsplit(old)
    return new.join(news)


# Pandas utilities.
def ungroupby(df, idx_label):
    # ungroup the pandas groupby object.
    idx_list = df[idx_label].values.tolist()
    new_range = np.arange(idx_list)
    return df.reset_index(drop=True).reindex(new_range).fillna(method='ffill')

def example_col_math(df, col1, col2, col3, new_col):
    darray = [df[col1].values[0]]
    for i in range(1, len(df.index)):
        darray.append(darray[i-1]*df[col2].values[i]+df[col3].values[i])
    df[new_col] = darray
    return df

def example_df(nrows, ncols, inc_id_col=None, bool_cols=None,
               inc_date=None, rseed=129):
    """Create a simple df for sandbox testing or answering questions.
    Parameters
    ----------
    nrows: int
        number of rows.
    ncols: int
        number of columns.
    inc_id_col: bool (default: False)
        Include random 'ID' column.
    bool_cols: bool (default: False)
        Include random boolean column.
    inc_date: bool (default: False)
        Include date column or random dates between 01/15/2015 - 12/15/2015.
    rseed: int
        RNG seed number.
    
    Returns
    -------
    pd.DataFrame : pd.DataFrame
        Shape nrow x ncols with column names as an alphabetic sequence.
    """
    random.seed(rseed)
    # Create alphabetic list in uppercase.
    alphabet_cols = list(string.ascii_uppercase)[:ncols]
    df = pd.DataFrame(random.randint(nrows,
                                     size=(nrows, ncols)),
                      columns=alphabet_cols)
    
    # Create ID-like column A.
    if inc_id_col:
        df['A'] = [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 7, 7]
        df['A'] = 9990+df.A.values
        df = df.rename(columns={'A': 'ID'})
    
    # Populate boolean values for the ncol-1 right-most columns.
    if bool_cols:
        df[df.columns[-ncols+1:]] = random.randint(2, nrows,
                                                   len(df.columns[-ncols+1:]))
        df.sort_values(by='ID', inplace=True)
        df.reset_index(inplace=True, drop=True)
    
    # Create a Date column cycling from 1/15/2015 to 12/15/2015.
    if inc_date:
        df['Date'] = np.tile([td(days=30*i)+date(2015, 1, 15)\
                              for i in range(0, 12)], np.round(nrows/4))
        df['Date'] = pd.to_datetime(df['Date'])
        return df

def eliminate_invalids(df, cols):
    """Eliminate invalid data in ``cols`` of ``df``."""
    numdf = df.drop(cols, axis=1).join(df[cols].apply(pd.to_numeric,
                                                      errors='coerce'))
    numdf = numdf[~numdf[cols].isnull().apply(np.any, axis=1)]
    return numdf

def df_cols_by_type(df):
    """Returns list of ``df`` col names for non-numerics, numerics, numeric_stats."""
    all_cols = df.columns.values.tolist()
    non_numeric = [x for x in all_cols if
                   not (df[x].dtype == np.float64 or df[x].dtype == np.int64)]
    numeric = [x for x in all_cols if x not in non_numeric]
    return {'numeric': numeric, 'non_numeric': non_numeric}

def partial_convert_only_numerics(df):
    """Convert ``df`` numeric cols and try to coerce any errors encountered."""
    col_dict = df_cols_by_type(df)
    partial_convert = partial(pd.to_numeric, errors='coerce')
    df[col_dict['numeric']].apply(partial_convert)
    return df

# Useful one-liners.
# df.select_dtypes(include=['bool'])
# list(df.select_dtypes(include=['bool']).columns)

def left_merge_groupby_aggregrate(df, on_col, agg_col, func):
    def map_func():
        if func in 'count':
            return df.groupby([on_col]).count()
        if func in 'mean':
            return df.groupby([on_col]).mean()
        if func in 'std':
            return df.groupby([on_col]).std()
    
    agg_frame = map_func()
    agg_frame = agg_frame.iloc[:, 1].values
    grouped = pd.DataFrame({agg_col: agg_frame,
                            on_col: sorted(df[on_col].unique())})
    return pd.merge(df, grouped, how='left', left_on=on_col, right_on=on_col)

def gen_flatten(seq):
    """
    Generator to flatten values of irregular nested sequences.

    Parameters
    ----------
    seq: array-like

    Notes
    -------
    Adopted and/or modified from reference(s):
    http://stackoverflow.com/questions/36840438/
    http://stackoverflow.com/questions/952914/

    Example
    -------
    tuple(flatten(seq))
    list(flatten(seq))
    """
    for el in seq:
        try:
            yield from np.ndarray.flatten(el)
        except TypeError:
            yield el

def data_to_row_bins(ar, npts=1):
    """
    Splits an array ``ar`` into two arrays, 'X' and 'y' using np.strides,
    where each row contains a bin of data with ``npts``.
    Modified from http://glowingpython.blogspot.com/

    Parameters
    ----------
    ar: np.array
        1-D time series.
    npts: int
        Number of points to include in each row of output matrix.
    Returns
    -------
    X: np.array
        m x npts array where each row contains a bin of data with 'npts'.
    y: np.array
        The target values for each row of X.
    """
    ashape = ar.shape[:-1]+(ar.shape[-1]-npts+1, npts)
    astrides = ar.strides+(ar.strides[-1],)
    X = np.lib.stride_tricks.as_strided(ar, shape=ashape, strides=astrides)
    y = np.array([X[i+npts][-1] for i in range(len(X)-npts)])
    return X[:-npts], y

def df_info(df):
    print('Shape: \n', df.shape)
    print('Column Names: \n', df.columns.values.tolist())
    print('Data Types: \n', df.dtypes)
    print('DF Head:\n', df.head(2))
    print('DF Tail:\n', df.tail(2))
    return

def map_series1_index_to_kth_largest_in_series(df, c1, c2, new_col_str):
    """
    Returns list of kth indexes in ``c2`` where the kth value of ``c2`` is
    greater than the *ith* largest value in ``c1``.
    The criteria uses the following logic:
    ``(c2[k] >= c1[i] and c2[k+1] < c1[i])``, for all ``i`` in ``c1``.

    Parameters
    ----------
    df: pd.DataFrame
        input df
    c1: str
        First column name.
    c2: str
        Second column name.
    new_col_str: str
        New column name.
    """
    mapd = None
    try:
        A = df.c1.values
        B = df.c2.values
        mapd = [k for k in range(0, len(B)-1) for a in A if
                (B[k] <= a) & (B[k+1] > a) or (a > max(B))]
    except AttributeError:
        A = df.c1.values.tolist()
        B = df.c2.values.tolist()
        mapd = [k for k in range(0, len(B)-1) for a in A if
                (B[k] <= a) & (B[k+1] > a) or (a > max(B))]
    if mapd is not None:
        df[new_col_str] = mapd
    return df

# Simple stats/math
def dec_round(num, dprec=4, rnd='down', rto_zero=False):
    """
    Round up/down numeric ``num`` at specified decimal ``dprec``.

    Parameters
    ----------
    num: float
    dprec: int
        Decimal position for truncation.
    rnd: str (default: 'down')
        Set as 'up' or 'down' to return a rounded-up or rounded-down value.
    rto_zero: bool (default: False)
        Use a *round-towards-zero* method, e.g., ``floor(-3.5) == -3``.

    Returns
    ----------
    float (default: rounded-up)
    """
    dprec = 10**dprec
    if rnd == 'up' or (rnd == 'down' and rto_zero and num < 0.):
        return np.ceil(num*dprec)/dprec
    elif rnd == 'down' or (rnd == 'up' and rto_zero and num < 0.):
        return np.floor(num*dprec)/dprec
    return np.round(num, dprec)

def euclidean_distance(x1, y1, x2, y2, prec_calc=2, prec_out=2):
    """
    Calculates euclidean distance between a pair of cartesian points.
    Includes parameter to apply a cutoff precision.

    Parameters
    ----------
    x1, y1: float coordinates of first point.
    x2, y2: float coordinates of second point.
    prec_calc: int (default: 3)
        decimal precision for calculations.
    prec_out: int (default: 2)
        output decimal precision.
    """
    x1, y1 = float(x1), float(y1)
    x2, y2 = float(x2), float(y2)
    x_off = dec_round(math.fabs(x1-x2), prec_calc, 'down')
    y_off = dec_round(math.fabs(y1-y2), prec_calc, 'down')
    dist = math.sqrt((x_off**2)+(y_off**2))
    return dec_round(dist, prec_out, 'down', True)

def nth_largest(n, iter_list):
    """``O(nlogn)`` time if ``n`` is median. 
    Better if largest or smallest.
    
    Notes
    -----
    Adopted and/or modified from reference(s):
    FogleBird on stackoverflow.com/questions/1034846/
    """
    length = len(iter_list)
    if n >= length:
        return heapq.nlargest(length, iter_list)[-1]
    return heapq.nlargest(n, iter_list)[-1]

# OS utilities
def prevent_file_collision(fullpath, cnt=None):
    f_dir, nameext = os.path.split(fullpath)
    name, ext = os.path.splitext(nameext)
    if not cnt:
        cnt = 1
    new_path = fullpath
    while os.path.isfile(new_path):
        cnt += 1
        new_name = name+'({}){}'.format(cnt, ext)
        new_path = os.path.join(f_dir, new_name)
        print('Export file collision. Renaming file.')
        print('Export file is now: ', os.path.basename(new_path))
    return new_path

# Collecting files in OS path
def dict_of_files_in_path(fpath, string1, string2):
    """
    Recursive search for all '.txt' files in ``fpath`` and split 
    into two lists if file base name contains ``string1`` or ``string2``.
    """
    string1_list = list()
    string2_list = list()
    for file in glob(os.path.join(fpath, '**/*.txt'),
                     recursive=True):
        file_base = os.path.basename(file)
        # Check if 'string1' in basename.
        if string1 in file_base:
            string1_list.append(file)
        # Check if 'string2' in basename.
        elif string2 in file_base:
            string2_list.append(file)
    return {'{}'.format(string1): string1_list,
            '{}'.format(string2): string2_list}

# Settings
np.set_printoptions(edgeitems=3, infstr='inf', linewidth=78,
                    nanstr='nan', precision=4, suppress=False,
                    threshold=50, formatter=None)
pd.set_option('expand_frame_repr', True, 'max_seq_items', 40,
              'max_colwidth', 80, 'precision', 4, 'display.float_format',
              lambda x: '%.4f'%x)

if __name__ == '__main__':
    exit(0)
