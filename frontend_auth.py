import time
import re

import streamlit as st
from extra_streamlit_components import CookieManager

from frontend_streamlit import *
from auth_helper import *

# set global configs
st.set_page_config(layout="wide", page_title="Duoboard",menu_items={'About': "# This is a header. This is an *extremely* cool app!"},page_icon=":owl:")
cookie_manager = CookieManager()
VALID_PASSWORD_PATTERN = r"^[a-zA-Z0-9]+$"

def register_user() -> None:
    """
    Checks and registers any pre-authorized users
    """

    # Registration form
    st.title("User Registration")

    with st.form("register_form"):
        st.header("Register")

        # Input fields
        full_name = st.text_input("Full Name", placeholder="Enter your full name")
        username = st.text_input("Duolingo username", placeholder="Choose a username")
        password = st.text_input("Password", type="password", placeholder="Enter a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")

        # Dropdown or radio button for referral source
        referral_sources = ["Friend", "Social Media", "Search Engine", "Advertisement", "Other"]
        referral = st.selectbox("Where did you hear about us?", options=referral_sources, index=0)

        # Submit button
        submit = st.form_submit_button("Register")

    # Handle form submission
    if submit:
        # if some field is empty
        if not full_name or not username or not password or not confirm_password:
            st.error("Please fill out all required fields.")
        # if entered password and confirm passwords mismatch
        elif password != confirm_password:
            st.error("Passwords do not match. Please try again.")
        # if user is already registered don't register again
        elif check_if_registered(username=username):
            st.error("User already registered. Please log in.")
        # password pattern should match
        elif not bool(re.match(VALID_PASSWORD_PATTERN, password)):
            st.error("Password contains illegal characters. It should only contain alphanumeric characters.")
        else:
            # user should be pre-authorized by admin
            if check_pre_authorization(username=username):
                # set cookie for user for password less login
                result, hashed_password = set_cookie(cookie_manager, username=username, password=password)
                if result:
                    # add the user to registered
                    if add_user(full_name, username, hashed_password, referral):
                        st.success(f"Registration successful! Welcome, {full_name}! Please go back to home and log in.")
                        time.sleep(3)
                    else:
                        st.error("Registration failed. Please try again.")
                else:
                    st.error("Registration failed. Please try again.")
                st.stop()
            else:
                st.error("User is not pre-authorized to register.")

def login_user():
    """
    Renders a login form for already registered user
    """
    # Login form
    st.title("User Login")
    all_cookie = {}

    # if user logged in before there should be a cookie present
    if st.session_state["authentication_status"] is None:
        all_cookie = get_all_cookie(st.session_state["login_count"])
    
    # if cookie is present
    if all_cookie:
        # check cookie is valid
        if check_cookie(all_cookie, st.session_state["login_count"]):

            # if valid, log user in
            st.session_state["authentication_status"] = True
            name = get_full_name(all_cookie)
            st.session_state["name"] = name
            st.rerun()

    # if no cookie or invalid cookie render login form
    with st.form("login_form"):
        st.header("Login")

        # Input fields
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        # Submit button
        login = st.form_submit_button("Login")

    # Forgot password button (outside the form)
    if st.button("Forgot Password?"):
        st.warning("For password recovery, please drop a mail to duoboard.help@gmail.com")

    # Handle form submission
    if login:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            # check if user entered password is matching with saved password
            password_check = check_input_password(username, password)

            # -1: user not registered
            # 0 : user registered but passwords do not match
            # 1 : all ok
            if password_check == -1:
                st.error("User not registered.")
            elif password_check == 0:
                st.error("Incorrect password.")
            else:
                # set cookie for future passwordless login
                result, hashed_password = set_cookie(cookie_manager, username=username, password=password)
                if result:

                    # log the user in
                    all_cookie = {"duoboard":f"{username}|user_logged_in|{round(time.time())}"}
                    name = get_full_name(all_cookie)
                    st.session_state["name"] = name
                    st.session_state["authentication_status"] = True
                    st.rerun()

