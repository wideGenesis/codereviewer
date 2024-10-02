import os

from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv(dotenv_path='settings/.env')


class RedisConfig(BaseModel):
    # ########## Database settings ########## #
    REDIS_HOST: str = os.environ.get("REDIS_HOST", "192.168.1.19")
    REDIS_PORT: str = os.environ.get("REDIS_PORT", "6379")
    REDIS_DB: str = os.environ.get("REDIS_DB", "0")



class AzureDatabaseConfig(BaseModel):
    DB_IS_MSI_CONNECT: bool = False
    # ########## Database settings ########## #
    DB_DRIVER: str = "{ODBC Driver 18 for SQL Server}"
    DB_HOST: str = os.environ.get("DB_HOST")
    DB_NAME: str = os.environ.get("DB_NAME")
    DB_PORT: str = "1433"
    DB_USER: str = os.environ.get("DB_USER", None)
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", None)
    AZURE_CLIENT_ID: str = os.environ.get("AZURE_CLIENT_ID", None)
    AZURE_TENANT_ID: str = os.environ.get("AZURE_TENANT_ID", None)
    SQL_COPT_SS_ACCESS_TOKEN: int = 1256  # As defined in msodbcsql.h
    SQL_ALCHEMY_BASE_CONN_STR: str = (
        f"mssql+pyodbc:///?odbc_connect="
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_HOST};"
        f"DATABASE={DB_NAME};"
    )

    if DB_IS_MSI_CONNECT:
        SQL_ALCHEMY_CONN_STR: str = SQL_ALCHEMY_BASE_CONN_STR
    else:
        SQL_ALCHEMY_CONN_STR: str = (
                SQL_ALCHEMY_BASE_CONN_STR +
                f"UID={DB_USER};"
                f"PWD={DB_PASSWORD};"
                f"Connection Timeout=30"
        )

    SQL_ALCHEMY_ASYNC_CONN_STR: str = (
        f"mssql+aioodbc:///?odbc_connect="
        f"DRIVER={DB_DRIVER};"
        f"SERVER={DB_HOST};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"Connection Timeout=30"
    )

DATABASE_CONF = AzureDatabaseConfig()

class MysqlDatabaseConfig(BaseModel):
    DB_HOST: str = os.environ.get("DB_HOST", "192.168.1.19")
    DB_NAME: str = os.environ.get("DB_NAME", "codereviewer")
    DB_PORT: str = "3306"
    DB_USER: str = os.environ.get("DB_USER", "general")
    DB_PASSWORD: str = os.environ.get("DB_PASSWORD", "General2035")
    ASYNC_DATABASE_URL: str = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SYNC_DATABASE_URL: str = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class AzureStorageConfig(BaseModel):
    STORAGE_ACCOUNT_NAME: str = os.environ.get("STORAGE_ACCOUNT_NAME")
    STORAGE_CONNECTION_STRING: str = os.environ.get("STORAGE_CONNECTION_STRING")
    STORAGE_KEY: str = os.environ.get("STORAGE_KEY")


class AppInsightsConfig(BaseModel):
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = os.environ.get(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
