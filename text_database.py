from sqlalchemy import text
from database import engine

with engine.connect() as connection:
    result=connection.execute(text('select database()'))
    print('データベース接続成功:', result.scalar())
