# Teiko_Sample_Analysis
A simple tool designed to analyze cell samples from different drug trials

Depends on numpy, matplotlib, tkinter, sqlite3, scipy, and pandas.
To create the database, you must run load_data.py.
Then, in your python environment with these dependencies installed, you can
simply run main.py to run the analysis tool.

The database schema used was
```
CREATE TABLE subjects(
    subject TEXT PRIMARY KEY NOT NULL,
    project TEXT NOT NULL,
    age INTEGER NOT NULL,
    sex TEXT NOT NULL,
    condition TEXT NOT NULL,
    treatment TEXT NOT NULL,
    response TEXT
);
CREATE TABLE samples(
    sample TEXT PRIMARY KEY NOT NULL,
    sample_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    time_from_treatment_start INTEGER NOT NULL,
    b_cell INTEGER NOT NULL,
    cd8_t_cell INTEGER NOT NULL,
    cd4_t_cell INTEGER NOT NULL,
    nk_cell INTEGER NOT NULL,
    monocyte INTEGER NOT NULL
);
```
My reasoning here was that all of the data specific to patiends should be stored with the patient. I considered creating another table with just project and sample type, since sample type only varried from project-to-project, but ultimately decided to keep sample type with the rest of the sample data, even though it doesn't change from sample-to-sample, just because it is relevant to the rest of the sample data. Over hundreds of projects, the samples table would scale very large so we would want to track programs that access it to ensure that it isn't being accessed more than it needs to.
I chose to structure my code by creating analysis methods in the most general form possible, putting specific controls in the main user interface. I chose a tkinter ui over a web-based interface for this problem because I decided that a simple UI based entirely in python would be adequate for a sample analysis demo like this.
