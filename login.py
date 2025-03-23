import re
import aiomysql
from os import getenv
from dotenv import load_dotenv

load_dotenv()

DB_HOST = getenv("DB_HOST")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_NAME = getenv("DB_NAME")

logged_in_users = {}

async def connect_db():
    """Establish a connection to the MySQL database."""
    return await aiomysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)

async def is_valid_phone_number(number):
    """Check if the phone number has a valid format."""
    pattern = r"\d{9}"
    return re.match(pattern, number) is not None

async def check_user_in_db(phone_number):
    """Check if the phone number exists in the database."""
    conn = await connect_db()  # Await the connection directly
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT 1 FROM users WHERE phone_number = %s", (phone_number,))
        result = await cursor.fetchone()
    conn.close()  # Manually close the connection
    return result is not None

async def check_password_in_db(phone_number, password):
    """Check if the given password matches the one stored in the database."""
    conn = await connect_db()  # Await the connection directly
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT password FROM users WHERE phone_number = %s", (phone_number,))
        result = await cursor.fetchone()

    conn.close()  # Manually close the connection
    if result:
        stored_password = result[0].strip()
        return stored_password == password.strip()
    
    return False

async def login_user(uid, phone_number):
    """Save the logged-in user in memory."""
    is_logged_in = '1'
    conn = await connect_db()  # Get database connection
    async with conn.cursor() as cursor:
        data = [(phone_number, is_logged_in, uid)]
        await cursor.executemany(
            "INSERT INTO user_status (phone_number, is_logged_in, uid)"
            "values (%s,%s,%s)", data)
        await conn.commit()
    conn.close()  # Close the connection


async def is_user_logged_in(uid):
    """Check if a user ID is already logged in."""
    conn = await connect_db()  # Get database connection
    
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT is_logged_in FROM user_status WHERE uid = %s", (uid,)
        )
        result = await cursor.fetchone()
    
    conn.close()  # Close the connection properly

    return result is not None and result[0] == "1"  # Return True if logged in, False otherwise


async def is_phone_logged_in(phone_number):
    """Check if a phone number is already in use by another user."""
    conn = await connect_db()  # Get database connection
    
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT is_logged_in FROM user_status WHERE phone_number = %s", (phone_number,)
        )
        result = await cursor.fetchone()
    
    conn.close()  # Close the connection properly

    return result is not None and result[0] == '1'  # Return True if logged in, False otherwise


async def get_logged_in_phone(uid):
    """Retrieve the phone number of a logged-in user."""
    conn = await connect_db()  # Get database connection
    
    async with conn.cursor() as cursor:
        await cursor.execute(
            "SELECT phone_number FROM user_status WHERE uid = %s", (uid,)
        )
        result = await cursor.fetchone()
    
    conn.close()  # Close the connection properly

    return result[0] if result else None  # Return phone number if found, otherwise None


async def logout_user(uid):
    """Log out the user."""
    conn = await connect_db()  # Get database connection
    
    async with conn.cursor() as cursor:
        await cursor.execute(
            "DELETE FROM user_status WHERE uid = %s", (uid,)
        )
        await conn.commit()
    conn.close()  # Close the connection properly