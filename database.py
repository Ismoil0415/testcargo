import aiomysql
import re
from datetime import datetime
from aiogram import Bot, types
from os import getenv
from dotenv import load_dotenv
from openpyxl import Workbook
import aiofiles

load_dotenv()
DB_HOST = getenv("DB_HOST")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_NAME = getenv("DB_NAME")

async def connect_db():
    """Establish a connection to the MySQL database."""
    return await aiomysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, db=DB_NAME)

async def check_tracking_status(track_code):
    """Check if the tracking code exists in the cargo table."""
    conn = await connect_db()  # Directly await the connection
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT 1 FROM cargo WHERE tracking_code = %s", (track_code,))
        result = await cursor.fetchone()
    conn.close()  # Close the connection manually
    return result is not None  # Returns True if tracking code exists

async def get_tracking_status(track_code):
    """Get the status of a tracking code from the cargo table."""
    conn = await connect_db()  # Directly await the connection
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT status FROM cargo WHERE tracking_code = %s", (track_code,))
        result = await cursor.fetchone()
    conn.close()  # Close the connection manually
    if result:
        return result[0]  # Return the status
    else:
        return "❌ Статус недоступен"  # Handle empty results properly

async def get_tracking_arriveDate(track_code):
    """Get the arrival date of a tracking code from the cargo table."""
    conn = await connect_db()  # Directly await the connection
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT arrival_date FROM cargo WHERE tracking_code = %s", (track_code,))
        result = await cursor.fetchone()
    conn.close()  # Close the connection manually
    if result:
        return result[0]  # Return the arrival date
    else:
        return "❌ Дата прибытия неизвестна"  # Handle empty results properly
    
async def get_track_link(track_code):
    """Get the arrival date of a tracking code from the cargo table."""
    conn = await connect_db()  # Directly await the connection
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT linked_phone FROM cargo WHERE tracking_code = %s", (track_code,))
        result = await cursor.fetchone()
    conn.close()  # Close the connection manually
    if result[0] == "unlinked":
        return "unlinked"  # Return the arrival date
    else:
        return result[0]  # Handle empty results properly
    
async def link_track_toPhone(track_code: str, phone_number: str, uid: str):
    """Save the logged-in user in memory."""
    conn = await connect_db()  # Get database connection
    async with conn.cursor() as cursor:
        query = "UPDATE cargo SET linked_phone = %s, linked_uid = %s WHERE tracking_code = %s"
        values = (phone_number, uid, track_code)  # Ensure these are strings

        await cursor.execute(query, values)
        await conn.commit()

    await conn.ensure_closed()

async def myOrderList(uid: str):
    """Retrieve order list for the user."""
    conn = await connect_db()  # Get database connection
    async with conn.cursor() as cursor:
        query = "SELECT tracking_code FROM cargo WHERE linked_uid = %s"
        values = (uid,)

        await cursor.execute(query, values)
        result = await cursor.fetchall()  # Await the async call

    await conn.ensure_closed()
    return result  # List of tuples, each containing a single tracking_code

async def get_admin_code(secret_code):
    """Retrieve order list for the user."""
    conn = await connect_db()  # Get database connection
    async with conn.cursor() as cursor:
        await cursor.execute("SELECT secret_code FROM admin")
        result = await cursor.fetchone()
    conn.close()
    if result:
        stored_code = result[0].strip()
        return stored_code == secret_code.strip()
    
    return False

async def save_to_db(data):
    """ Save extracted data into MySQL database asynchronously. """
    try:
        conn = await connect_db()
        async with conn.cursor() as cur:
            # Insert each row into database
            query = "INSERT INTO cargo (tracking_code, status, arrival_date, linked_phone, linked_uid) VALUES (%s, 'active', %s, 'unlinked', 'unlinked')"
            await cur.executemany(query, data)  
        await conn.commit()
        await conn.ensure_closed()
        print("✅ Data successfully saved to MySQL!")
    except Exception as e:
        print(f"❌ Database Error: {e}")

