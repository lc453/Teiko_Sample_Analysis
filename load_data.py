import sqlite3
from pandas import read_csv

schema_script = """
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS samples;
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
"""


def main() -> None:
    connection = sqlite3.connect("cell_counts.db")
    connection.executescript(schema_script)
    cursor = connection.cursor();

    base_data = read_csv("cell-count.csv")
    #file = open("cell-count.csv")
    #base_data = csv.reader(file)
    base_data.to_sql("data", connection, if_exists="replace", index=False)
    #connection.execute("""
    #    INSERT INTO projects (project, sample_type)
    #    SELECT DISTINCT project, sample_type FROM data;
    #""")
    connection.execute("""
        INSERT INTO subjects (subject, project, age, sex, condition, treatment, response)
        SELECT DISTINCT subject, project, age, sex, condition, treatment, response FROM data;
    """)
    connection.execute("""
        INSERT INTO samples (sample, sample_type, subject, time_from_treatment_start, b_cell,
            cd8_t_cell, cd4_t_cell, nk_cell, monocyte)
        SELECT sample, sample_type, subject, time_from_treatment_start, b_cell, cd8_t_cell,
            cd4_t_cell, nk_cell, monocyte
        FROM DATA;
    """)
    cursor.execute("DROP TABLE data;")
    connection.commit()
    connection.close()

if __name__ == "__main__":
    main()