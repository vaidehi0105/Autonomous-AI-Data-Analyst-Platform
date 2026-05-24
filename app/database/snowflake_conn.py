import os

from dotenv import load_dotenv

from sqlalchemy import create_engine

load_dotenv()

connection_string = (
    f"snowflake://"
    f"{os.getenv('SNOWFLAKE_USER')}:"
    f"{os.getenv('SNOWFLAKE_PASSWORD')}@"
    f"{os.getenv('SNOWFLAKE_ACCOUNT')}/"
    f"{os.getenv('SNOWFLAKE_DATABASE')}/"
    f"{os.getenv('SNOWFLAKE_SCHEMA')}"
    f"?warehouse={os.getenv('SNOWFLAKE_WAREHOUSE')}"
    f"&role={os.getenv('SNOWFLAKE_ROLE')}"
)

engine = create_engine(connection_string)

def get_engine():

    return engine