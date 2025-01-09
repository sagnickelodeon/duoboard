import streamlit as st
import pandas as pd

from azure_functions import *

CONTAINER_CLIENT = get_blob_object()

@st.cache_data
def read_data() -> pd.DataFrame:
    """
    Read all user stats from azure and filters out all bots
    """
    with read_csv_from_blob("DUOLINGO_DATA/STAT_FILE_TOTAL.csv", CONTAINER_CLIENT) as file:
        df = pd.read_csv(file)
    df = df[df["is_bot"]=="no"]
    df = df[["name","username","joining_date","streak","total_xp","current_league","weeks_in_league","top_3_finish"]]
    return df


def display(name: str) -> None:
    """
    Renders the UI users will see
    """

    # read the data
    df = read_data()

    unique_joinings = df["joining_date"].unique().tolist()
    unique_leagues = ["Bronze", "Silver", "Gold", "Sapphire", "Ruby", "Emerald", "Amethyst", "Pearl", "Obsidian", "Diamond"]

    user_to_df_column_name = {"Name":"name", "Username":"username", "Streak":"streak", "Total XP":"total_xp", "Top 3 Finish":"top_3_finish"}
    sort_user_view = ["Name", "Username", "Streak", "Total XP","Top 3 Finish"]

    st.sidebar.title(f"Welcome {name}")

    # provide user the option to customize the sort
    sortby = st.sidebar.selectbox("Sort the data by", sort_user_view, index=2)

    # provide the user option to filter joining dates and leagues
    specific_joinings = st.sidebar.multiselect("Select joining months", unique_joinings, default=None)
    specific_leagues = st.sidebar.multiselect("Select league", unique_leagues, default=None)

    # Apply filters to DataFrame
    if specific_joinings:
        df = df[df["joining_date"].isin(specific_joinings)]
    if specific_leagues:
        df = df[df["current_league"].isin(specific_leagues)]
    
    # perform the user specified sort
    df = df.sort_values(by=user_to_df_column_name[sortby], ascending=False)

    # Define the number of entries per page
    entries_per_page = 50

    # Calculate the total number of pages
    total_pages = len(df) // entries_per_page + (len(df) % entries_per_page > 0)

    # page change option
    page = st.sidebar.number_input(
        "Page number",
        min_value=1,
        max_value=total_pages,
        step=1,
        value=1
    )

    # Button to go to a specific page (e.g., Page 6)
    if st.sidebar.button("Logout"):
        st.session_state["authentication_status"] = False
        st.rerun()

    # Determine the start and end indices for the current page
    start_idx = (page - 1) * entries_per_page
    end_idx = start_idx + entries_per_page

    # Slice the dataframe for the current page
    current_page_df = df.iloc[start_idx:end_idx]

    # Display the current page dataframe as a list
    st.title(f"Page {page} of {total_pages}")
    st.table(current_page_df)

if __name__=="__main__":
    pass