async def save_to_db(data):
    """ Save extracted data into MySQL database asynchronously, avoiding duplicates. """
    try:
        conn = await connect_db()
        async with conn.cursor() as cur:
            # ✅ Query to check if a tracking code with the same arrival_date already exists
            check_query = "SELECT COUNT(*) FROM cargo WHERE tracking_code = %s AND arrival_date = %s"
            insert_query = "INSERT INTO cargo (tracking_code, status, arrival_date, linked_phone, linked_uid) VALUES (%s, 'active', %s, 'unlinked', 'unlinked')"
            
            new_entries = []  # ✅ Store only unique entries to insert
            for tracking_code, arrival_date in data:
                await cur.execute(check_query, (tracking_code, arrival_date))
                (count,) = await cur.fetchone()
                
                if count == 0:  # ✅ If no duplicate found, add to insert list
                    new_entries.append((tracking_code, arrival_date))

            # ✅ Insert only new (non-duplicate) entries
            if new_entries:
                await cur.executemany(insert_query, new_entries)
                await conn.commit()
                print(f"✅ {len(new_entries)} new records saved to MySQL!")
            else:
                print("⚠️ Нет новых записей для вставки. Все трек-коды уже в базе данных.")

        await conn.ensure_closed()

    except Exception as e:
        print(f"❌ Database Error: {e}")

async def save_new_user_db(name: str, phone: str, password: str):
    """ Save user data to MySQL if the phone number is unique. """
    try:
        # ✅ Connect to MySQL
        conn = await connect_db()
        async with conn.cursor() as cur:
            
            # ✅ Check if phone number already exists
            check_query = "SELECT COUNT(*) FROM users WHERE phone_number = %s"
            await cur.execute(check_query, (phone,))
            (count,) = await cur.fetchone()

            if count > 0:
                print(f"⚠️ Phone number {phone} is already registered. Skipping entry.")
                return "⚠️ Этот номер телефона уже зарегистрирован. Пожалуйста, используйте другой."

            # ✅ Insert Новый пользователь data
            insert_query = "INSERT INTO users (Name, phone_number, password) VALUES (%s, %s, %s)"
            await cur.execute(insert_query, (name, phone, password))
            await conn.commit()

            print(f"✅ User {name} saved successfully!")
            return "✅ Регистрация прошла успешно!"

        await conn.ensure_closed()

    except Exception as e:
        print(f"❌ Database Error: {e}")
        return "❌ Ошибка базы данных. Попробуйте еще раз позже."

async def delete_user_db(phone: str):
    """ Удалить пользователя from MySQL by phone number if exists. """
    try:
        # ✅ Connect to MySQL
        conn = await connect_db()
        async with conn.cursor() as cur:

            # ✅ Check if phone number exists
            check_query = "SELECT COUNT(*) FROM users WHERE phone_number = %s"
            await cur.execute(check_query, (phone,))
            (count,) = await cur.fetchone()

            if count == 0:
                print(f"⚠️ Phone number {phone} not found. Cannot delete.")
                return "⚠️ Этот номер телефона не зарегистрирован."

            # ✅ Удалить пользователя
            delete_query = "DELETE FROM users WHERE phone_number = %s"
            await cur.execute(delete_query, (phone,))
            await conn.commit()

            print(f"✅ User with phone {phone} deleted successfully!")
            return "✅ Пользователь успешно удален!"

        await conn.ensure_closed()

    except Exception as e:
        print(f"❌ Database Error: {e}")
        return "❌ Ошибка базы данных. Попробуйте еще раз позже."
    