def display_cookie_policy() -> None:
    st.markdown("""# Cookie Policy\n**Effective Date:** 10th January, 2025 \n\n **This Cookie Policy explains how cookies are used in Duoboard and what information is collected during your use of the app.**\n## What are Cookies?\nCookies are small text files stored on your device to enhance your experience while using the app. They help us provide essential functionality and improve your overall experience.\n## How We Use Cookies  
We use cookies strictly for essential purposes, such as:\n- Maintaining your login session.\n- Ensuring smooth operation of the app.\n## What Information is Stored?  
We do not store any personal information through cookies. The only data we process includes:\n- Your Duolingo username.\n- A hashed version of your Duoboard password.\n- The time you logged in.\n\nThis information is necessary to manage your session securely and effectively.\n## Third-Party Cookies\nWe do not use any third-party cookies or tracking technologies.\n## Managing Cookies\nYou can disable cookies in your browser settings; however, please note that this may affect the functionality of the app, including your ability to stay logged in.\n## Changes to this Policy  
We may update this Cookie Policy from time to time. Changes will be posted on this page, and the effective date will be updated accordingly.\n## Contact Us  
If you have any questions or concerns about this Cookie Policy, please contact us at duoboard.help@gmail.com.\n### By using Duoboard, you consent to the use of cookies as described in this policy.
""")
    st.session_state.view="home"
    if st.button("Go back"):
        st.rerun()

def display_faq():
    st.markdown('''# FAQ\n### 1. What is Duoboard for?\nDuoboard is a global leaderboard that tracks the progress and ranking of pre-authorized Duolingo users based on their activity, achievements, and language learning progress.\n### 2. Who can access this leaderboard?\nThe leaderboard is only accessible to users who have been pre-authorized by the developer. If you are not on the list, you will not be able to view or participate.\n### 3. How can I get authorized to join the leaderboard?\nAuthorization is handled manually by the developer. If you think you should be part of the leaderboard, please reach out directly to the developer with your details at duoboard.help@gmail.com.\n### 4. How often is the leaderboard updated?\nThe leaderboard is refreshed periodically to reflect the latest activity and scores of the participants. Due to technical limitations and a large user base, daily updates for everyone are not feasible. However, if you're a registered user, your data will be refreshed daily.\n### 5. What metrics are used to rank users?\nUsers are ranked based on a combination of metrics such as XP earned, streak maintenance, league, and other Duolingo activity data.\n### 6. Why is my score not updated?\nIf you are registered and your score hasn't been updated, please contact the developer.\n### 7. Can I opt out of the leaderboard?\nYes, if you prefer not to appear on the leaderboard, please notify the developer, and your data will be removed from the display.\n### 8. Is my data safe?\nAbsolutely. The data displayed is used only for ranking purposes on this private leaderboard. No personal information other than those available in your public duolingo account is collected and none are shared with any third party.\n### 9. Can I suggest features or changes to the leaderboard?\nYes, feedback is always welcome! Feel free to share your suggestions directly with the developer.\n### 10. I found an error in my data. What should I do?\nIf you notice any discrepancies in your data, please contact the developer with specific details so the issue can be investigated and resolved.\n\n## Contact\nEmail: duoboard.help@gmail.com''')

def handle_login():
    """
    Handles all of login, register, and display data
    """

    # set some state variables if this is the dirst execution
    if "login_count" not in st.session_state:
        st.session_state["login_count"] = 0
        st.session_state["authentication_status"] = None

    # if authentication_status is True, user is logged in
    if st.session_state["authentication_status"]:
        name = st.session_state["name"]
        display(name)
    else:
        # Use session state to determine the active view
        if "view" not in st.session_state:
            st.session_state.view = "home"

        # decide what the user clicked
        if st.session_state.view == "home":
            st.title("Welcome to Duoboard!")
            if st.button("Existing user? Sign in"):
                st.session_state.view = "login"
                st.rerun()
            if st.button("New user? Sign up"):
                st.session_state.view = "register"
                st.rerun()
            display_faq()
            if st.button("View our cookie policy"):
                st.session_state.view="cookie"
                st.rerun()
        
        elif st.session_state.view == "cookie":
            display_cookie_policy()

        elif st.session_state.view == "login":
            login_user()
            if st.button("Back to Home"):
                st.session_state.view = "home"

        elif st.session_state.view == "register":
            register_user()
            if st.button("Back to Home"):
                st.session_state.view = "home"
                st.rerun()

if __name__ == "__main__":
    handle_login()
