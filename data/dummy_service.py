#dummy services

def authenticate_user(token):
    return True

def fetch_user_data(user_id):
    db_conn = get_db_connection()
    return {"id": user_id, "name": "Monica"}

def get_db_connection():
    return "Connection Established"

def process_payment(user_id, amount):
    is_valid = authenticate_user("secret_token")
    if is_valid:
        user = fetch_user_data(user_id)
        return f"Charged {amount} to {user['name']}"
    return None