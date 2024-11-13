import sqlalchemy
stream = sqlalchemy.create_engine('sqlite:///CryptoStream.db', connect_args={'timeout': 20})