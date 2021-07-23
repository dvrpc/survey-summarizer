from __future__ import annotations

import click
import pandas as pd
from pathlib import Path
from datetime import datetime

from src.helpers.ask_user_for_file import ask_user_for_file
from src.helpers.extract_data import (
    count_responses_to_multi_entry_question,
    count_semicolon_list,
    count_the_values,
    get_freeform_text,
)

# This list matches the columns (/sequence) of the CSV file
SURVEY = [
    "Timestamp",
    "What is your view of the transportation network in southeastern Pennsylvania, including  current condition, coverage and services? (Choose as many as apply)",
    "New or extended rail lines",
    "Highway capacity improvements",
    "New roads or road extensions",
    "Improve maintenance, safety and operations of the highway and transit network",
    "Speed up transit / increase service frequency",
    "More trails and bicycle/pedestrian improvements",
    "List any specific projects or improvements that you feel are critical to the region’s future.",
    "Do you support raising state funds across Pennsylvania to pay for transportation needs?",
    "Toll Major Bridges",
    "Tolls on Managed Lanes",
    "Congestion Pricing",
    "Corridor Tolling",
    "Road User Charge",
    "Fees or Tax increases on other non-transportation items",
    "Do you support raising funds at the city or county level in Southeast Pennsylvania to supplement federal and state funds to pay for local transportation needs?",
    "Earned Income Tax",
    "Local Services Tax",
    "Real Estate Transfer Tax",
    "Vehicle Property Tax",
    "Property Tax",
    "Sales Tax",
    "Uber and Lyft fee",
    "Local Gasoline Tax",
    "Do you have other ideas or suggestions about how the region could fund transportation investments?",
    "Is there anything else you would like to share with us regarding the region's transportation and funding?",
    "Who do you represent?: (check all that apply)",
    "Where do you serve?: (check all that apply)",
]

# These are the questions where users give ratings to each option in the list
RADIO_QUESTIONS = {
    "What kind of improvements, if any, would you like to see to improve the transportation network?": {
        "columns": SURVEY[2:8],
        "options": ["Lowest priority", "Medium priority", "Highest priority"],
    },
    SURVEY[9]: {
        "columns": SURVEY[10:16],
        "options": ["I oppose this", "I need to learn more", "I support this"],
    },
    SURVEY[16]: {
        "columns": SURVEY[17:25],
        "options": ["I oppose this", "I need to learn more", "I support this"],
    },
}
# These are the freeform text entries
FREEFORM_TEXT = [SURVEY[8]] + SURVEY[25:27]

# These are the columns that have semicolon-delimited lists
SEMICOLON_LISTS = [SURVEY[1]] + SURVEY[27:]

# These are the columns with a binary Yes/No answer
YES_NO = [SURVEY[9], SURVEY[16]]


@click.command()
@click.option("--filter", "-f", default=None)
def southeast_pa_funding_options(filter):
    """
    Crunch raw CSV into output XLSX file
    """
    print(f"Filtering raw data to {filter=}")
    main(filter)


