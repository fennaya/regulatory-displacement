import duckdb
import pytest

from displacement_observatory.db import SCHEMA_SQL


@pytest.fixture
def con():
    connection = duckdb.connect(":memory:")
    connection.execute(SCHEMA_SQL)
    yield connection
    connection.close()