async def export_user_data(bot: Bot, chat_id: int):
    """ Export 3 Excel files with user and tracking data, then send via Telegram. """
    try:
        conn = await connect_db()
        async with conn.cursor() as cur:

            # ✅ 1️⃣ Query for "All users data in database"
            query_users = """
                SELECT 
                    u.Name, 
                    u.phone_number, 
                    COUNT(c.tracking_code) AS track_count
                FROM users u
                LEFT JOIN cargo c ON u.phone_number = c.linked_phone
                GROUP BY u.Name, u.phone_number
                ORDER BY track_count DESC
            """
            await cur.execute(query_users)
            users_data = await cur.fetchall()

            # ✅ 2️⃣ Query for "Track data (arrived to Tajikistan)"
            query_arrived = """
                SELECT 
                    c.tracking_code, 
                    u.Name, 
                    c.linked_phone 
                FROM cargo c
                LEFT JOIN users u ON c.linked_phone = u.phone_number
                WHERE c.status = 'arrived'
                ORDER BY 
                    CASE 
                        WHEN c.linked_phone = 'unlinked' THEN 1 ELSE 0 
                    END, 
                    c.linked_phone
            """
            await cur.execute(query_arrived)
            arrived_data = await cur.fetchall()

            # ✅ 3️⃣ Query for "List of All Tracks"
            query_all_tracks = """
                SELECT 
                    c.tracking_code, 
                    c.arrival_date, 
                    c.status, 
                    c.linked_phone 
                FROM cargo c
                ORDER BY 
                    c.status DESC, 
                    c.arrival_date ASC
            """
            await cur.execute(query_all_tracks)
            all_tracks_data = await cur.fetchall()

            # ✅ Save to Excel files using openpyxl
            def save_to_excel(data, headers, filename):
                wb = Workbook()
                ws = wb.active
                ws.append(headers)  # Write headers
                for row in data:
                    ws.append(row)
                wb.save(filename)
            
            users_file = "All_users_data.xlsx"
            arrived_file = "Track_data_arrived.xlsx"
            all_tracks_file = "List_of_all_tracks.xlsx"

            save_to_excel(users_data, ["Имя", "Номер телефон", "Количество заказов"], users_file)
            save_to_excel(arrived_data, ["Трек-коды", "Имя", "Номер телефон"], arrived_file)
            save_to_excel(all_tracks_data, ["Трек-коды", "Дата получения", "Статус", "Привязанный номер телефона"], all_tracks_file)

            # ✅ Send all files
            async with aiofiles.open(users_file, "rb") as file1, \
                       aiofiles.open(arrived_file, "rb") as file2, \
                       aiofiles.open(all_tracks_file, "rb") as file3:
                await bot.send_document(chat_id, await file1.read(), caption="📂 Все данные пользователей в базе данных")
                await bot.send_document(chat_id, await file2.read(), caption="📂 Данные по треку (прибыло в Таджикистан)")
                await bot.send_document(chat_id, await file3.read(), caption="📂 Список всех трек-кодов")

        await conn.ensure_closed()

    except Exception as e:
        print(f"❌ Database Error: {e}")
        await bot.send_message(chat_id, "❌ Ошибка базы данных. Попробуйте еще раз позже.")

def validate_date_range(date_text: str):
    """Check if input follows the format DD.MM.YYYY-DD.MM.YYYY"""
    pattern = r"^\d{2}\.\d{2}\.\d{4}-\d{2}\.\d{2}\.\d{4}$"
    return bool(re.fullmatch(pattern, date_text))

def convert_date_format(date_text: str):
    """Convert DD.MM.YYYY to YYYY-MM-DD for MySQL"""
    return datetime.strptime(date_text, "%d.%m.%Y").strftime("%Y-%m-%d")

