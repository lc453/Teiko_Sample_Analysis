import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

cell_types=["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
cell_types_percentages = [f"{cell}_percentage" for cell in cell_types]

def get_summary(connection: sqlite3.Connection) -> str|None:
    cursor = connection.cursor()
    
    total = "+".join(cell_types)
    select_string = ""
    for type in cell_types:
        # Get absolute cell count first
        # b_cell AS b_cell_count
        select_string += f"{type} AS {type}_count, "
        # Get percentage next
        # 100*CAST(b_cell AS FLOAT)/(b_cell+cd8_t_cell+cd4_t_cell+nk_cell+monocyte) AS b_cell_percentage
        select_string += f"100*CAST({type} AS FLOAT)/({total}) AS {type}_percentage, "

    # Remove the trailing comma
    select_string = select_string[:-2]
    select_string = f"SELECT sample, ({total}) AS total_count,{select_string} FROM samples"
    table_name = "summary";
    
    try:
        cursor.execute(f"CREATE TEMPORARY TABLE {table_name} AS {select_string};")
        return table_name
    except Exception as e:
        print(f"Table creation failed with error: {e}")
        return None
    
def get_filter_string(params: list[str|int]) -> str:
    """
    Gets the filter string (i.e. WHERE param = condition) for the query.
    params should be in order [sample type, condition, treatment, response, time since treatment, sex]
    """
    filter=[]
    # First element should be sample type
    if params[0]:
        filter.append(f"sample_type = '{params[0]}'")
    # Second element should be condition
    if params[1]:
        filter.append(f"condition = '{params[1]}'")
    # Third element should be treatment
    if params[2]:
        filter.append(f"treatment = '{params[2]}'")
    # Fourth element should be response
    if params[3]:
        filter.append(f"response = '{params[3]}'")
    # Fifth element should be time since treatment. This one should be treated differently since
    # 0 is a valid time, which would register as false
    if params[4] != "" and params[4] is not None:
        filter.append(f"time_from_treatment_start = '{params[4]}'")
    # Sixth element should be sex.
    if params[5]:
        filter.append(f"sex = '{params[5]}'")
    if len(filter) == 0:
        return ""
    else:
        return "WHERE " + " AND ".join(filter)

def compare_populations(connection: sqlite3.Connection, tablename: str, p1: list[str|int], p2: list[str|int]) -> dict[any]:
    """
    Compares two sets of cell populations based on the desired parameters
    stored in p1 and p2. These params should be in order [sample type, condition, treatment, response, time since treatment, sex]
    """
    cursor = connection.cursor();
    responsive = cursor.execute(f"""
    SELECT {", ".join(cell_types_percentages)} FROM
        {tablename} JOIN
        samples ON {tablename}.sample = samples.sample JOIN 
        subjects ON samples.subject = subjects.subject 
            {get_filter_string(p1)}
    """)
    # Since fetching a row returns a tuple, convert it into np array to make data easier to use
    responsive_data = np.array(responsive.fetchall())

    unresponsive = cursor.execute(f"""
    SELECT {", ".join(cell_types_percentages)} FROM
        {tablename} JOIN
        samples ON {tablename}.sample = samples.sample JOIN 
        subjects ON samples.subject = subjects.subject 
            {get_filter_string(p2)}
    """)
    unresponsive_data = np.array(unresponsive.fetchall())
    
    offset=0.2
    fig, ax = plt.subplots()
    ax.set_ylabel("Percentage of total cell count.")
    colors=['olive','firebrick']
    for i in range(len(responsive_data[1,:])):
        b_plot = ax.boxplot([responsive_data[:,i],unresponsive_data[:,i]],
                    positions=[i-offset,i+offset], patch_artist=True)
        for patch, color in zip(b_plot['boxes'], colors):
            patch.set_facecolor(color)
        ax.text(i,0,f"{cell_types[i]}",horizontalalignment='center')
    legend_labels = ['Responsive', 'Unresponsive']
    legend_handles = [plt.Rectangle((0,0),1,1, color=color) for color in colors]
    ax.legend(legend_handles, legend_labels)
    ax.set_ylim(-1,None)
    fig.savefig("boxplot.png")

    report_strings = []
    for i in range(len(cell_types)):
        cell_report = find_differences(cell_types[i], responsive_data[:,i], unresponsive_data[:,i])
        if cell_report:
            report_strings.append(cell_report)

    return {"boxplot": fig, "report": "\n".join(report_strings)}

def find_differences(cell_type:str, pop1: list[int], pop2: list[int]) -> str:
    significant_findings = []
    # Conduct t-test/f-test to determine statistical significance
    t_stat, p_val1 = stats.ttest_ind(pop1, pop2)
    statistical_significance = 0.05
    if p_val1 < statistical_significance:
        if t_stat > 0:
            significant_findings.append(f"responsive mean is significantly higher (p={p_val1})")
        else:
            significant_findings.append(f"responsive mean is significantly lower (p={p_val1})")
    f_value = (np.std(pop1)**2)/(np.std(pop2)**2)
    p_val2 = stats.f.cdf(f_value, len(pop1)-1, len(pop2)-1)
    if p_val2 < statistical_significance:
        if f_value > 1:
            significant_findings.append(f"responsive spread is significaltly wider (p={p_val2})")
        else:
            significant_findings.append(f"responsive spread is significantly tighter (p={p_val2})")
    if len(significant_findings)==0:
        return ""
    else:
        return f"For cell {cell_type}: " + " and ".join(significant_findings)
    



def subset_analysis(connection: sqlite3.Connection, params: list[str]) -> list[tuple]:
    """
    Returns simple counts from the samples given paramters stored in params
    These params should be in order [sample type, condition, treatment, response, time since treatment, sex]
    """
    cursor = connection.cursor()
    query_string = f"""
    SELECT project, response, sex FROM samples JOIN subjects ON samples.subject = subjects.subject
    {get_filter_string(params)}
    """
    table_name = "subset"
    try:
        cursor.execute(f"CREATE TEMPORARY TABLE {table_name} AS {query_string};")
    except Exception as e:
        print(f"Table creation failed with error: {e}")
        return None

    # obtain number of samples for each case:
    # Each Project
    subset_search="""
    SELECT COUNT(CASE WHEN {0} = '{1}' THEN 1 ELSE NULL END),
    COUNT(CASE WHEN {0} = '{2}' THEN 1 ELSE NULL END),
    COUNT(CASE WHEN {0} = '{3}' THEN 1 ELSE NULL END) FROM {4};
    """
    prj_search = cursor.execute(subset_search.format("project","prj1","prj2","prj3",table_name))
    prj_count = prj_search.fetchone()

    # Responders/Non-responders
    resp_search = cursor.execute(subset_search.format("response","no","yes","n/a",table_name))
    resp_count = resp_search.fetchone()

    # Males/Females
    sex_search = cursor.execute(subset_search.format("sex","M","F","n/a",table_name))
    sex_count = sex_search.fetchone()
    
    cursor.execute(f"DROP TABLE {table_name};")

    return [prj_count,resp_count,sex_count]