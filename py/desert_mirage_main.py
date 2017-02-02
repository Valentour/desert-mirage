#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
desert_mirage_main.py
This is the main entry point to the desert mirage module.
Accepts the json path as an argument from command-line.
Copyright (c) Jan 2017 Nicholas Valentour
"""
import sys
import os
from desert_mirage_lib import *

np.set_printoptions(edgeitems=4, infstr='inf', linewidth=79,
                    nanstr='nan', precision=4, suppress=False,
                    threshold=40, formatter=None)
pd.set_option('expand_frame_repr', True, 'max_seq_items', 40,
              'max_colwidth', 60, 'precision', 4, 'display.float_format',
              lambda x: '%.4f'%x, 'display.max_rows', 10,
              'chop_threshold', 0.0001)

# String parsing functions.
def parse_date_from_string(list_o_str, min_len=3):
    """Parses 4-digit date by filtering on consecutive numerics of length
    ``min_len`` in strings ``list_o_str``. If consecutive numerics are longer than
     4-digits, returns last 4-digits."""
    digit_list = []
    for astr in list_o_str:
        ds = [s for s in re.findall(r'\d+',
                                    repr(astr)) if len(s) >= min_len][0]
        if len(ds) == 4:
            ds = ds[:2]+'/'+ds[2:4]
        else:  # Take last four.
            ds = ds[-4:-2]+'/'+ds[-2:]
        digit_list.append(ds)
    return digit_list

def parse_line_name(pdf, sensor):
    """
    Extract rows from DataFrame ``pdf`` with the substring sensor ID ``sensor``
    present in the column label "Line". Must contain column "Line" in ``pdf``.

    Parameters
    ----------
    pdf : pd.DataFrame
        DataFrame containing a column 'Line' of line name strings.
    sensor : str
        Substring ID for inclusive filtering rows in ``pdf``.

    Returns
    -------
    pd.DataFrame : pd.DataFrame
        ``pdf`` with additional columns 'Sensor_ID', 'FileName', 'TestID',
        'AM_PM', and 'Date'.

    Notes
    -----
    Single Coil - L[*][TN][MMDD][*]a - SN occupies either [*] slot.
    Towed Array - L[*][TN][*]a_SN    - MMDD occupies either [*] slot.
    Single-coil Sensor IDs include regex [A-Za-z]+[0-9].
    Towed-array Sensor IDs are 2-digit numeric suffixes (e.g., 01).

    #. `L` - Default prefix in raw EM61-MK2 data line names.
    #. `*` - Any sequence of alphanumerics + underscores, regex [A-Za-z0-9_].
    #. `MMDD` - 4-digit numeric date of collection, regex [0-9]{4}.
    #. `TN` - Test ID alphanumeric sequence. Currently only IVS test is 
       supported.
    #. `a` - Alpha char to distinguish opening/closing or am/pm tests, [ap]{1}.
    #. `SN` - Sensor ID `sensor`. Differs by array type.
    """
    df1 = pdf.copy()
    # Only Towed Array lines can end in a numeric.
    if any(df1.Line.str.endswith(
            sensor)) and _jGUI.SurveyType != 'Single Coil':
        print('Identified towed array line data.')
        df1['Sensor_ID'] = ['{}'.format(sensor)]*len(df1.index)
        df1['FileName'] = df1['Line']
        df1['TestID'] = [_jGUI.IvsID]*len(df1.index)
        df1['AM_PM'] = pd.Series(df1.Line.str[-4:-3]+'m').str.upper()
        df1['Date'] = parse_date_from_string(df1.Line.values, min_len=4)
        return df1

    print('Identified single coil line data.')
    df1['Sensor_ID'] = [sensor]*len(df1.index)
    df1['Filename'] = df1['Line']
    df1['TestID'] = [_jGUI.IvsID]*len(df1.index)
    df1['AM_PM'] = pd.Series(df1.Line.str[-1:]+'m').str.upper()
    df1['Date'] = parse_date_from_string(df1.Line.values, min_len=4)
    return df1

def subset_col_ending_id_string(unique_col_entries, id_string=None):
    """
    Search col for unique entries ending with two-digit numeric substring.

    Parameters
    ----------
    unique_col_entries : list
        list of all unique array entries.
    id_string : str
        substring line integer ID ('01') for inclusive masking.

    Returns
    -------
    list : logical set of unique entries in array containing ``id_string``.
        If substring is empty, then returns all non-integer ending entries.
    """
    if id_string is None:
        id_string = ['01']
    no_match_list = []
    match_list = []
    for line in unique_col_entries:
        # Check if line name ends in an integer returns false if not.
        last_char = re.split("[^\d]", line)[-1]
        if last_char is not None and last_char in id_string:
            match_list.append(line)
        else:
            no_match_list.append(line)
    if len(match_list) > 0:
        return match_list
    return list(set(unique_col_entries)-set(no_match_list))


# Basic stats
def static_test_ptp(ch, thr):
    """Static test peak to peak.
    Returns
    -------
    float : Percent of values in `ch` exceeding threshold `thr`.
    """
    exceedances = 0.
    if np.ptp(ch)[0] > thr:
        while np.ptp(ch)[0] > thr:
            ch.pop(ch.max())
            exceedances += 1.
            ch.pop(ch.min())
            exceedances += 1.
        exceedances /= len(ch.values)
        return 1.-exceedances
    return 1.


# IVS data processing functions
def dynamic_response_dict(track, first_pass_bool, aseed_series):
    """Process ``track`` data for the seed described by ``aseed_series``. If this
    is the first pass the string '_fwd' will be appended to the output line,
    otherwise '_bck' will be appended.

    Parameters
    ----------
    track : pd.DataFrame
        A pass of the ivs line.
    first_pass_bool : bool
        True if first pass of seed item (fwd), False if not (bck).
    aseed_series : pd.Series

    Returns
    -------
    ivs table dict : dict
        keys as USACE MS Access table column names and items as values.
    """
    seed_name = aseed_series.Test_Item_ID.values[0]
    truex = aseed_series.TrueX.values[0]
    truey = aseed_series.TrueY.values[0]

    # Set IVS Major Axis and measurement system.
    seedloc = truey
    if _jGUI.MajorAxis == 'X':
        seedloc = truex

    # Mask data outside radius from true seed along major axis.
    distal_mask = (track[_jGUI.MajorAxis] >= seedloc-MASK_RADIUS) \
                  & (track[_jGUI.MajorAxis] <= seedloc+MASK_RADIUS)
    proximal_data = track.loc[distal_mask, :]

    # Max amplitude near seed info.
    peak_index = proximal_data[_jGUI.ResponseChannel].idxmax()
    peak_row = proximal_data.loc[peak_index]
    peak_rsp = peak_row[_jGUI.ResponseChannel].max()
    peak_x = peak_row.loc['X']
    peak_y = peak_row.loc['Y']

    # Calc the peak response euclid_offset and distance from known seed item.
    euclid_offset = euclidean_distance(peak_x, peak_y, truex, truey, 4, 2)
    if euclid_offset >= MASK_RADIUS:
        peak_rsp = 0.
    # Additional line info to report.
    # TODO: 1. Add ivs track suffix field to json.
    track_pass = 'bck'
    if first_pass_bool:
        track_pass = 'fwd'
    filename_str = peak_row.loc['Line']+'_'+track_pass

    # Populate dict for Access DB table
    access_dict = [0, filename_str, peak_row['Date'], peak_row['AM_PM'],
                   seed_name, peak_row['Sensor_ID'], peak_rsp, peak_x,
                   peak_y, '', '', euclid_offset, _jGUI.ResponseChannel]
    dict_keys = _jAccess.IVSDailyResultsTable.Columns
    return dict(zip(dict_keys, access_dict))

def relative_diff(num1, num2):
    """Defined as absolute difference divided by maximum absolute value.

    Parameters
    ----------
    num1 : numeric
    num2 : numeric
    """
    return abs(abs(num1)-abs(num2))/max(abs(num1), abs(num2))

def process_dynamic_response(ivs_df, seed_series):
    """Process dynamic response related lines in ``ivs_df`` for seed item data in
    ``seed_item_series``.

    Parameters
    ----------
    ivs_df : pd.DataFrame
    seed_series : pd.Series

    Returns
    -------
    table dataframe : pd.DataFrame
        Columns from MS Access Table 'IVS_daily_results_Table'.
    """
    unique_lines = [i for i in ivs_df.Line.unique()]
    print('Processing {} in {}'.format(seed_series.Test_Item_ID.values[0],
                                       unique_lines))
    df_grp = ivs_df.groupby(['Line'])
    # Initialize Access database formatted table.
    cols = _jAccess.IVSDailyResultsTable.Columns
    access_table = pd.DataFrame(columns=cols)
    for test_line in unique_lines:
        test_grp = df_grp.get_group(test_line)
        midpoint_index = math.floor(len(test_grp.index)/2)
        fwd_track = test_grp.copy().iloc[:midpoint_index]
        bck_track = test_grp.copy().iloc[midpoint_index:]
        fwd_dict = dynamic_response_dict(fwd_track, True, seed_series)
        bck_dict = dynamic_response_dict(bck_track, False, seed_series)
        fwd_rsp = fwd_dict['IVS_Response']
        bck_rsp = bck_dict['IVS_Response']
        # Check for tracks that do not pass the same test item on each pass.
        # Threshold logic is hard-coded. Relative diff 50% and min resp 20mV.
        # TODO: 2. Add rel diff and min resp fields to json.
        if relative_diff(fwd_rsp, bck_rsp) < .5 and fwd_rsp > 20 \
                and bck_rsp > 20:
            access_table = access_table.append(other=fwd_dict,
                                               ignore_index=True)
            access_table = access_table.append(other=bck_dict,
                                               ignore_index=True)
            continue
        if _jGUI.SurveyType == 'Single Coil':
            continue
        # If Towed Array then geometry flips on backward track.
        if fwd_rsp > bck_rsp and fwd_rsp > 20:
            access_table = access_table.append(other=fwd_dict,
                                               ignore_index=True)
            continue
        if bck_rsp > fwd_rsp and bck_rsp > 20:
            access_table = access_table.append(other=bck_dict,
                                               ignore_index=True)
            continue
    return access_table


# Seed item functions.
def import_seed_data_csv(fp):
    """
    Import seed data csv in path 'fp'. Fails if header does not contain
     column names in '_seed_columns'.

    Parameters
    ----------
    fp : str
        os filepath to csv.

    Returns
    -------
    seed item dataframe : pd.DataFrame
    """
    sdf = pd.read_csv(fp, header=0)
    for col in _seed_columns:
        if col not in sdf.columns:
            print('Required column {} was not found in seed csv.'.format(col))
            exit(1)
    return sdf

def set_ivs_seed_geometry(seed_table):
    """
    Used for formatting into MS Access table. Creates columns 'Orientation'
    and 'Inclination' from strings in 'Placement' of the ``seed_table``
    DataFrame returned by 'import_seed_data_csv'.

    Parameters
    ----------
    seed_table : df
        df returned by 'import_seed_data_csv'

    Returns
    -------
    pd.DataFrame : ``seed_table`` with 'Orientation' and 'Inclination'.

    Notes
    -----
    Orientation of nose, degrees (0/180 is N/S, 90/270 is W/E).
    Inclination of nose, degrees (0/360 is flat, 90/270 is down/up).

    """
    for i in seed_table.index.values:
        # IVS Major Axis is X.
        if _jGUI.MajorAxis == "X":
            if seed_table.at[i, 'Placement'].startswith('Vert'):
                seed_table.at[i, 'Orientation'] = 0
                seed_table.at[i, 'Inclination'] = 270
            if seed_table.at[i, 'Placement'].startswith('In'):
                seed_table.at[i, 'Orientation'] = 270
                seed_table.at[i, 'Inclination'] = 0
            if seed_table.at[i, 'Placement'].startswith('Cross'):
                seed_table.at[i, 'Orientation'] = 0
                seed_table.at[i, 'Inclination'] = 0
            return seed_table
        # IVS Major Axis is Y.
        if seed_table.at[i, 'Placement'].startswith('Vert'):
            seed_table.at[i, 'Orientation'] = 0
            seed_table.at[i, 'Inclination'] = 270
        if seed_table.at[i, 'Placement'].startswith('In'):
            seed_table.at[i, 'Orientation'] = 180
            seed_table.at[i, 'Inclination'] = 0
        if seed_table.at[i, 'Placement'].startswith('Cross'):
            seed_table.at[i, 'Orientation'] = 90
            seed_table.at[i, 'Inclination'] = 0
        return seed_table

def seeds_within_lanewidth(atrack, thresh):
    xtrue = _csvSeedDF.TrueX.values
    ytrue = _csvSeedDF.TrueY.values
    slist = []
    for i, (xt, yt) in enumerate(zip(xtrue, ytrue)):
        dx = np.square(np.subtract(atrack.X.values, xt))
        dy = np.square(np.subtract(atrack.Y.values, yt))
        count_data = np.count_nonzero(
                [i for i in np.sqrt(dx+dy) if i < thresh])
        if count_data:
            slist.append(_csvSeedDF.Test_Item_ID.values[i])
    return slist


# File collection and exporting.
def collect_files_in_directory(dfolder=None, fpattern=None):
    if not fpattern:
        fpattern = '**/*.csv'
    if not dfolder:
        dfolder = _jGUI.DataFolder
    file_list = glob(os.path.join(dfolder, '{}'.format(fpattern)),
                     recursive=True)
    file_list = [os.path.normpath(i) for i in file_list]
    base_name_list = [os.path.basename(i) for i in file_list]
    print('Processing files: {} \n'.format(base_name_list))
    return file_list

def export_access_table(tbl_df, atable_name):
    """
    Exports the ``tbl_df`` as a csv formatted to match USACE MS Access tables.
    Export location is a new folder in the local directory one level above the
    location of this file. See global script variable '_access_folder'.

    Supported tables include:

    IVS_daily_result_Table.csv
    Seed&Test_Item_Table.csv
    IVS_Standard_Values_Table.csv
    """

    def drop_duplicates_create_keys(adf, tbl_name):
        if all([item in tbl_name for item in ['Standard', 'Values']]):
            chk_cols = ['Test_Item_ID', 'Sensor_ID']
            adf.drop_duplicates(subset=chk_cols, inplace=True)
            adf['Project_ID'] = [2000.+i for i in range(len(adf.index))]

        if all([item in tbl_name for item in ['daily', 'result']]):
            chk_cols = ['Filename', 'Date', 'AM_PM', 'Test_Item_ID',
                        'Sensor_ID']
            adf.drop_duplicates(subset=chk_cols, inplace=True)
            adf['OID'] = [1000.+i for i in range(len(adf.index))]

        if all([item in tbl_name for item in ['Seed', 'Test', 'Item']]):
            adf.drop_duplicates(inplace=True)
        return adf

    access_dir = os.path.join(_access_folder, "AccessTables")
    if not os.path.exists(access_dir):
        os.makedirs(access_dir)

    atable_path = os.path.join(access_dir, atable_name)
    print('Writing table: {}'.format(atable_name))
    print('    Directory: {}'.format(access_dir))
    if os.path.isfile(atable_path):
        orig_table = pd.read_csv(atable_path, header=0)
        tbl_df = orig_table.append(tbl_df, True, False)
        print('    An existing table was appended with unique entries only.')
    new_df = drop_duplicates_create_keys(tbl_df, atable_name)
    new_df.to_csv(atable_path, index=False)
    return


# General processing by file and sensor.
def df_sensor_lines_only(df, id_substring, test_substring):
    """Filter pd.DataFrame ``df`` lines by ``id_substring` and
    ``test_substring``.

    Parameters
    ----------
    df : pd.DataFrame
    id_substring : str
    test_substring : str

    Returns
    -------
    DataFrame : pd.Dataframe
    """
    if not id_substring:
        print('id_substring is empty.')
        sys.exit(2)
    df = df.loc[df['Line'].str.contains(test_substring), :]
    df = df.loc[df['Line'].str.contains(id_substring), :]
    # Single sensor ids of length 1 must be second index in line name.
    if len(id_substring) == 1:
        lprefix = "L"+id_substring
        return df.loc[df['Line'].str.startswith(lprefix), :]
    # Check if id_substring is a towed array id.
    if id_substring in _towed_array_ids:
        return df.loc[df['Line'].str.endswith(id_substring), :]
    return df

def process_file_in_folder(ifile, sensors_list):
    """Process ``ifile`` in Data Folder for sensor ids in ``sensors_list``.
    Parameters
    ----------
    ifile : str
    sensors_list : list

    Returns
    -------
    None : None
    """
    df = pd.read_csv(ifile, header=0)
    # Skip file if response channel is not in file header.
    if _jGUI.ResponseChannel not in list(df):
        print('Response Channel {} not in file header.'
              .format(_jGUI.ResponseChannel))
        return
    for sid in sensors_list:
        # Process the current file lines
        process_ivs_and_create_access_tables(sid, df.copy())
    return

def process_ivs_and_create_access_tables(sid, df):
    """Process sensor id ``sid`` data in pd.DataFrame ``df``. Creates folder
    in parent directory of this file. See ``export_access_table`` for more.

    Parameters
    ----------
    sid : str
    df : pd.DataFrame

    Returns
    -------
    None : None
    """
    # Filter lines that do not contain ivs string identifier.
    df2 = df_sensor_lines_only(df, sid, _jGUI.IvsID)
    lane_seed_list = seeds_within_lanewidth(df2, LANE_WIDTH/2)
    _seed_collector.append(lane_seed_list)
    # Skip file if no seed items within radius.
    if not lane_seed_list:
        return
    print('Test_Item_IDs active: {}'.format(lane_seed_list))
    sensor_df = parse_line_name(df2, sid)
    if df2.values[0].any():
        print('DataFrame head:\n{}\n'.format(df2.head()))
    if sensor_df is None:
        print('Warning: No sensor lines identified after parsing line names.')
        return

    # Create "IVS_daily_result_Table".
    ivs_table = pd.DataFrame(columns=_jAccessIVS.Columns)
    for aseed in lane_seed_list:
        aseed_df = _csvSeedDF.loc[
            _csvSeedDF['Test_Item_ID'].str.contains(aseed)]
        temp_table = process_dynamic_response(sensor_df, aseed_df)
        ivs_table = ivs_table.append(temp_table, True, False)
    export_access_table(ivs_table, _jAccess.IVSDailyResultsTable.TName)

    # Create "Seed&Test_Item_Table".
    seed_table = pd.DataFrame()
    seed_table['Offset_distance'] = ivs_table['Comment']
    seed_table['Test_Item_ID'] = ivs_table['Test_Item_ID']
    seed_table['Sensor_ID'] = ivs_table['Sensor_ID']
    seed_table['Date'] = ivs_table['Date']
    # Drop duplicates so pd.merge does not add suffixes to duplicate label.
    temp_seeds = _csvSeedDF.dropna(axis=1, inplace=False)
    seed_table = seed_table.merge(temp_seeds, on='Test_Item_ID', how='left')
    seed_table = set_ivs_seed_geometry(seed_table)
    # Append table to empty table to retrive dropped cols.
    tmp_cols = _jAccess.SeedTestItemTable.Columns
    seed_table = pd.DataFrame(columns=tmp_cols).append(seed_table, True, False)
    export_access_table(seed_table, _jAccess.SeedTestItemTable.TName)

    # Create "IVS_Standard_Values_Table".
    tmp_cols = _jAccess.IVSStandardValuesTable.Columns
    std_values_table = pd.DataFrame(columns=tmp_cols)
    agg_cols = ['Sensor_ID', 'Test_Item_ID']
    ivs_tablegrp = ivs_table.groupby(by=agg_cols, as_index=False).mean()
    std_values_table[agg_cols] = ivs_tablegrp[agg_cols]
    std_values_table['Mean_Response_online'] = ivs_tablegrp['IVS_Response']
    std_values_table['Mean_Response_online_offset'] = ivs_tablegrp['Comment']
    export_access_table(std_values_table,
                        _jAccess.IVSStandardValuesTable.TName)

    print('Processed SensorID: {}\n'.format(sid))
    return


def validate_json_fields():
    """Checks ``IvsID`` and ``SurveyType`` fields in the json file."""
    # Check ivs test string identifier was populated.
    if _jGUI.IvsID == "":
        print('IVS String Identifier was not defined.')
        sys.exit(2)
    # Check SingleCoilSensorID is populated for single-coil and mixed surveys.
    if _jGUI.SurveyType != 'Towed Array' and not _jGUI.SingleCoilSensorID:
        print('Sensor ID entries required for single-coil or mixed data.')
        sys.exit(2)
    return

# Define internal global parameters.
_dir_path = os.path.dirname(os.path.realpath(__file__))
# Access tables output to 'AccessTables' folder in parent directory.
_access_folder = os.path.dirname(_dir_path)
# Required seed csv columns.
_seed_columns = ['Test_Item_ID', 'TrueX', 'TrueY']
# Geonics Multi61 software output for towed array sensor coils ids.
_towed_array_ids = ['01', '02', '03']

# Default json file name (implied path is os.cwd()).
_json_path = os.path.abspath("desert_mirage_config.json")

_seed_collector = []

if __name__ == "__main__":
    print('----Desert Mirage Begin----\n')
    print('Arguments: ', [i for i in sys.argv])
    if len(sys.argv) > 1:
        _json_path = os.path.abspath(sys.argv[1])
        print("json file path: {}".format(_json_path))

    # Create dictionary-like object from json.
    _jsonDict = json_config(jfile=_json_path, jobj_hook=JsonDict)
    # Create dataframe of seed csv file.
    _csvSeedDF = import_seed_data_csv(_jsonDict.GUI.SeedFile)

    # Shorten the names of more frequently used json fields.
    _jGUI = _jsonDict.GUI
    _jAccess = _jsonDict.AccessDatabase
    _jAccessIVS = _jsonDict.AccessDatabase.IVSDailyResultsTable
    validate_json_fields()

    # Import positioning params.
    LANE_WIDTH = float(_jGUI.LaneWidthMask)
    MASK_RADIUS = float(_jGUI.SeedRadiusMask)
    if _jGUI.PositioningUnits == 'Feet':
        LANE_WIDTH *= 3.28  # convert meters to feet
        MASK_RADIUS *= 3.28  # convert meters to feet

    # Collect sensor ids using survey type and single coil sensor id entry.
    sensor_id_list = []
    if _jGUI.SingleCoilSensorID != "":
        sensor_id_list = [i.strip() for i in
                          _jGUI.SingleCoilSensorID.split(",")]
    if 'Single' not in _jGUI.SurveyType:
        sensor_id_list.extend(_towed_array_ids)
    print('Sensor ID List: ', sensor_id_list)

    # Collect IVS data files to process.
    _fileList = collect_files_in_directory(dfolder=_jGUI.DataFolder,
                                           fpattern='**/*.csv')

    # Main loop on data folder.
    for _ in _fileList:
        print('File: {}'.format(os.path.basename(_)))
        process_file_in_folder(_, sensor_id_list)

    if not _seed_collector:
        print('No seed items found in data provided.')
    print('\n----Desert Mirage End----')
