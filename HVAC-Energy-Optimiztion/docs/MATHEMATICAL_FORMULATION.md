# Mathematical Formulation of HVAC Energy Optimization
## Project: HVAC Energy Optimization Using IoT Analytics

---

## 1. Problem Overview & Scope

Heating, Ventilation, and Air Conditioning (HVAC) systems constitute **40% to 60% of total electrical energy consumption** in commercial and residential buildings. Conventional HVAC systems operate on static, non-adaptive thermostatic control (e.g., maintaining a constant 21°C or 22°C with high fan speed regardless of ambient weather conditions, room occupancy, or indoor air quality).

This project designs and implements an intelligent, IoT-enabled **Constrained Multi-Objective Optimization Problem (CMOP)** that dynamically determines:
1. Optimal Temperature Setpoint: $T_{set}^* \in \mathbb{R}$
2. Optimal Evaporator Fan Speed: $S_{fan}^* \in \{\text{LOW}, \text{MEDIUM}, \text{HIGH}\}$

The optimization achieves substantial energy conservation while guaranteeing compliance with:
- **ASHRAE Standard 55**: Thermal Environmental Conditions for Human Occupancy (Predicted Mean Vote $\text{PMV} \in [-0.5, +0.5]$).
- **ASHRAE Standard 62.1**: Ventilation for Acceptable Indoor Air Quality ($CO_2 \le 1000 \text{ ppm}$).

---

## 2. State & Decision Variables

### State Vector $\mathbf{x} \in \mathbb{R}^6$ (Real-time IoT Telemetry):
$$\mathbf{x} = \begin{bmatrix} T_{in} \\ T_{out} \\ RH \\ Occ \\ CO_2 \\ P_{current} \end{bmatrix} = \begin{matrix} \text{Indoor Temperature } (^\circ\text{C}) \\ \text{Outdoor Ambient Temperature } (^\circ\text{C}) \\ \text{Relative Humidity } (\%) \\ \text{Occupancy State } (0 = \text{Empty}, 1 = \text{Occupied}) \\ \text{Carbon Dioxide Concentration } (\text{ppm}) \\ \text{Active Electrical Power } (\text{Watts}) \end{matrix}$$

### Decision Control Vector $\mathbf{u}$ (Actuator Setpoints):
$$\mathbf{u} = \begin{bmatrix} T_{set} \\ S_{fan} \end{bmatrix}$$
Where:
- $T_{set} \in \{22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 27.0, 27.5, 28.0, 28.5, 29.0\}^\circ\text{C}$
- $S_{fan} \in \{\text{LOW}, \text{MEDIUM}, \text{HIGH}\}$

---

## 3. Mathematical Objective Function

The global objective function $\mathcal{J}(\mathbf{u} \mid \mathbf{x})$ is a weighted scalarized multi-objective cost index:

$$\min_{\mathbf{u}} \mathcal{J}(T_{set}, S_{fan} \mid \mathbf{x}) = w_E \cdot \mathcal{F}_{energy}(T_{set}, S_{fan}) + w_C \cdot \mathcal{P}_{comfort}(T_{set}, \mathbf{x}) + w_V \cdot \mathcal{P}_{IAQ}(CO_2, S_{fan})$$

Where:
- $w_E$: Weight assigned to electrical energy conservation ($w_E = 0.60$)
- $w_C$: Weight assigned to thermal comfort maintenance ($w_C = 0.30$)
- $w_V$: Weight assigned to ventilation and indoor air quality ($w_V = 0.10$)
- $w_E + w_C + w_V = 1.0$

---

## 4. Cost Components Formulation

### A. Normalized Energy Cost $\mathcal{F}_{energy}$
$$\mathcal{F}_{energy}(T_{set}, S_{fan}) = \frac{P_{predicted}(T_{set}, S_{fan} \mid \mathbf{x})}{P_{rated}}$$
Where:
- $P_{predicted}$: Electrical power predicted by the Scikit-Learn regression model (Watts).
- $P_{rated}$: Nameplate maximum electrical load of the HVAC compressor system ($2200 \text{ Watts}$).

### B. Thermal Discomfort Penalty Function $\mathcal{P}_{comfort}$
Adhering to Fanger's Predicted Mean Vote (PMV) principle codified in ASHRAE 55:

$$\mathcal{P}_{comfort}(T_{set}, \mathbf{x}) = \begin{cases}
\left(\frac{T_{set} - T_{neutral}}{1.5}\right)^2 + \gamma_{RH} \cdot \max\left(0, \frac{RH - 60}{10}\right) & \text{if } Occ = 1 \\
\beta_{setback} \cdot \max(0, 27.0 - T_{set}) & \text{if } Occ = 0
\end{cases}$$

Where:
- $T_{neutral} = 24.0^\circ\text{C}$ (Standard neutral comfort temperature at 50% RH).
- $\gamma_{RH} = 0.5$ (Humidity discomfort sensitivity coefficient).
- $\beta_{setback} = 2.5$ (Penalty for cooling an unoccupied space below eco-threshold).

