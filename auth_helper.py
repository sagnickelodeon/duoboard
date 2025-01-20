import time

import bcrypt
import yaml
from yaml.loader import SafeLoader
from extra_streamlit_components import CookieManager
import streamlit as st

from azure_functions import *

ONE_MONTH_IN_SECONDS = 30*24*60*60
CONTAINER_CLIENT = get_blob_object()

def hash_password(password: str) -> str:
    """Hashes a plain text password."""
    # Convert the password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate a salt and hash the password
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    
    # Return the hashed password as a string
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verifies a password against a stored hash."""
    # Convert both the password and the stored hash to bytes
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed.encode('utf-8')
    
    # Check if the password matches the hash
    return bcrypt.checkpw(password_bytes, hashed_bytes)

@st.cache_data
def read_config(coming_from:str) -> dict:
    """
    Reads the config.yaml file from azure
    """
    with read_csv_from_blob('config.yaml', CONTAINER_CLIENT) as file:
        config = yaml.load(file, Loader=SafeLoader)
    return config

def update_config(config: dict) -> None:
    """
    Writes updated dictionary to config.yaml in azure
    """
    yaml_data = yaml.dump(config, default_flow_style=False, sort_keys=False)
    write_csv_to_blob("config.yaml", yaml_data, CONTAINER_CLIENT)

def check_input_password(username: str, password: str) -> int:
    """
    Checks if user trying to log in is allowed or not
    """
    config = read_config(coming_from="login")

    # not being in config means user hasn't registered
    if username not in config["authorized"]:
        return -1
    
    # verification returns true means all ok
    if verify_password(password, config["authorized"][username]["password"]):
        return 1
    
    # else incorrect password
    return 0

def check_pre_authorization(username: str) -> bool:
    """
    Checks whether user trying to register is pre-authorized to do so
    """
    config = read_config(coming_from="register")
    return username in config["pre-authorized"]

def add_user(name: str, username: str, hashed_password: str, referral: str) -> bool:
    """
    Adds provided user and details to the config file and removes from pre-authorized list
    """
    try:
        config = read_config(coming_from="register")
        config["authorized"][username] = dict()
        config["authorized"][username]["name"] = name
        config["authorized"][username]["password"] = hashed_password
        config["authorized"][username]["referral"] = referral

        config["pre-authorized"].remove(username)
        update_config(config=config)
        return True
    except Exception as e:
        return False

def get_all_cookie(id: int = 0) -> dict:
    """
    Returns all the available cookies
    """
    cookie_manager = CookieManager(key=f"all_cookie_{id}")
    cookies = cookie_manager.get_all(f"all_cookie_all_{id}")
    return cookies

def get_cookie(id: int = 0) -> dict:
    """
    Returns specifically duoboard cookie
    """
    cookie_manager = CookieManager(key=f"get_cookie_{id}")
    cookies = cookie_manager.get_all(key=f"get_cookie_all_{id}")
    if "duoboard" in cookies:
        return cookies["duoboard"]
    return {}

def set_cookie(cookie_manager: CookieManager, username: str, password: str) -> bool:
    """
    Adds a duoboard cookie to the browser
    """
    try:
        # store username, hash of password, and registering time in cookie
        registering_time = round(time.time())
        hashed_password = hash_password(password)
        cookie_string = f"{username}|{hashed_password}|{registering_time}"
        cookie_manager.set("duoboard", cookie_string, secure=False, same_site="lax")
        return True, hashed_password
    except Exception as e:
        return False, None

def check_cookie(cookie:dict, id) -> bool:
    """
    Check if passed cookie is valid
    """
    if "duoboard" not in cookie:
        return False
    cookie = cookie["duoboard"]

    config = read_config(coming_from="login")
    
    # get individual parts of the cookie
    username, password, registered = cookie.split("|")

    # convert both registration time and current time to int
    current_time = round(time.time())
    registered = int(registered)

    # if cookie is present, that means user already logged in before so no need to check password
    # only check if 30 days has passed
    try:
        if (current_time-registered) <= ONE_MONTH_IN_SECONDS and username in config["authorized"]:
            return True
    except Exception as e:
        return False
    return False

def check_if_registered(username: str) -> bool:
    """
    Check if user has already registered
    """
    config = read_config(coming_from="register")
    return username in config["authorized"]

def get_full_name(cookie: dict) -> str:
    """
    Takes the username and returns the user's name from config
    """
    cookie_string = cookie["duoboard"]
    username, password, validity = cookie_string.split("|")
    config = read_config(coming_from="login")
    return config["authorized"][username]["name"]

if __name__=="__main__":
    pass
