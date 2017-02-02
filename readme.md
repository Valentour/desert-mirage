# Desert Mirage

**Desert Mirage** is an open-source Python data processing module for the [geophysical system verification][s1] (GSV) of [Geonics EM61-MK2][s2] instruments. A compiled Windows Form GUI written in C# is also included with the module.

[s1]: https://www.serdp-estcp.org/Featured-Initiatives/Munitions-Response-Initiatives/Geophysical-System-Verification
[s2]: http://www.geonics.com/html/em61-mk2.html

<div style="text-align:center"><img src ="https://github.com/valentour/desert-mirage/blob/master/images/repo_gui_cs.PNG" /></div>

## Usage

*    Supports IVS reporting for both single-coil and multi-coil towed-array systems.  
*    Identifies the peak sensor dynamic response and offset distance from the true seed item location in the instrument verification strip (IVS).   
*    Outputs the test results to *.csv* tables formatted for direct import into the standard MS Access project database used by the US Army Corps of Engineers (USACE).

## Background

<div style="text-align:center"><img src ="https://github.com/valentour/desert-mirage/blob/master/images/gsv_ivs.PNG" /></div>

The [GSV][s3] process was developed by the Strategic Environmental Research and Development Program (SERDP) and the Environmental Security Technology Certification Program (ESTCP).  A primary element of the GSV is the instrument verification strip (IVS).  

> The IVS is a line of objects buried in a representative, open area convenient to the location where the geophysical survey equipment is set up or operated. The objective of the IVS is to verify that the geophysical detection system is operating properly at the beginning and end of each data collection day. The objects should be observed in the data with signals that are consistent with both historical measurements and physics-based model predictions. The IVS also serves to verify that the geo-location system provides accurate sensor location data. \-[GSV Report][s3]

[s3]: https://www.serdp-estcp.org/Featured-Initiatives/Munitions-Response-Initiatives/Geophysical-System-Verification
[s4]: https://www.serdp-estcp.org/content/download/7426/94837/version/4/file/GSV+Final+Report+with+Addendum+%28V2%29.pdf

## Supported Tables

**IVS\_daily\_results\_Table** - reports the peak sensor response magnitude and geographic position for each sensor and dataset.

**IVS\_StandardValues\_Table** - reports the running average of the peak sensor response magnitude and euclidean offset for each sensor and seed item. These running averages may be used in conjunction with the theoretical sensor response curves from the GSV Report.

**Seed&Test\_Item\_Table** - reports the euclidean offset distance between peak sensor response location and true seed item location for each sensor and dataset.

## Requirements

* **Windows operating system**  
* **Python 3 >= 3.3**  
* **Numpy >= 1.11.2** - earlier versions may work.  
* **Pandas >= 0.19.2** - earlier versions may work.  <p>
**Recommended**:  **[Anaconda][s5] >= 4.2.0** - silver bullet for all of the above Python dependencies.  <p>
If you ever need to check Python or package versions, you can enter the following command-lines:  <p>
Verify Python version: `python --version` or `conda info`  
    Verify package version: `pip list` or `conda list`  
    Or install a package: `pip install` or `conda install` followed by the package name.  
[s5]: https://www.continuum.io/downloads

## Basic Instructions

### Contents

`/data` - fictitious sample sensor data for testing purposes.

`/py` - python module.

`Desert Mirage.exe` - a *C# Windows Form* GUI built on the *Microsoft .NET Framework 4.6.1*.

`py_console.txt` - example console output. This file will be created or appended if the module is executed from the GUI + Python Mode.  Example Python console output using the sample data is shown below.

<div style="text-align:center"><img src ="https://github.com/valentour/desert-mirage/blob/master/images/py_output.PNG" /></div>

### GUI + Python Mode  
All you need to do to run Desert Mirage is download the repository *.zip* and run the *.exe*. The executable is a *C# Windows Form* GUI built on the *Microsoft .NET Framework 4.6.1*.  The form will ask for general information about the survey and the directory paths to the json, input data folder, and python interpreter.  <p>

### Pure Python Mode
You can run the python module directly without the *.exe* by configuring the `/py/desert_mirage_config.json` in a text editor.  <p>
Copy/Paste local directory paths into the `GUI{}` object fields in the *json*. This dictionary is what is populated when running the executable. Be sure to use "/" or "\\\" for Windows directory paths in the *json*.  <p>
Now execute the module using the command-line below. You will have to use the full file paths and not the relative paths shown.

`python /py/desert_mirage_main.py /py/desert_mirage_config.json`  

A Python GUI developed using the *Tkinter* package can be found in */py/tk-gui/*. This GUI was abandoned in favor of the C# Windows Form, but the GUI is in working condition if you're adventurous.  <p>

## Caveats

### IVS Sensor Data
Sensor data is batch processed from the user-defined "Data Folder". Files should be in *.csv* format with a header in the first line. For those curious, the module reads each .csv into a Pandas DataFrame by calling `pandas.read_csv(file, header=0)`.  

### IVS Seed Data
The seed *.csv* must contain the following columns within the header:  <p>
**Test\_Item\_ID**: The IVS Seed ID. Must be unique for transcribing to the MS Access formatted table.  
**TrueX**: The item X-positioning in UTM or State Plane Coordinate projections.  
**TrueY**: The item Y-positioning in UTM or State Plane Coordinate projections.  
**Placement**: Description of the orientation of the buried item within the track: **Vertical**, **Inline**, or **Crossline**.  

### Line Naming Convention
Here are the line naming convention patterns for single-coil and towed-array surveys.

| String Key| Description                                                                                              |
|-------	|------------------------------------------------------------------------------------------------------------ |
| `L`   	| Default prefix in raw EM61-MK2 data line names.                                                            	|
| `*`  	 | Any sequence of alphanumerics + underscores. Equivalent to the *regex* class `[A-Za-z0-9_]`.                |
| `MMDD` | 4-digit numeric date of collection. Equivalent to *regex* class `[0-9]{4}`.                                	|
| `TN`  	| Test ID alphanumeric sequence. Currently only the IVS test is supported.                                    |
|  `a`   |  Alpha character to distinguish opening/closing or am/pm tests. An example *regex* class is `[ap]{1}`.      |
| `SN`  	| Sensor IDs differ by array type. Single-coil IDs include the *regex* class `[A-Za-z]+[0-9]*`.<sup>[1]</sup> |


|Survey Type | Line Name Pattern | Notes  
|------------|--------           |--------------------------------------|
|Single Coil |`L[*][TN][MMDD][*]a` | `SN` occupies either `[*]` slot.     |
|Towed Array | `L[*][TN][*]a_SN` | `MMDD` occupies either `[*]` slot.   | 

<sup>[1]</sup> Towed-array line data is assumed to have been processed by Geonics Dat61MK2 software which automatically adds Sensor IDs as 2-digit numerics (e.g., 01) to the end of line names.  

Contact: <Nicholas.Valentour@gmail.com>.

&copy; 2017 Nicholas Valentour

