import sys
from pathlib import Path

import duckdb
import pytest

# scripts/ isn't part of the installed package; make it importable for
# tests/test_falsification_coverage.py without restructuring it as one.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from displacement_observatory.db import SCHEMA_SQL


@pytest.fixture
def con():
    connection = duckdb.connect(":memory:")
    connection.execute(SCHEMA_SQL)
    yield connection
    connection.close()
