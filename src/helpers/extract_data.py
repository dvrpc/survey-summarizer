import pandas as pd


def count_semicolon_list(data_series: pd.Series) -> pd.DataFrame:
    """
    - Each entry in the series is a semicolon-delimited list
    - Count the occurances of each unique item within each series entry

    Arguments:
        data_series (pd.Series): single column from a dataframe, with semicolon-delimited data

    Returns:
        pd.DataFrame: dataframe with results
    """
    results = {}
    for entry in data_series.dropna():
        for item in entry.split(";"):
            if item not in results:
                results[item] = 0

            results[item] += 1

    results_as_ordered_list = [[x, results[x]] for x in reversed(sorted(results, key=results.get))]

    return pd.DataFrame(results_as_ordered_list, columns=["text value", "count"])


def count_the_values(data_series: pd.Series) -> pd.DataFrame:
    """
    - Count the number of yes and no responses

    Arguments:
        data_series (pd.Series): single column from a dataframe, with yes/no data

    Returns:
        pd.DataFrame: dataframe with results
    """
    return data_series.value_counts(dropna=True).to_frame("count")


def get_freeform_text(data_series: pd.Series) -> pd.DataFrame:
    """
    - Strip out any blank entries in the series

    Arguments:
        data_series (pd.Series): single column from a dataframe, with freeform text

    Returns:
        pd.DataFrame: dataframe with each non-null entry

    """
    return data_series.dropna().to_frame()


def count_responses_to_multi_entry_question(
    raw_df: pd.DataFrame, list_of_cols_to_summarize: list, list_of_options: list
) -> pd.DataFrame:
    """
    - Run through a set of columns, where the header is the option and each row's value is one
    of a set of possible options (i.e. radio button)

    - This function gets the value counts for each column, and then flattens all results
    from all of the columns into a single resulting dataframe

    Arguments:
        raw_df (pd.DataFrame): dataframe with all of the raw data
        list_of_cols_to_summarize (list): name of each column in raw_df that you want to aggregate
        list_of_options (list): all of the exact text values that users were able to choose from

    Returns:
        pd.DataFrame: dataframe with 'Option' column holding the original column name, and another
                      column for each of the provided list of options
    """

    # Get the number of times each option was selected for each question
    question_results = {}
    for col in list_of_cols_to_summarize:
        count_df = count_the_values(raw_df[col]).reset_index()

        count_df.columns = ["value", "count"]

        question_results[col] = count_df

    # Extract the counts for each of the provided options
    results = []
    for option, option_df in question_results.items():
        option_results = {}
        for possible_option in list_of_options:
            option_results[possible_option] = 0
        for _, row in option_df.iterrows():

            for possible_option in list_of_options:
                if possible_option == row["value"]:
                    option_results[possible_option] = row["count"]

        new_row = [option]

        for _, v in option_results.items():
            new_row.append(v)

        results.append(new_row)

    return pd.DataFrame(results, columns=["Option"] + list_of_options)
