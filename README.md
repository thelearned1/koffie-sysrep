# README

`sysrep.py` is a simple Python program for processing certain kinds of data
in Excel format. 

# INSTALLATION

No installation is necessary.  Python 3.9.9 is required for the 
operation of the program.

# OPERATION

This program is quite primitive, and as a consequence there are few 
instructions for operation.  It reads in a single input file, called
`input_data.xlsx`, from the same directory as `main.py`.  This can 
contain any data that contains the following columns:

* Company Name (string)
* VIN (string)
* Annual GWP (number)
* Effective Date (Date)
* Expiration Date (Date)
* State (two-letter string from the set { 'IL', 'TN' })

Note that, should some of these columns be missing, the program will
crash.  However, the program can generally recover from malformed data,
though it might ignore the row depending on the severity.

# OUTPUT

After processing, the program outputs a report, dated August 1, 2022,
summarizing the above data and some of their derivatives.  The summary 
consists of an Excel spreadsheet, `aggregated_report-2022 08 01.xlsx`.
There is no other output except a line to the command line confirming 
that the input file has been read.

# MANIFEST 

The current version of the software contains the following files:

```
+ sysrep-challenge/
|
+-- .gitignore
|
+-- ASSESSMENT.md
|
+-- README.md
|
+-- aggregated_report-2022 08 01.xlsx
|
+-- input_data.xlsx
|
+-- main.py
|
+-- requirements.txt
```

# COPYRIGHT 

The copyright on this matter is unclear.

# GIT 

You can download the latest version of this software from Github via the
command line:
```
git clone https://github.com/thelearned1/spacewar
```
You will probably want to fork the repo first, since pull requests will 
be denied.

# BUGS

No bugs are known at the moment provided the input matches the listed 
requirements; the program does a reasonably good job of cleaning up the
data on its own.  

