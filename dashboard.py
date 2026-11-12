import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="HVAC Energy Optimization",
    page_icon="❄️",
    layout="wide"
)

# ==========================================
# TITLE
# ==========================================

st.title("❄️ HVAC Energy Optimization")
st.subheader("IoT Analytics Dashboard")

st.markdown("---")

# ==========================================
# LOAD DATA
# ==========================================

data = pd.read_csv("hvac_data.csv")

data["Time"] = pd.to_datetime(data["Time"])

# ==========================================
# CALCULATIONS
# ==========================================

avg_temperature = data["Temperature"].mean()
avg_humidity = data["Humidity"].mean()
avg_power = data["Power"].mean()
total_energy = data["Energy"].sum()

# ==========================================
# KPI CARDS
# ==========================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🌡️ Temperature",
        f"{avg_temperature:.2f} °C"
    )

with col2:
    st.metric(
        "💧 Humidity",
        f"{avg_humidity:.2f} %"
    )

with col3:
    st.metric(
        "⚡ Average Power",
        f"{avg_power:.2f} kW"
    )

with col4:
    st.metric(
        "🔋 Total Energy",
        f"{total_energy:.2f} kWh"
    )

st.markdown("---")

# ==========================================
# TEMPERATURE GRAPH
# ==========================================

st.subheader("🌡️ Temperature Monitoring")

temperature_chart = px.line(
    data,
    x="Time",
    y="Temperature",
    markers=True,
    title="Temperature vs Time"
)

st.plotly_chart(
    temperature_chart,
    use_container_width=True
)

# ==========================================
# HUMIDITY + POWER
# ==========================================

col1, col2 = st.columns(2)

with col1:

    humidity_chart = px.line(
        data,
        x="Time",
        y="Humidity",
        markers=True,
        title="Humidity vs Time"
    )

    st.plotly_chart(
        humidity_chart,
        use_container_width=True
    )

with col2:

    power_chart = px.bar(
        data,
        x="Time",
        y="Power",
        title="HVAC Power Consumption"
    )

    st.plotly_chart(
        power_chart,
        use_container_width=True
    )

# ==========================================
# ENERGY OPTIMIZATION
# ==========================================

st.markdown("---")

st.subheader("🔋 Energy Optimization")

original_energy = data["Energy"].sum()

# Simulated optimization
optimized_energy = original_energy * 0.75

energy_saved = original_energy - optimized_energy

saving_percentage = (
    energy_saved / original_energy
) * 100

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Original Energy",
        f"{original_energy:.2f} kWh"
    )

with col2:
    st.metric(
        "Optimized Energy",
        f"{optimized_energy:.2f} kWh"
    )

with col3:
    st.metric(
        "Energy Saving",
        f"{saving_percentage:.1f}%"
    )

# ==========================================
# ALERT
# ==========================================

st.markdown("---")

if avg_temperature > 28:

    st.warning(
        "⚠️ High average temperature detected!"
    )

else:

    st.success(
        "✅ Temperature is within acceptable range."
    )

# ==========================================
# SENSOR DATA
# ==========================================

st.markdown("---")

st.subheader("📊 Sensor Data")

st.dataframe(
    data,
    use_container_width=True
)

# ==========================================
# DOWNLOAD DATA
# ==========================================

csv = data.to_csv(index=False)

st.download_button(
    label="📥 Download HVAC Data",
    data=csv,
    file_name="hvac_data.csv",
    mime="text/csv"
)
# ==========================================
# HVAC CONTROL SIDEBAR
# ==========================================

st.sidebar.title("❄️ HVAC Controls")

setpoint = st.sidebar.slider(
    "Temperature Setpoint (°C)",
    min_value=18,
    max_value=30,
    value=24
)

fan_speed = st.sidebar.slider(
    "Fan Speed (%)",
    min_value=0,
    max_value=100,
    value=60
)

hvac_mode = st.sidebar.selectbox(
    "HVAC Mode",
    ["AUTO", "ON", "OFF"]
)

st.sidebar.markdown("---")

st.sidebar.write("### Current Settings")

st.sidebar.write(
    f"🌡️ Setpoint: **{setpoint} °C**"
)

st.sidebar.write(
    f"🌀 Fan Speed: **{fan_speed}%**"
)

st.sidebar.write(
    f"❄️ Mode: **{hvac_mode}**"
)