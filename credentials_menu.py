import getpass
import re
import webbrowser

import credentials
import fa_menu


def prompt_login():
    username = ""
    while len(username) == 0:
        username = input("Factorio Username: ")
    password = ""
    while len(password) == 0:
        password = getpass.getpass("Factorio Password: ")
    return {"username": username, "password": password}


def sign_in_password_menu():
    while True:
        print(f"Leaving password blank will set username without logging in.")
        c = prompt_login()
        if c["password"] == "":
            break
        try:
            return credentials.sign_in_via_web_api(c["username"], c["password"])
        except credentials.Bad_Credentials as e:
            print(f"Login failed: {e}")
    credentials.sign_in_with_credentials(c["username"], "")
    return 1


def sign_in_with_token_menu():
    username = ""
    while not re.fullmatch(r"[\w.-]+", username):
        username = input("Factorio Username: ")
    token = ""
    while True:
        print(
            "To get your service token, which is required for updates, and many multiplayer functions, please follow the instructions below:"
        )
        print(
            "1. Go to https://factorio.com/profile in your browser. An option to launch is at the end of the instructions."
        )
        print(
            '2. Once logged in and on your profile page, Click the link with the text "reveal".'
        )
        print(
            "3. Once clicked, your token string will be just before the link that will have disappeared. The token consists of a string of 30 numbers and letters between a and f. The text after the token is an invalidate link."
        )
        token = input(
            "4. Enter your token here, or l to open the page for you, or n to skip for now."
        )
        token = token.strip()
        if re.fullmatch(r"[nN][oO]?", token):
            token = ""
            break
        if re.fullmatch(r"[\da-f]{30}", token):
            if credentials.check_credentials({"username": username, "token": token}):
                break
            print(
                "The token entered failed to validate. Please try again, or enter no to skip"
            )
        if re.fullmatch(r"[Ll](aunch)?", token):  # cSpell:disable-line
            webbrowser.open("https://factorio.com/profile")
            continue
        print(
            "The token entered did not match the expected format. Please try again, or enter no to skip"
        )
    credentials.sign_in_with_credentials(username, token)
    return 1


sign_in_menu = {
    "_desc": "Sign in to Factorio to use multiplayer features, and get updates.\nTo just set your username, use the token menu and say no to the token.",
    "Sign in with Password": sign_in_password_menu,
    "Sign in with Token": sign_in_with_token_menu,
}
