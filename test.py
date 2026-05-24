import snowflake.connector

conn = snowflake.connector.connect(
    user='VAIDEHI0105',
    password='Venky#2509Amb#',
    account='YZKCDZK-FH46731',
    warehouse='COMPUTE_WH',
    database='AI_ANALYTICS',
    schema='RAW',
    role='ACCOUNTADMIN'
)

cursor = conn.cursor()

cursor.execute("SELECT CURRENT_VERSION()")

print(cursor.fetchone())