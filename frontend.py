import streamlit as st
import pandas as pd
import requests
import json

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
        message = f"The data types of CSV are correct."
        return True, df, message
    except Exception as exception:
        error_message = f"The data types of file '{filename}' were not expected. Details: {exception}"
        return False, None, error_message

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
                        st.success(transform_message)

                        # Rename columns
                        column_names_by_filename = column_names[uploaded_file.name]
                        df = df.rename(columns=column_names_by_filename)
                        st.success("The columns of DataFrame were renamed.")

                        # Display the DataFrame
                        st.write("DataFrame head:")
                        st.write(df)

                        # Convert the DataFrame to JSON
                        json_data = df.to_dict(orient="list")

                        # Write JSON data to the file
                        json_filename = uploaded_file.name.replace(".csv", ".json")
                        with open(json_filename, 'w') as json_file:
                            json.dump(json_data, json_file, indent=4)

                        # Display the generated JSON
                        # st.write("Generated JSON:")
                        # print(json_data)
                        # st.code(json_data, language="json")

                        # Button to send the JSON to an API (you must implement your own API!)
                        if st.button("Insert into Snowflake"):
                            # API URL (replace with your own URL)
                            api_url = "https://your-api.com/endpoint"

                            # Simulate a POST request to the API
                            headers = {'Content-Type': 'application/json'}
                            response = requests.post(api_url, data=json_data, headers=headers)

                            # Check the result of the request
                            if response.status_code == 200:
                                st.success("Data sent successfully to the API.")
                            else:
                                st.error(f"Error sending data to the API. Status code: {response.status_code}")

            except pd.errors.EmptyDataError:
                st.error("Empty CSV file. Please upload a file with data.")
