from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.demo import generate_demo
from src.data import make_daily
from src.forecast import run_forecast

@pytest.fixture(scope="session")
def demo():
    return generate_demo()

@pytest.fixture(scope="session")
def demo_result(demo):
    return run_forecast(make_daily(demo), 30, data_id="test", scope="All sales")
