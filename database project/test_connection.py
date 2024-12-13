import psycopg2
from psycopg2 import OperationalError
import pytest

def test_connect_to_opengauss():
    try:
        # 连接到 OpenGauss 数据库
        connection = psycopg2.connect(
            database="postgres",
            user="admin",
            password="admin@123",
            host="172.26.96.208",
            port="7654"
        )

        # 创建游标对象
        cursor = connection.cursor()

        # 执行 SQL 查询
        cursor.execute("SELECT version();")

        # 获取查询结果
        version = cursor.fetchone()
        print("Database Version:", version)
        assert version is not None, "Version should not be None"

        # 关闭游标和连接
        cursor.close()
        connection.close()

    except OperationalError as e:
        print("Error while connecting to OpenGauss:", e)
        pytest.fail(str(e))