### C. Indoor Air Quality (IAQ) Penalty Function $\mathcal{P}_{IAQ}$
Adhering to ASHRAE Standard 62.1:
$$\mathcal{P}_{IAQ}(CO_2, S_{fan}) = \begin{cases}
0 & \text{if } CO_2 < 1000 \text{ ppm} \\
\mu_{vent} \cdot \left(\frac{CO_2 - 1000}{100}\right) & \text{if } CO_2 \ge 1000 \text{ ppm and } S_{fan} \ne \text{HIGH} \\
0 & \text{if } CO_2 \ge 1000 \text{ ppm and } S_{fan} = \text{HIGH}
\end{cases}$$

Where:
- $\mu_{vent} = 4.0$ (High air-quality priority factor).
- When indoor $CO_2$ exceeds $1000 \text{ ppm}$, selecting any fan speed lower than `HIGH` incurs a severe penalty, guaranteeing ventilation override.

---

## 5. System Constraints

1. **Occupied Comfort Envelope Constraint (ASHRAE 55)**:
   $$23.0^\circ\text{C} \le T_{set} \le 25.5^\circ\text{C} \quad \forall \; Occ = 1$$

2. **Unoccupied Energy Setback Constraint**:
   $$27.0^\circ\text{C} \le T_{set} \le 29.5^\circ\text{C} \quad \forall \; Occ = 0$$

3. **Ventilation Guarantee (ASHRAE 62.1)**:
   $$S_{fan} = \text{HIGH} \quad \text{if } CO_2 \ge 1000 \text{ ppm}$$

4. **Compressor Anti-Short-Cycling Dwell Time Constraint**:
   To prevent mechanical fatigue and oil foaming in the compressor motor, consecutive setpoint modifications must respect a minimum dwell interval:
   $$t_{switch} - t_{last\_switch} \ge 180 \text{ seconds (3 minutes)}$$

---

## 6. Building Thermal & Energy Model

The thermal load $Q_{total}$ removed by the HVAC unit is given by:
$$Q_{total} = Q_{envelope} + Q_{internal} + Q_{latent} \quad (\text{kW})$$

1. **Building Envelope Conduction & Infiltration**:
   $$Q_{envelope} = U \cdot A \cdot (T_{out} - T_{set})$$
   Where $U \cdot A \approx 0.14 \text{ kW/}^\circ\text{C}$ for a standard commercial/residential zone.

2. **Internal Thermal Heat Gains**:
   $$Q_{internal} = N_{occupants} \cdot q_{sensible} + Q_{equipment}$$
   Where $q_{sensible} \approx 120 \text{ W/person}$, $Q_{equipment} \approx 150 \text{ W}$.

3. **Latent Heat Dehumidification Load**:
   $$Q_{latent} = \max\left(0, (RH - 50.0) \times 0.005\right) \quad (\text{kW})$$

4. **Outdoor Ambient Coefficient of Performance (COP)**:
   The cooling efficiency degrades linearly as outdoor condensing temperature rises:
   $$COP(T_{out}) = COP_{rated} \cdot \left[1 - \lambda \cdot \max(0, T_{out} - 30.0)\right]$$
   Where $COP_{rated} = 3.4$, $\lambda = 0.016 \text{ /}^\circ\text{C}$.

5. **Electrical Power Demand (Watts)**:
   $$P_{HVAC}(T_{set}, S_{fan}) = \left(\frac{Q_{total}}{COP(T_{out})} \times 1000\right) \cdot \eta_{modulation} + P_{fan}(S_{fan})$$
   Where:
   - $P_{fan}(\text{LOW}) = 45 \text{ W}$, $P_{fan}(\text{MEDIUM}) = 85 \text{ W}$, $P_{fan}(\text{HIGH}) = 140 \text{ W}$.
   - $\eta_{modulation} \in [0.3, 1.2]$ is the inverter compressor throttling ratio.

---

## 7. Energy Conservation Quantifications

### Real-Time Power Reduction:
$$\Delta P = P_{baseline}(21^\circ\text{C}, \text{HIGH}) - P_{optimized}(T_{set}^*, S_{fan}^*) \quad (\text{Watts})$$

### Energy Savings Percentage:
$$\text{Savings } (\%) = \left(\frac{P_{baseline} - P_{optimized}}{P_{baseline}}\right) \times 100\%$$

### Cumulative Energy Conserved (kWh):
$$E_{saved} = \sum_{k=1}^{M} \Delta P_k \times \frac{\Delta t}{3600 \times 1000} \quad (\text{kWh})$$

### Financial Electricity Cost Saved:
$$\text{Cost Saved} = E_{saved} \times \mathcal{C}_{tariff}$$
Where $\mathcal{C}_{tariff} = \$0.15 \text{ per kWh}$ (or ₹$8.50 \text{ per kWh}$).

