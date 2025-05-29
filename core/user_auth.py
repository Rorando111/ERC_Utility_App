import json
import os
import hashlib
from core.email_utils import generate_code, send_verification_email

USER_FILE = "users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def signup(username, password, email):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    
    users[username] = {
        "password": hash_password(password),
        "email": email
    }
    save_users(users)
    return True, "Signup successful."

def login(username, password):
    users = load_users()
    if username in users and users[username]["password"] == hash_password(password):
        code = generate_code()
        email_sent = send_verification_email(users[username]["email"], code, username)
        if email_sent:
            return True, code
        else:
            return False, "2FA code could not be sent. Check email setup."
    return False, "Invalid username or password."