async def update_tracking_status(date_range: str):
    """Update tracking status to 'arrived' for given date range"""
    try:
        if not validate_date_range(date_range):
            return "❌ Неверный формат! Введите диапазон дат в формате **01.03.2025-01.04.2025**."

        # ✅ Extract and convert dates
        start_date, end_date = date_range.split("-")
        start_date = convert_date_format(start_date)  # Convert to 'YYYY-MM-DD'
        end_date = convert_date_format(end_date)      # Convert to 'YYYY-MM-DD'

        # ✅ Connect to MySQL
        conn = await connect_db()
        async with conn.cursor() as cur:

            # ✅ Fixed Query: Remove `%s` and place date conversion inside SQL
            update_query = f"""
                UPDATE cargo 
                SET status = 'arrived' 
                WHERE STR_TO_DATE(arrival_date, '%d.%m.%Y') 
                      BETWEEN STR_TO_DATE('{start_date}', '%Y-%m-%d') 
                      AND STR_TO_DATE('{end_date}', '%Y-%m-%d')
            """
            await cur.execute(update_query)  # ✅ Correct execution
            affected_rows = cur.rowcount  # Get the number of updated rows
            await conn.commit()

        await conn.ensure_closed()

        return f"✅ Статус обновлен для **{affected_rows}** кодов отслеживания!"

    except aiomysql.Error as e:
        print(f"❌ Database Error: {e}")
        return "❌ Ошибка базы данных. Попробуйте еще раз позже."

async def notify_users_about_arrivals(bot):
    """ Notify users whose tracking codes have arrived in Tajikistan """
    try:
        conn = await connect_db()
        async with conn.cursor() as cur:

            # ✅ Query to get tracking codes with status = 'arrived' and linked to a user
            query = """
                SELECT 
                    c.tracking_code, 
                    c.linked_uid, 
                    u.Name, 
                    u.phone_number
                FROM cargo c
                JOIN users u ON c.linked_phone = u.phone_number
                WHERE c.status = 'arrived' AND c.linked_uid IS NOT NULL
            """
            await cur.execute(query)
            arrived_tracks = await cur.fetchall()

            # ✅ Group tracking codes by `linked_uid`
            users_tracks = {}
            for tracking_code, linked_uid, name, phone_number in arrived_tracks:
                if linked_uid not in users_tracks:
                    users_tracks[linked_uid] = {"name": name, "tracking_codes": []}
                users_tracks[linked_uid]["tracking_codes"].append(tracking_code)

            # ✅ Send notifications to users
            for linked_uid, data in users_tracks.items():
                # Build message
                message = f"Здравствуйте {data['name']}, ваши трек-коды прибыли в Таджикистан.\nСписок прибывших трек-кодов:\n"
                message += "\n".join(data["tracking_codes"])

                # ✅ Send the message to the user
                await bot.send_message(linked_uid, message)

            # ✅ Close connection
            await conn.ensure_closed()

            if users_tracks:
                return "✅ Уведомления отправлены всем пользователям о полученных трек-кодах!"
            else:
                return "ℹ️ Ни для одного пользователя не найдено ни одного трек-кода."

    except Exception as e:
        print(f"❌ Database Error: {e}")
        return "❌ Не удалось отправить уведомления. Попробуйте еще раз позже."
    
async def delete_from_db(data):
    try:
        conn = await connect_db()
        async with conn.cursor() as cur:
            # ✅ Query to check if a tracking code exists
            check_query = "SELECT COUNT(*) FROM cargo WHERE tracking_code = %s"
            delete_query = "DELETE FROM cargo WHERE tracking_code = %s"

            deleted_entries = 0  # Counter for deleted records
            for tracking_code, arrival_date in data:
                await cur.execute(check_query, (tracking_code,))
                (count,) = await cur.fetchone()

                if count > 0:  # ✅ If the tracking code exists, delete it
                    await cur.execute(delete_query, (tracking_code,))
                    deleted_entries += 1

            # ✅ Commit the changes if any records were deleted
            if deleted_entries > 0:
                await conn.commit()
                print(f"✅ {deleted_entries} records deleted from MySQL!")
            else:
                print("⚠️ No matching track codes found for deletion.")

        await conn.ensure_closed()

    except Exception as e:
        print(f"❌ Database Error: {e}")