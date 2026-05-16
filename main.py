import tkinter as tk
from tkinter import ttk
from analysis import get_summary, compare_populations, subset_analysis
import sqlite3
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

DATABASE = "cell_counts.db"

def main() -> None:
    connection = sqlite3.connect(DATABASE)
    summary_table = get_summary(connection)
    root = tk.Tk()
    root.title("Sample Data Analysis")
    root.geometry("600x800+350+30")
    
    filter_frame = ttk.Frame(root, height=50, width=600, padding=(0,20) )
    button_frame = ttk.Frame(root, height=50, width=600)
    plot_frame = ttk.Frame(root, height=400, width=600)
    report_frame = ttk.Frame(root, height=400, width=600)
    summary_frame = ttk.Frame(root, height=800, width=1200)
    
    plot_image = tk.Label()


    # Regions used for easier readability in vscode 
    #region FILTER FIELDS
    type_value = tk.StringVar()
    type_items = ["PBMC", "WB", ""]
    type_cb = ttk.Combobox(filter_frame, values=type_items, textvariable=type_value)

    condition_value = tk.StringVar()
    condition_items = ["melanoma", "carcinoma", ""]
    condition_cb = ttk.Combobox(filter_frame, values=condition_items, textvariable=condition_value)

    treatment_value = tk.StringVar()
    treatment_items = ["miraclib", "phauximab", ""]
    treatment_cb = ttk.Combobox(filter_frame, values=treatment_items, textvariable=treatment_value)

    response_value = tk.StringVar()
    response_items = ["yes", "no", ""]
    response_cb = ttk.Combobox(filter_frame, values=response_items, textvariable=response_value)

    time_value = tk.StringVar()
    time_items = ["0", "7", "14", ""]
    time_cb = ttk.Combobox(filter_frame, values=time_items, textvariable=time_value)

    sex_value = tk.StringVar()
    sex_items = ["M", "F", ""]
    sex_cb = ttk.Combobox(filter_frame, values=sex_items, textvariable=sex_value)
    filter_frame.pack()
    
    tk.Label(filter_frame, text="Sample Type:").grid(row=0,column=0, sticky="e")
    type_cb.grid(row=0,column=1)
    type_cb.current(0)
    tk.Label(filter_frame, text="Condition:").grid(row=1, column=0, sticky="e")
    condition_cb.grid(row=1, column=1)
    condition_cb.current(0)
    tk.Label(filter_frame, text="Treatment:").grid(row=2, column=0, sticky="e")
    treatment_cb.grid(row=2, column=1)
    treatment_cb.current(0)
    tk.Label(filter_frame, text="Response:").grid(row=0, column=2, sticky="e")
    response_cb.grid(row=0, column=3)
    response_cb.current(2)
    tk.Label(filter_frame, text="Time From Treatment Start:").grid(row=1, column=2, sticky="e")
    time_cb.grid(row=1, column=3)
    time_cb.current(3)
    tk.Label(filter_frame, text="Sex:").grid(row=2, column=2, sticky="e")
    sex_cb.grid(row=2, column=3)
    sex_cb.current(2)
    #endregion

    #region BUTTON FUNCTIONS
    def hide_frame(frame: ttk.Frame) -> None:
        if frame.winfo_ismapped():
            for child in frame.winfo_children():
                child.destroy()
            frame.pack_forget()

    def __show_plot():
        # params should be in order [sample type, condition, treatment, response, time since treatment, sex]
        responsive_items = [type_value.get(), condition_value.get(), treatment_value.get(), "yes", time_value.get(), sex_value.get()]
        unresponsive_items = [type_value.get(), condition_value.get(), treatment_value.get(), "no", time_value.get(), sex_value.get()]
        response_value.set("")
        full_report = compare_populations(connection, summary_table, responsive_items, unresponsive_items)
        fig = full_report["boxplot"]
        report = full_report["report"]
        # Change the view to show the plot. Delete existing plot if plot frame is already active
        hide_frame(report_frame)
        hide_frame(plot_frame)
        hide_frame(summary_frame)
        
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()
        # creating the Matplotlib toolbar
        toolbar = NavigationToolbar2Tk(canvas, plot_frame)
        toolbar.update()
        # placing the toolbar on the Tkinter window
        canvas.get_tk_widget().pack()

        tk.Label(plot_frame,text=report).pack()

        plot_frame.pack()
         

    def __show_report():
        filters = [type_value.get(), condition_value.get(), treatment_value.get(), response_value.get(), time_value.get(), sex_value.get()]
        subset_values = subset_analysis(connection, filters) # list of tuples. [prj, response, sex]
        # Change the view to show the report. Delete existing report if plot frame is already active
        hide_frame(report_frame)
        hide_frame(plot_frame)
        hide_frame(summary_frame)

        report_title = tk.Label(report_frame, text="Sample count report:")
        report_title.grid(row=0,column=0,columnspan=6)
        prj_count_box=[tk.Text(report_frame,width=8,height=1),tk.Text(report_frame,width=8,height=1),tk.Text(report_frame,width=8,height=1)] # three possible project values
        for i in range(len(prj_count_box)):
            prj_count_box[i].insert(1.0,subset_values[0][i])
            prj_count_box[i].configure(state="disabled")
            tk.Label(report_frame,text=f"Project {i+1}:").grid(row=1,column=(2*(i+1)-1))
            prj_count_box[i].grid(row=1, column=(2*(i+1)))
        resp_count_box=[tk.Text(report_frame,width=8,height=1),tk.Text(report_frame,width=8,height=1)] # two possible responses. The instructions only state to count responders and nonresponders
        for i in range(len(resp_count_box)):
            resp=['Unresponsive','Responsive']
            resp_count_box[i].insert(1.0,subset_values[1][i])
            resp_count_box[i].configure(state="disabled")
            tk.Label(report_frame,text=f"{resp[i]}:").grid(row=2,column=(2*(i+1)-1))
            resp_count_box[i].grid(row=2, column=(2*(i+1)))
        sex_count_box=[tk.Text(report_frame,width=8,height=1),tk.Text(report_frame,width=8,height=1)] # two possible responses.
        for i in range(len(sex_count_box)):
            sex=['Male','Female']
            sex_count_box[i].insert(1.0,subset_values[2][i])
            sex_count_box[i].configure(state="disabled")
            tk.Label(report_frame,text=f"{sex[i]}:").grid(row=3,column=(2*(i+1)-1))
            sex_count_box[i].grid(row=3, column=(2*(i+1)))
        report_frame.pack()
        
    def __show_summary():
        hide_frame(report_frame)
        hide_frame(plot_frame)
        hide_frame(summary_frame)

        
        root.geometry("1200x800+350+30")

        cursor = connection.cursor()

        data = cursor.execute(f"SELECT * FROM {summary_table}")
        column_names = [description[0] for description in cursor.description]
        display_summary = ttk.Treeview(summary_frame,columns=column_names, show="headings")
        for column in column_names:
            display_summary.column(column, width="100")
            display_summary.heading(column, text=column.replace("_"," ").capitalize())
        for row in data.fetchall():
            rounded = tuple([f"{round(x,2)}%" if isinstance(x,float) else x for x in row])
            display_summary.insert("", "end", values=rounded)
        display_summary.pack(fill="both", expand=True)
        summary_frame.pack(fill="both", expand=True)

    #endregion
    button_frame.grid_columnconfigure(0, weight=1, uniform="un1")
    button_frame.grid_columnconfigure(1, weight=1, uniform="un1")
    button_frame.grid_columnconfigure(2, weight=1, uniform="un1")
    tk.Label(button_frame,text="Show boxplots comparing \nresponsive/unresponsive subjects'\ncell counts for above filters").grid(row=0,column=0)
    plot_button = ttk.Button(button_frame, text="Compare Cell Counts", command=__show_plot, width=20)
    tk.Label(button_frame,text="(clears 'Response' field)").grid(row=2,column=0)
    plot_button.grid(row=1,column=0)
    tk.Label(button_frame, text="Show sample counts for\n filters broken up by\nproject, response, and sex.").grid(row=0,column=1)
    subset_button = ttk.Button(button_frame, text="Show Sample Counts", command=__show_report, width=20)
    subset_button.grid(row=1,column=1)
    tk.Label(button_frame,text="Show cell proportion summary").grid(row=0,column=2)
    summary_button = ttk.Button(button_frame, text="Summary", command=__show_summary, width=20)
    summary_button.grid(row=1,column=2)
    
    button_frame.pack(fill="x")



    def on_closing():
        # close the database connection
        connection.close()
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()