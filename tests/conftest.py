from pathlib import Path
import pytest
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="session", autouse=True)
def prefect_db():
    with prefect_test_harness():
        yield


@pytest.fixture
def base_scripts_folder():
    return Path(__file__).parent / "scripts"
