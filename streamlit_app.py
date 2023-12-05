# -*- coding: utf-8 -*-

"""
Frontend Streamlit to receive CSV files and then upload them to Snowflake

The Streamlit frontend functions as a web page designed to receive CSV files containing data.
It performs various validation checks, including verifying filenames, ensuring the correct
number of columns, and validating data types for each column. Upon successful validation,
the data undergoes transformation into a pandas DataFrame and is subsequently converted
into JSON format. This JSON data is then sent via an API request to be inserted into
the Snowflake storage service.
"""

import json
import numpy as np
import pandas as pd
import requests
import simplejson
import streamlit as st


# Valid CSV filenames
valid_filenames = ["hired_employees.csv", "departments.csv", "jobs.csv"]

# Desired dtypes for columns of CSV filenames
desired_dtypes = {
    "hired_employees.csv": {
        0: ['int'],
        1: ['object'],
        2: ['object'],
        3: ['int', 'float'],
        4: ['int', 'float']
    },
    "departments.csv": {
        0: ['int'],
        1: ['object']
    },
    "jobs.csv": {
        0: ['int'],
        1: ['object']
    }
}

# Column names for CSV filenames
column_names = {
    "hired_employees.csv": {
        0: 'id',
        1: 'name',
        2: 'datetime',
        3: 'department_id',
        4: 'job_id'
    },
    "departments.csv": {
        0: 'id',
        1: 'department'
    },
    "jobs.csv": {
        0: 'id',
        1: 'job'
    }
}


def transform_df_dtypes(filename, df):
    """
    Transform data types of columns in a DataFrame based on a dictionary of specified data types.

    Parameters:
    - filename: filename of CSV uploaded
    - df: pandas DataFrame of CSV uploaded

    Returns:
    - Transformed DataFrame or None if an error occurs
    """
    desired_dtypes_by_filename = desired_dtypes[filename]
    try:
        for column, dtype_list in desired_dtypes_by_filename.items():
            correct_dtype = True
            for desired_dtype in dtype_list:
                if desired_dtype not in str(df[column].dtype):
                    correct_dtype = False
                    break
                if not correct_dtype:
                    df[column] = df[column].astype(dtype_list[column][0])
        message = "The data types of CSV are correct."
        return True, df, message
    except Exception as exception:
        error_message = f"The data types of file '{filename}' were not expected. Details: {exception}"
        return False, None, error_message


def prepare_elem_df_for_api(table_name, df):
    """
    Prepare a pandas DataFrame for API insertion by converting it to JSON format and handling NaN values.

    Parameters:
    - table_name: Name of the table corresponding to the DataFrame.
    - df: pandas DataFrame to be prepared for API insertion.

    Returns:
    - JSON data formatted for API insertion.
    """
    # Convert the DataFrame to JSON
    json_data = df.to_dict(orient="list")

    # Replace NaN for null
    json_data = json.loads(simplejson.dumps(json_data, ignore_nan=True))

    # Prepare JSON data for API
    json_data_for_api = {
        "table": {
            table_name: json_data
        }
    }
    # json_data_for_api["table"] = {}
    # json_data_for_api["table"][table_name] = json_data
    return json_data_for_api


def is_valid_datetime_column(df, column_name):
    if df.shape[1] == 5:
        try:
            _ = pd.to_datetime(df[column_name])
            return True, ""
        except (ValueError, pd.errors.ParserError) as _:
            error_message = f"The third column has invalid datetime values."
            return False, error_message
    return True, ""


if __name__ == "__main__":
    # Page setup
    st.title("Upload CSV and Insert into Snowflake")

    # Display valid filenames
    st.write("Valid CSV filenames:")
    st.write(valid_filenames)

    # Upload CSV file
    uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])

    # Check if a file was uploaded
    if uploaded_file is not None:
        # Check if the filename is valid
        if uploaded_file.name not in valid_filenames:
            st.error("Invalid filename. Please select a valid CSV filename.")
        else:
            st.success("File uploaded successfully.")
            # Read the CSV file into a pandas DataFrame
            try:
                # Skip header to treat the first row as data if the CSV doesn't have column names
                df = pd.read_csv(uploaded_file, header=None)
                # Validate the number of columns based on the filename
                expected_columns = 5 if uploaded_file.name == "hired_employees.csv" else 2
                if df.shape[1] != expected_columns:
                    st.error(f"Invalid number of columns. Expected {expected_columns} columns.")
                else:
                    # Validate data types of columns based on the filename
                    valid_transformation, df, transform_message = transform_df_dtypes(uploaded_file.name, df)
                    if not valid_transformation:
                        st.error(transform_message)
                    else:
                        # Valid datetime column
                        valid_datetime_colum, valid_datetime_message = is_valid_datetime_column(df, 2)
                        if not valid_datetime_colum:
                            st.error(valid_datetime_message)
                        else:
                            # Rename columns
                            column_names_by_filename = column_names[uploaded_file.name]
                            df = df.rename(columns=column_names_by_filename)

                            # Display the DataFrame
                            st.write("DataFrame head:")
                            st.write(df)

                            # Split the DataFrame in sub DataFrames on 1000 records
                            max_records = 1000
                            splitted_df_list = np.array_split(df, range(max_records, len(df), max_records))

                            # Table name
                            table_name = uploaded_file.name.replace(".csv", "")

                            json_data_for_api_list = []
                            for elem_df in splitted_df_list:
                                json_data_for_api = prepare_elem_df_for_api(table_name, elem_df)
                                json_data_for_api_list.append(json_data_for_api)

                            # TEST: Save JSON data for API
                            # for idx, json_data_for_api in enumerate(json_data_for_api_list):
                            #     json_filename = f"{table_name}_{idx + 1}.json"
                            #     with open(json_filename, 'w') as json_file:
                            #         json.dump(json_data_for_api, json_file, indent=None)

                            # Button to send the JSON to an API
                            if st.button("Insert into Snowflake"):
                                # API URL (replace with your own URL)
                                api_url = "https://l9k2s37rid.execute-api.us-east-1.amazonaws.com/globant-challenge/receive-table-data"
                                # Simulate a POST request to the API
                                headers = {'Content-Type': 'application/json'}
                                # Send all data using the API
                                all_inserted = True
                                final_message = ""
                                with st.spinner('Wait for it...'):
                                    for json_data in json_data_for_api_list:
                                        response = requests.post(api_url, headers=headers, json=json_data)
                                        response_text = json.loads(response.text)
                                        final_message = response_text["message"]
                                        if response_text["status"] == "error":
                                            all_inserted = False
                                            break
                                # Final message
                                if all_inserted:
                                    st.success(final_message)
                                else:
                                    st.error(final_message)
            except pd.errors.EmptyDataError:
                st.error("Empty CSV file. Please upload a file with data.")
