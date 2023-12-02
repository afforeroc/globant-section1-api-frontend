import streamlit as st
import pandas as pd
import requests

def format_json_data(json_data):
    # Format the JSON data for the API
    formatted_json_data = {
        "id": json_data.get("id", []),
        "name": json_data.get("name", []),
        "datetime": json_data.get("datetime", []),
        "department_id": json_data.get("department_id", []),
        "job_id": json_data.get("job_id", [])
    }
    return formatted_json_data

# Page setup
st.title("Upload CSV and Send to API")

# Upload CSV file
uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])

# Check if a file was uploaded
if uploaded_file is not None:
    st.success("File uploaded successfully.")

    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(uploaded_file)
    # print(df)

    # Display the DataFrame
    st.write("DataFrame:")
    st.write(df)

    # Convert the DataFrame to JSON
    json_data = df.to_dict(orient="list")
    formatted_json_data = format_json_data(json_data)
    # print(json_data)

    # Display the generated JSON
    st.write("Generated JSON:")
    st.code(json_data, language="json")

    # Button to send the JSON to an API (you must implement your own API!)
    if st.button("Send to API"):
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