def crunch_raw_data(
    filepath: Path, place_name_filter: str = None
) -> dict[str, dict[str, pd.DataFrame]]:
    """
    - Read raw CSV file, and replace column names with cleaned up

    Arguments:
        filepath (Path): filepath to survey output
        place_name_filter (str): name of a place to filter on (e.g. 'Philadelphia')

    Returns:
        dict: a dictionary keyed on question type with sub-dictionary that is keyed by
              prompt, with the aggregated pd.DataFrame as the value
    """

    crunched_data = {
        "multi_radio_questions": {},
        "yes_no": {},
        "semicolon_lists": {},
        "freeform_text": {},
    }

    df = pd.read_csv(filepath)

    if place_name_filter:
        print("FILTERING!", place_name_filter)
        # Make sure no NaNs exist
        df["Where do you serve?: (check all that apply)"] = df[
            "Where do you serve?: (check all that apply)"
        ].fillna("no response provided")

        # Filter the dataframe to rows that contain the `place_name_filter`
        df = df[df["Where do you serve?: (check all that apply)"].str.contains(place_name_filter)]

    df.columns = SURVEY

    for colname in YES_NO:
        crunched_data["yes_no"][colname] = count_the_values(df[colname])

    for colname in SEMICOLON_LISTS:
        crunched_data["semicolon_lists"][colname] = count_semicolon_list(df[colname])

    for colname in FREEFORM_TEXT:
        crunched_data["freeform_text"][colname] = get_freeform_text(df[colname])

    for prompt in RADIO_QUESTIONS:
        columns = RADIO_QUESTIONS[prompt]["columns"]
        options = RADIO_QUESTIONS[prompt]["options"]
        crunched_data["multi_radio_questions"][prompt] = count_responses_to_multi_entry_question(
            df, columns, options
        )

    return crunched_data


