import streamlit as st
import requests
import pandas as pd
from recycle_conn_mysql import MYSQL_RECYCLE
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

sql_connection = f"mysql+pymysql://{MYSQL_RECYCLE.USER_NAME.value}:{MYSQL_RECYCLE.PASSWORD.value}@{MYSQL_RECYCLE.HOST.value}/{MYSQL_RECYCLE.NAME.value}"
recycle_db = create_engine(sql_connection, echo=True)

data = []
with Session(recycle_db) as conn:
    result = conn.execute(text("select prediction, max(score) as score, max(date) as date from predictions group by prediction order by max(date) desc;"), dict())
    for row in result.mappings():
        info = dict()
        info["prediction"] = row["prediction"]
        info["score"] = row["score"]
        info["date"] = row["date"]
        data.append(info)

# Convert data to DataFrame for easier handling
df = pd.DataFrame(data)


# Function to call REST API
def call_rest_api(prediction):
    # Example API URL
    api_url = f"https://dermatechserver.cloud/products/tips/?prompt=how can I recycle {prediction}?"
    response = requests.get(api_url)
    if response.status_code == 200:
        # Assuming the API returns JSON data
        return f"Recycle Advices for {prediction}: \n" + response.json()["tips"]
    else:
        return "Error: Unable to fetch data from the API"


# Displaying the table
st.title("Last Detections:")
st.divider()
for index, row in df.iterrows():
    prediction = row['prediction']
    st.write(f"Prediction: {prediction}.")
    st.write(f"Score: {row['score']}.")
    st.write(f"Date: {row['date']}.")
    if st.button("Get Recycle Advice", key=index):
        # Call REST API and display result
        api_result = call_rest_api(prediction)
        # Assuming the API result is text or dict, modify as needed
        st.sidebar.write(api_result)
    st.divider()
