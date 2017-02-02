#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
desert_mirage_gui.py:
This module is the GUI for the Desert Mirage Project.
Copyright (c) Jan 2017 Nicholas Valentour
"""

from os import path, getcwd
import desert_mirage_lib as dem
from tkinter import *
from tkinter import ttk, filedialog
import json
from glob import glob

def select_json():
    selection = filedialog.askopenfilename(initialdir=getcwd(),
                                           title='Select project json file')
    _jsonVar.set(selection)
    print('Selected json file: {}'.format(_jsonVar.get()))

def select_seed():
    selection = filedialog.askopenfilename(initialdir=getcwd(),
                                           title='Select IVS seed file')
    _seedVar.set(selection)
    print('Selected seed file: {}'.format(_seedVar.get()))

def select_folder():
    from tkinter import filedialog
    
    selected = filedialog.askdirectory(initialdir=getcwd(),
                                       title='Select IVS Data Folder')
    _folderVar.set(selected)
    print('Selected data folder: {}'.format(_folderVar.get()))

def select_file():
    selected = filedialog.askopenfilename(initialdir=getcwd(),
                                          title='Select IVS Data File')
    _fileVar.set(selected)
    print('Selected data file: {}'.format(_fileVar.get()))

def select_export():
    selected = filedialog.askdirectory(initialdir=getcwd(),
                                       title='Select Export Tables Folder')
    _tableFolderVar.set(selected)
    print('Selected export table folder: {}'.format(_tableFolderVar.get()))

def reload_json_data():
    def toggle_gui_data(jdict, toggled):
        global _root
        if toggled:
            _jsonVar.set(jdict.GUI.PreviousJSON)
            _seedVar.set(jdict.GUI.SeedDataCSV)
            _fileVar.set(jdict.GUI.DailyTestFile)
            _folderVar.set(jdict.GUI.DailyTestFolder)
            _surveyVar.set(jdict.GUI.SurveyType)
            _measureVar.set(jdict.GUI.MeasurementSystem)
            _ivsAxisVar.set(jdict.GUI.MajorAxis)
            _ivsResponse.set(jdict.GUI.ResponseChannel)
            _sensorIDVar.set(jdict.GUI.SingleCoilIDs)
            _backgroundVar.set(jdict.GUI.Background)
            _cableshakeVar.set(jdict.GUI.CableShake)
            _dynamicVar.set(jdict.GUI.DynamicResponse)
            _static1Var.set(jdict.GUI.Static1)
            _static2Var.set(jdict.GUI.Static2)
            _static3Var.set(jdict.GUI.Static3)
            _tableFolderVar.set(jdict.GUI.ExportFolder)
            return
        _jsonVar.set("")
        _seedVar.set("")
        _fileVar.set("")
        _folderVar.set("")
        _surveyVar.set(0)
        _measureVar.set(0)
        _ivsAxisVar.set(0)
        _ivsResponse.set("")
        _sensorIDVar.set("")
        _backgroundVar.set("")
        _cableshakeVar.set("")
        _dynamicVar.set("")
        _static1Var.set("")
        _static2Var.set("")
        _static3Var.set("")
        _tableFolderVar.set("")
        return
    
    # Search local directory for json file ending with 'config.json'.
    local_glob_list = glob('*config.json', recursive=False)
    # Exit with error code 2 if no json file exists.
    if not local_glob_list:
        print("No json found in current working directory.")
        exit(2)
    local_json_file = local_glob_list[0]
    # If multiple json files exist. Select the largest json file.
    if len(local_glob_list) > 1:
        print("multiple json files in working directory.")
        for i in local_glob_list:
            if path.getsize(i) > path.getsize(local_json_file):
                local_json_file = i
        print('Using largest json: {}'.format(path.basename(local_json_file)))
    json_dict = dem.json_config(local_json_file, jobj_hook=dem.JsonDict)
    try:
        if 'GUI' in json_dict.__dict__.keys():
            toggle_gui_data(jdict=json_dict, toggled=_reloadVar.get())
    except AttributeError:
        print('Reload failed. Check json or try proceeding manually.')
        pass
    return

def list_args_as_strings(*args):
    alist = []
    for arg in args:
        alist.append(str(arg.get()))
    return alist

def commit():
    global _root
    global _commitpressed
    _commitpressed = True
    save_form_data()
    _root.destroy()

def save_form_data():
    """
    Updates the json with the user's current selections.
    """
    global _root
    main_dict = {}
    path_labels = ['PreviousJSON', 'SeedDataCSV', 'DailyTestFolder',
                   'DailyTestFile', 'SurveyType', 'MeasurementSystem',
                   'MajorAxis', 'ResponseChannel', 'SingleCoilIDs',
                   'Background', 'CableShake', 'DynamicResponse',
                   'Static1', 'Static2', 'Static3','ExportFolder']
    path_vars = [str(i.get()) for i in
                 [_jsonVar, _seedVar, _folderVar, _fileVar, _surveyVar,
                  _measureVar, _ivsAxisVar, _ivsResponse, _sensorIDVar,
                  _backgroundVar, _cableshakeVar, _dynamicVar, _static1Var,
                  _static2Var, _static3Var, _tableFolderVar]]
    main_dict.update(dict(zip(path_labels, path_vars)))
    
    if not main_dict['PreviousJSON'].endswith('config.json', ):
        print('Invalid json. Name must end in *config.json.')
        
        pnew = path.abspath('new_config.json')
        main_dict['PreviousJSON'] = dem.prevent_file_collision(pnew, cnt=0)
        print('Form data written to default: {}.'.format(path.basename(pnew)))
    
    data_dict = {"GUI": main_dict}
    
    if not path.isfile(main_dict['PreviousJSON']):
        with open(main_dict['PreviousJSON'], 'w') as f:
            json.dump(data_dict, f, sort_keys=True, indent=4)
        return
    
    with open(main_dict['PreviousJSON'], 'r+') as f:
        data = json.load(f)
        data.update(data_dict)
        num_lines = len(f.readlines())
        f.seek(0)
        f.truncate(num_lines)
        json.dump(data, f, sort_keys=True, indent=4)
    return

def run_gui(trig=False):
    if not trig:
        return False
    global _root
    _root.mainloop()
    global user_json
    user_json = _jsonVar.get()
    print('GUI completed.')
    return

user_json = None  # var called by external scripts. Updated by run_gui.
_commitpressed = False
# '#FFD27F' blue
_ibt_bg1 = '#FFD27F'  # light orange
_abt_bg2 = '#7FACFF'  # light blue
_abt_bg2b = '#005000' # dark green
_fg1 = 'black'
_frame_bg1 = '#f8f1e7'  # Cream
_frame_bg2 = '#f8f1e7'  # Cream

# Setup _root frame.
_root = Tk()
_root.title("Desert Mirage v0.0.1")
_root.configure(background='#170a00')
_root.resizable(width=False, height=False)

# Setup top frame.
_frame1 = ttk.Frame(_root, padding="10", relief='sunken')
_frame1.grid(column=0, row=0, sticky='news')
_frame1.grid_columnconfigure(0, weight=1, uniform="Label1Group")
_frame1.grid_columnconfigure(1, weight=1, uniform="Button1Group")
_frame1.grid_columnconfigure(2, weight=1, uniform="Comment1Group")
_frame1.grid_columnconfigure(3, weight=1, uniform="Label2Group")
_frame1.grid_columnconfigure(4, weight=1, uniform="Button2Group")
_frame1.grid_columnconfigure(5, weight=1, uniform="Comment2Group")
_frame1.columnconfigure(0, weight=1)
_frame1.rowconfigure(0, weight=1)

# Config style
s = ttk.Style()
s.configure('.', font=('Verdana', 8), bordercolor=_fg1, foreground=_fg1,
            background=_frame_bg1)
s.configure('Header1.TLabel', font=('Arial', 12, 'bold'), anchor='center')
s.configure('SubHeader1.TLabel', font=('Arial', 9, 'italic'), anchor='center')
s.configure('Header2.TLabel', font=('Arial', 10, 'bold'))
s.configure('Author.TLabel', font=('Arial', 8, 'italic'),
            foreground='black')
s.configure('Comment.TLabel', font=('Verdana', 8, 'italic'))
s.configure('C.TCheckbutton', font=('Verdana', 9),
            foreground=_fg1, background=_frame_bg1)
s.configure('Bot.TFrame', background=_frame_bg2)
s.configure('Bot.TLabel', background=_frame_bg2, font=('Verdana', 8))

# Button keyword arguments
_bkwargs = {'fg': _fg1, 'bg': _ibt_bg1, 'activeforeground': _fg1,
            'activebackground': _abt_bg2, 'cursor': 'hand2'}
_commit_bkwargs = {'fg': _fg1, 'bg': _ibt_bg1, 'activeforeground': _fg1,
                   'activebackground': _abt_bg2b, 'cursor': 'hand2'}
# Title and Header
_row = 0
ttk.Label(_frame1, text='Desert Mirage',
          style='Header1.TLabel').grid(columnspan=6, rowspan=1)
ttk.Label(_frame1,
          text='A python processing module for geophysical system '
               'verification of Geonics EM61-MK2 instruments.',
          style='SubHeader1.TLabel').grid(columnspan=6, row=_row+1)
ttk.Label(_frame1, text='Project Info',
          style='Header2.TLabel').grid(column=0, row=_row+2, sticky=W)

# Json config path widget
_row += 3
_jsonVar = StringVar()
ttk.Label(_frame1, text='Project JSON:').grid(column=0, row=_row, sticky=W)
Button(_frame1, text='JSON', command=select_json,
       **_bkwargs).grid(columnspan=1, column=1, row=_row, sticky=EW)

# Seed path widget
_seedVar = StringVar()
ttk.Label(_frame1, text='IVS Seed CSV:').grid(column=3, row=_row, sticky=W)
Button(_frame1, text='Seed Table', command=select_seed,
       **_bkwargs).grid(columnspan=2, column=4, row=_row, sticky=EW)

# Array radiobutton
_row += 1
_surveyVar = StringVar()
ttk.Label(_frame1, text='Survey Type(s):').grid(column=0, row=_row, sticky=W)
ttk.Radiobutton(_frame1, text=' Single\n/Portable', variable=_surveyVar,
                value='Single').grid(column=1, row=_row, sticky=W)
ttk.Radiobutton(_frame1, text=' Towed\n/Mixed', variable=_surveyVar,
                value='Towed').grid(column=2, row=_row, sticky=NSEW)
# SingleCoilIDs TEntry
_sensorIDVar = StringVar()
ttk.Label(_frame1, text='Single Coil IDs:').grid(column=3, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_sensorIDVar,
          width=8, cursor='ibeam').grid(column=4, row=_row, sticky=W)
ttk.Label(_frame1, text='s1, s2, ..',
          style='Comment.TLabel').grid(column=5, row=_row, sticky=W)

# Major Axis radiobutton
_row += 1
_ivsAxisVar = StringVar()
ttk.Label(_frame1, text='IVS Major Axis:') \
    .grid(column=0, row=_row, sticky=W)
ttk.Radiobutton(_frame1, text='E-W', variable=_ivsAxisVar, value='X'). \
    grid(column=1, row=_row, sticky=W)
ttk.Radiobutton(_frame1, text='N-S', variable=_ivsAxisVar, value='Y') \
    .grid(column=2, row=_row, sticky=W)
# Channel TEntry
_ivsResponse = StringVar()
ttk.Label(_frame1, text='IVS Response Channel:') \
    .grid(column=3, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_ivsResponse,
          width=8, cursor='ibeam').grid(column=4, row=_row, sticky=W)
ttk.Label(_frame1, text='Ex: Ch1',
          style='Comment.TLabel').grid(column=5, row=_row, sticky=W)

# Measurement radiobutton
_row += 1
_measureVar = StringVar()
ttk.Label(_frame1, text='Units:') \
    .grid(column=0, row=_row, sticky=W)
ttk.Radiobutton(_frame1, text='Metric', variable=_measureVar,
                value='Metric').grid(column=1, row=_row, sticky=W)
ttk.Radiobutton(_frame1, text='Imperial', variable=_measureVar,
                value='Imperial').grid(column=2, row=_row, sticky=W)

# Header - Processing Setup
_row += 2
ttk.Label(_frame1, text='Only use lines with test substring:',
          style='TLabel').grid(columnspan=2, row=_row, sticky=W)
# Test Strings TEntries
_row += 1
# ttk.Label(_frame1, text=':').grid(column=0, rowspan=2, row=_row, sticky=NW)
_backgroundVar = StringVar()
_cableshakeVar = StringVar()
_dynamicVar = StringVar()
_static1Var = StringVar()
_static2Var = StringVar()
_static3Var = StringVar()
if not _dynamicVar.get():
    _dynamicVar.set('ivs')
# Test String 1.
ttk.Label(_frame1, text='Background:').grid(column=1, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_backgroundVar,
          width=4, cursor='ibeam').grid(column=2, row=_row, sticky=W)
# Test String 2.
ttk.Label(_frame1, text='Static:').grid(column=3, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_static1Var,
          width=4, cursor='ibeam').grid(column=4, row=_row, sticky=W)
# Test String 3.
_row += 1
ttk.Label(_frame1, text='Cable Shake:').grid(column=1, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_cableshakeVar,
          width=4, cursor='ibeam').grid(column=2, row=_row, sticky=W)
# Test String 4.
ttk.Label(_frame1, text='Static Response:').grid(column=3, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_static2Var,
          width=4, cursor='ibeam').grid(column=4, row=_row, sticky=W)
# Test String 5.
_row += 1
ttk.Label(_frame1, text='Dynamic Response:').grid(column=1, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_dynamicVar,
          width=4, cursor='ibeam').grid(column=2, row=_row, sticky=W)
# Test String 6.
ttk.Label(_frame1, text='Static Recovery:').grid(column=3, row=_row, sticky=W)
ttk.Entry(_frame1, widget="ttk::entry", textvariable=_static3Var,
          width=4, cursor='ibeam').grid(column=4, row=_row, sticky=W)

# Header - Data Source
_row += 3
ttk.Label(_frame1, text='Data Source',
          style='Header2.TLabel').grid(column=0, row=_row, sticky=W)
# Process Data widgets
_row += 1
_fileVar = StringVar()
ttk.Label(_frame1, text='1. Process File:').grid(column=0, row=_row, sticky=W)
Button(_frame1, text='File', command=select_file,
       **_bkwargs).grid(column=1, row=_row, sticky=EW)
ttk.Label(_frame1, text='',
          style='Comment.TLabel').grid(columnspan=3, column=2, row=_row, sticky=W)
_row += 1
_folderVar = StringVar()
ttk.Label(_frame1, text='2. Process Folder:').grid(column=0, row=_row, sticky=W)
Button(_frame1, text='Folder ', command=select_folder,
       **_bkwargs).grid(column=1, row=_row, sticky=EW)
ttk.Label(_frame1, text='Batch all CSVs.',
          style='Comment.TLabel').grid(columnspan=3, column=2, row=_row, sticky=W)

# Header - Output Location
_row += 3
ttk.Label(_frame1, text='Output',
          style='Header2.TLabel').grid(column=0, row=_row, sticky=W)
# Output folder widget
_row += 4
ttk.Label(_frame1, text='Tables for Access:') \
    .grid(column=0, row=_row, sticky=W)
_tableFolderVar = StringVar()
Button(_frame1, text='Table Folder', command=select_export,
       **_bkwargs).grid(column=1, row=_row, sticky=EW)
ttk.Label(_frame1, text='Existing tables appended.',
          style='Comment.TLabel').grid(columnspan=3, column=2, row=_row, sticky=W)

# Reload, Commit, and Attribution widgets
_row += 1
ttk.Label(_frame1, text='MS Access tables formatted in compliance with '
                        'USACE EM 200-1-15.',
          style='Comment.TLabel').grid(column=0, columnspan=4, row=_row,
                                       sticky=EW)
_reloadVar = IntVar()
_reloadVar.set(0)
ttk.Checkbutton(_frame1, text='Reload', variable=_reloadVar, onvalue=1,
                offvalue=0, command=reload_json_data, cursor='exchange') \
    .grid(columnspan=2, column=4, row=_row, sticky=W)
Button(_frame1, text=u'Commit', command=commit,
       **_commit_bkwargs).grid(columnspan=2, column=4, row=_row+1, sticky=EW)
ttk.Label(_frame1, text=u'\xa9 2017 Nicholas Valentour',
          style='Author.TLabel').grid(column=0, row=_row+1, sticky=SW)
for child in _frame1.winfo_children():
    child.grid_configure(padx=5, pady=5)

# Bottom frame displays selected paths.
_row += 2
_frame2 = ttk.Frame(_root, padding="4", relief='sunken', style='Bot.TFrame')
_frame2.columnconfigure(0, weight=1)
_frame2.rowconfigure(0, weight=1)
_frame2.grid(column=0, row=_row, sticky='news')
_row += 1
ttk.Label(_frame2, textvariable=_jsonVar, style='Bot.TLabel') \
    .grid(columnspan=5, row=_row, sticky=NW)
ttk.Label(_frame2, textvariable=_seedVar, style='Bot.TLabel') \
    .grid(columnspan=5, row=_row+1, sticky=W)
ttk.Label(_frame2, textvariable=_folderVar, style='Bot.TLabel') \
    .grid(columnspan=5, row=_row+2, sticky=W)
ttk.Label(_frame2, textvariable=_fileVar, style='Bot.TLabel') \
    .grid(columnspan=5, row=_row+3, sticky=W)
ttk.Label(_frame2, textvariable=_tableFolderVar, style='Bot.TLabel') \
    .grid(columnspan=5, row=_row+4, sticky=W)

for child in _frame2.winfo_children():
    child.grid_configure(padx=1, pady=1)

run_gui()

if __name__ == '__main__':
    run_gui(True)
