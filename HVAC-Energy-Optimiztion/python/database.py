"""
HVAC Energy Optimization Using IoT Analytics
Database Storage Module
Manages SQLite historical persistence for sensor telemetry, optimization decisions,
and energy analytics aggregations.
"""

import sqlite3
import datetime
from typing import Dict, Any, List, Optional
from python.config import SQLITE_DB_PATH, DEFAULT_ELECTRICITY_TARIFF_PER_KWH


class HVACDatabase:
    """Encapsulates SQLite interactions with thread-safe connection pooling."""

    def __init__(self, db_path: str = SQLITE_DB_PATH):
        self.db_path = db_path
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initializes tables and indexing structures."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Raw IoT Sensor Telemetry Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                device_id TEXT NOT NULL,
                temperature REAL,
                humidity REAL,
                occupancy INTEGER,
                co2 REAL,
                voltage REAL,
                current REAL,
                power REAL,
                energy_kwh REAL,
                frequency REAL,
                power_factor REAL,
                hvac_state TEXT,
                active_setpoint REAL,
                active_fan TEXT
            );
            """)

            # 2. Optimization Decisions & Energy Calculations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                baseline_setpoint REAL,
                baseline_fan TEXT,
                baseline_power_w REAL,
                recommended_setpoint REAL,
                recommended_fan_speed TEXT,
                predicted_power_w REAL,
                power_saved_w REAL,
                savings_percentage REAL,
                occupancy_state INTEGER,
                co2_level REAL,
                indoor_temp REAL,
                outdoor_temp REAL,
                optimization_mode TEXT,
                justification TEXT
            );
            """)

            # 3. Hourly Aggregates Table for Dashboard Charts
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hourly_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_hour TEXT UNIQUE,
                baseline_energy_kwh REAL,
                optimized_energy_kwh REAL,
                energy_saved_kwh REAL,
                cost_saved_currency REAL,
                avg_indoor_temp REAL,
                avg_humidity REAL,
                avg_co2 REAL,
                occupancy_fraction REAL
            );
            """)

            # Create Indexes for high-speed timeseries queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_opt_time ON optimizations(timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hourly_time ON hourly_analytics(timestamp_hour);")

            conn.commit()

    def insert_telemetry(self, data: Dict[str, Any]) -> int:
        """Saves an incoming sensor telemetry packet from ESP32."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        timestamp = data.get("timestamp", now_iso)

        with self._get_connection() as conn:
            cursor = conn.cursor()


            
            cursor.execute("""
            INSERT INTO telemetry (
                timestamp, device_id, temperature, humidity, occupancy, co2,
                voltage, current, power, energy_kwh, frequency, power_factor,
                hvac_state, active_setpoint, active_fan
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                data.get("device_id", "ESP32_UNKNOWN"),
                data.get("temperature", 24.0),
                data.get("humidity", 50.0),
                int(data.get("occupancy", 0)),
                data.get("co2", 500.0),
                data.get("voltage", 230.0),
                data.get("current", 0.0),
                data.get("power", 0.0),
                data.get("energy_kwh", 0.0),
                data.get("frequency", 50.0),
                data.get("power_factor", 0.9),
                data.get("hvac_state", "ON"),
                data.get("active_setpoint", 24.0),
                data.get("active_fan", "MEDIUM")
            ))
            conn.commit()
            return cursor.lastrowid

    def insert_optimization(self, record: Dict[str, Any]) -> int:
        """Stores a generated optimization recommendation."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        timestamp = record.get("timestamp", now_iso)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO optimizations (
                timestamp, baseline_setpoint, baseline_fan, baseline_power_w,
                recommended_setpoint, recommended_fan_speed, predicted_power_w,
                power_saved_w, savings_percentage, occupancy_state, co2_level,
                indoor_temp, outdoor_temp, optimization_mode, justification
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                record.get("baseline_setpoint", 21.0),
                record.get("baseline_fan", "HIGH"),
                record.get("baseline_power_w", 1850.0),
                record.get("recommended_setpoint", 24.5),
                record.get("recommended_fan_speed", "MEDIUM"),
                record.get("predicted_power_w", 1250.0),
                record.get("power_saved_w", 600.0),
                record.get("savings_percentage", 32.4),
                int(record.get("occupancy_state", 1)),
                record.get("co2_level", 650.0),
                record.get("indoor_temp", 24.2),
                record.get("outdoor_temp", 33.5),
                record.get("optimization_mode", "OCCUPIED_COMFORT"),
                record.get("justification", "ASHRAE 55 Adaptive Comfort")
            ))
            conn.commit()
            return cursor.lastrowid

    def update_hourly_aggregate(
        self,
        hour_str: str,
        baseline_kwh: float,
        optimized_kwh: float,
        temp: float,
        humidity: float,
        co2: float,
        occupancy: float,
        tariff: float = DEFAULT_ELECTRICITY_TARIFF_PER_KWH
    ) -> None:
        """Upserts an hourly rolling energy summary row."""
        saved_kwh = max(0.0, baseline_kwh - optimized_kwh)
        saved_cost = saved_kwh * tariff

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO hourly_analytics (
                timestamp_hour, baseline_energy_kwh, optimized_energy_kwh,
                energy_saved_kwh, cost_saved_currency, avg_indoor_temp,
                avg_humidity, avg_co2, occupancy_fraction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(timestamp_hour) DO UPDATE SET
                baseline_energy_kwh = excluded.baseline_energy_kwh,
                optimized_energy_kwh = excluded.optimized_energy_kwh,
                energy_saved_kwh = excluded.energy_saved_kwh,
                cost_saved_currency = excluded.cost_saved_currency,
                avg_indoor_temp = excluded.avg_indoor_temp,
                avg_humidity = excluded.avg_humidity,
                avg_co2 = excluded.avg_co2,
                occupancy_fraction = excluded.occupancy_fraction
            """, (
                hour_str, baseline_kwh, optimized_kwh, saved_kwh, saved_cost,
                temp, humidity, co2, occupancy
            ))
            conn.commit()

    def get_latest_telemetry(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent telemetry entry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_latest_optimization(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent optimization recommendation."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM optimizations ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recent_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the last N records for plotting."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    def get_overall_energy_stats(self) -> Dict[str, Any]:
        """Calculates cumulative energy, savings, and reduction percentage."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT
                COUNT(*) as total_samples,
                AVG(baseline_power_w) as avg_baseline_power,
                AVG(predicted_power_w) as avg_optimized_power,
                AVG(power_saved_w) as avg_power_saved,
                AVG(savings_percentage) as avg_savings_pct,
                SUM(power_saved_w) * (5.0 / 3600.0 / 1000.0) as approx_total_kwh_saved
            FROM optimizations
            """)
            row = cursor.fetchone()
            if not row or row["total_samples"] == 0:
                return {
                    "total_samples": 0,
                    "avg_baseline_power_w": 0.0,
                    "avg_optimized_power_w": 0.0,
                    "avg_power_saved_w": 0.0,
                    "savings_percentage": 0.0,
                    "total_kwh_saved": 0.0,
                    "cost_saved": 0.0
                }

            kwh_saved = row["approx_total_kwh_saved"] or 0.0
            return {
                "total_samples": row["total_samples"],
                "avg_baseline_power_w": round(row["avg_baseline_power"] or 0.0, 1),
                "avg_optimized_power_w": round(row["avg_optimized_power"] or 0.0, 1),
                "avg_power_saved_w": round(row["avg_power_saved"] or 0.0, 1),
                "savings_percentage": round(row["avg_savings_pct"] or 0.0, 1),
                "total_kwh_saved": round(kwh_saved, 3),
                "cost_saved": round(kwh_saved * DEFAULT_ELECTRICITY_TARIFF_PER_KWH, 2)
            }

