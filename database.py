from sqlalchemy import URL,create_engine
from pathlib import Path
import os
from dotenv import load_dotenv

env_path = Path(__file__).with_name('.env')
load_dotenv(env_path,override=True)

database_url=URL.create(
    drivername='mysql+mysqlconnector',
    username=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT','3306')),
    database=os.getenv('DB_NAME')
)

engine=create_engine(database_url)