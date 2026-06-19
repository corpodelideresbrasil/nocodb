import pandas as pd
import numpy as np
from supertrend_v3_6.core.calculator import calculate_supertrend

def test_calculate_supertrend_basic():
    # Create dummy data
    data = {
        'high': [10, 11, 12, 11, 10, 9, 8, 7, 8, 9, 10],
        'low': [9, 10, 11, 10, 9, 8, 7, 6, 7, 8, 9],
        'close': [9.5, 10.5, 11.5, 10.5, 9.5, 8.5, 7.5, 6.5, 7.5, 8.5, 9.5]
    }
    df = pd.DataFrame(data)

    # Run calculation with small period for testing
    supertrend, direction = calculate_supertrend(df, period=3, multiplier=1.0)

    assert len(supertrend) == len(df)
    assert len(direction) == len(df)
    # Check that initial values are NaN/0
    assert np.isnan(supertrend[0])
    assert direction[0] == 0