def write_to_excel(source_file: Path, output_file: Path, place_name_filter: str = None) -> None:
    """
    - Write excel file by crunching raw data into summary tables
    - Add a graph for each summary table

    Arguments:
        source_file (Path): filepath to input CSV file
        output_file (Path): filepath to the resulting .xlsx file
        place_name_filter (str): name of a place to filter on (e.g. 'Philadelphia')

    Returns:
        None: but creates a new output_file with summary tables, graphs, and raw data
    """

    # Create the write object and all necessary font styles
    writer = pd.ExcelWriter(output_file, engine="xlsxwriter")

    format_prompt = writer.book.add_format({"italic": True, "font_size": 14, "color": "blue"})

    # Crunch the raw CSV into summary tables
    data = crunch_raw_data(source_file, place_name_filter)

    # Write a dummy, empty dataframe so that a 'charts' tab gets created
    # We will be inserting graphs into this tab, using data from other tabs
    # that we're about to create

    pd.DataFrame([0]).to_excel(writer, sheet_name="charts")
    chart_sheet = writer.sheets["charts"]

    # ------------------------
    # Write all data as tables
    # ------------------------

    graph_sheet_row_counter = 1

    # *** Yes/No questions ***

    start_row = 1
    pie_col = "A"
    for prompt, df in data["yes_no"].items():
        df.to_excel(writer, sheet_name="yes_no", startrow=start_row)

        sheet = writer.sheets["yes_no"]
        sheet.write(start_row - 1, 0, prompt, format_prompt)

        # Make pie chart
        chart = writer.book.add_chart({"type": "pie"})
        chart.set_size({"width": 350, "height": 350})
        chart.set_title({"name": prompt, "name_font": {"size": 12}})

        chart.add_series(
            {
                "values": ["yes_no", start_row + 1, 1, start_row + 2, 1],
                "categories": ["yes_no", start_row + 1, 0, start_row + 2, 0],
                "points": [
                    {"fill": {"color": "#67a9cf"}},
                    {"fill": {"color": "#ef8a62"}},
                ],
            }
        )

        chart_sheet.insert_chart(pie_col + str(graph_sheet_row_counter), chart)

        start_row += 5
        pie_col = "G"

    graph_sheet_row_counter += 20

    # *** Multi-option radio button questions ***

    bar_fill_colors = {2: "#ece2f0", 3: "#a6bddb", 4: "#1c9099"}
    start_row = 1

    for prompt, df in data["multi_radio_questions"].items():
        # Write the dataframe and prompt header
        df.to_excel(writer, sheet_name="radio", startcol=1, startrow=start_row, index=False)

        sheet = writer.sheets["radio"]
        sheet.write(start_row - 1, 0, prompt, format_prompt)

        # Make grouped bar chart
        chart = writer.book.add_chart({"type": "column"})
        chart.set_size({"width": 800, "height": 350})
        chart.set_title({"name": prompt, "name_font": {"size": 12}})
        chart.set_x_axis(
            {
                "major_gridlines": {"visible": True, "line": {"width": 0.75, "dash_type": "dash"}},
                "num_font": {"size": 9},
            },
        )
        chart.set_y_axis({"major_gridlines": {"visible": False}})

        # Add each series to the chart
        for graph_col in [2, 3, 4]:
            chart.add_series(
                {
                    "values": [
                        "radio",
                        start_row + 1,
                        graph_col,
                        start_row + df.shape[0],
                        graph_col,
                    ],
                    "categories": ["radio", start_row + 1, 1, start_row + df.shape[0], 1],
                    "name": ["radio", start_row, graph_col, start_row, graph_col],
                    "fill": {"color": bar_fill_colors[graph_col]},
                    "data_labels": {"value": True, "position": "inside_end"},
                }
            )
        chart_sheet.insert_chart("A" + str(graph_sheet_row_counter), chart)

        start_row += 3 + df.shape[0]
        graph_sheet_row_counter += 20

    sheet.set_column(1, 1, 70)
    sheet.set_column(2, 5, 18)

    # *** Questions with lists of semicolons ***

    start_row = 1
    for prompt, df in data["semicolon_lists"].items():

        df.to_excel(writer, sheet_name="semicolon", startcol=1, startrow=start_row, index=False)

        sheet = writer.sheets["semicolon"]
        sheet.write(start_row - 1, 0, prompt, format_prompt)

        # Make bar chart
        chart = writer.book.add_chart({"type": "bar"})
        chart.set_size({"width": 800, "height": 350})
        chart.set_title({"name": prompt, "name_font": {"size": 12}})
        chart.set_y_axis(
            {
                "reverse": True,
                "major_gridlines": {"visible": False},
                "num_font": {"size": 8},
            },
        )
        chart.set_x_axis(
            {
                "major_gridlines": {"visible": False},
            },
        )
        chart.set_legend({"none": True})
        chart.add_series(
            {
                "values": ["semicolon", start_row + 1, 2, start_row + df.shape[0], 2],
                "categories": ["semicolon", start_row + 1, 1, start_row + df.shape[0], 1],
                "data_labels": {"value": True, "position": "outside_end"},
                "gap": 50,
            }
        )

        chart_sheet.insert_chart("A" + str(graph_sheet_row_counter), chart)

        start_row += 3 + df.shape[0]
        graph_sheet_row_counter += 20
    sheet.set_column(1, 1, 70)

    # Freeform text questions
    start_row = 1
    for prompt, df in data["freeform_text"].items():
        df.to_excel(
            writer, sheet_name="freeform_text", startrow=start_row, index=False, header=False
        )

        sheet = writer.sheets["freeform_text"]
        sheet.write(start_row - 1, 0, prompt, format_prompt)

        start_row += 3 + df.shape[0]
    sheet.set_column(0, 0, 150)

    # ------------------------------------------------------
    # Write the raw data file into the output as its own tab
    # ------------------------------------------------------

    raw_df = pd.read_csv(source_file)

    raw_df.to_excel(writer, sheet_name="raw_data")

    # ----------
    # Save file!
    # ----------

    writer.save()


def main(place_name_filter: str = None):
    """
    - Ask user for source filepath
    - Create an output filepath with today's date
    - Crunch source file into summary tables, make graphs, and save to .xlsx

    Arguments:
        place_name_filter (str): name of a place to filter on (e.g. 'Philadelphia')
    """

    source_filepath = ask_user_for_file()

    timestamp = str(datetime.now()).split(" ")[0]

    if place_name_filter:
        output_filepath = (
            Path(".") / f"Southeast PA Funding Options - for {place_name_filter} {timestamp}.xlsx"
        )
    else:
        output_filepath = Path(".") / f"Southeast PA Funding Options {timestamp}.xlsx"

    write_to_excel(source_filepath, output_filepath, place_name_filter)


if __name__ == "__main__":
    main()
