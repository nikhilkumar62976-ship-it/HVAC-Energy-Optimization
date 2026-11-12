import pandas as pd
import numpy as np

np.random.seed(42)

time = pd.date_range(
    start="2026-09-30 00:00",
    periods=24,
    freq="h"
)

temperature = np.random.uniform(22, 32, 24)
humidity = np.random.uniform(40, 70, 24)
power = np.random.uniform(1.5, 4.5, 24)

data = pd.DataFrame({
    "Time": time,
    "Temperature": temperature,
    "Humidity": humidity,
    "Power": power
})

data["Energy"] = data["Power"]

data.to_csv("hvac_data.csv", index=False)

print("HVAC data generated successfully!")
print(data)
