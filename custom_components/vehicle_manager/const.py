"""Constants for Vehicle Manager HA integration."""

DOMAIN = "vehicle_manager"
VERSION = "0.1.0"

# License tiers
LICENSE_FREE = "free"
LICENSE_PRO = "pro"
BMAC_VERIFY_URL = "https://vehicle-manager-ha.vercel.app/api/verify-license"
FREE_MAX_VEHICLES = 1

# Vehicle types
VEHICLE_TYPE_ICE = "ice"
VEHICLE_TYPE_EV = "ev"
VEHICLE_TYPE_HEV = "hev"
VEHICLE_TYPE_PHEV = "phev"
VEHICLE_TYPE_MOTO_ICE = "moto_ice"
VEHICLE_TYPE_MOTO_EV = "moto_ev"

VEHICLE_TYPES = ["ice","ev","hev","phev","moto_ice","moto_ev"]
VEHICLE_TYPES_CAR = ["ice","ev","hev","phev"]
VEHICLE_TYPES_MOTO = ["moto_ice","moto_ev"]
VEHICLE_TYPES_ICE_ALL = ["ice","hev","phev","moto_ice"]
VEHICLE_TYPES_EV_ALL = ["ev","phev","moto_ev"]

# Counter tuple indexes
IDX_KEY=0; IDX_LABEL_EN=1; IDX_LABEL_RO=2; IDX_DEFAULT_DAYS=3; IDX_DEFAULT_KM=4; IDX_TYPES=5

# Legal documents — FREE tier
COUNTERS_LEGAL = [
    ("rca", "RCA Insurance", "Asigurare RCA", 365, None, VEHICLE_TYPES),
    ("casco", "CASCO Insurance", "Asigurare CASCO", 365, None, VEHICLE_TYPES),
    ("itp", "Vehicle Inspection", "ITP", 365, None, ["ice","hev","phev","moto_ice"]),
    ("itp_ev", "Vehicle Inspection EV", "ITP (EV)", 730, None, ["ev","moto_ev"]),
    ("rovinieta", "Road Vignette", "Rovinieta", 365, None, VEHICLE_TYPES_CAR),
    ("tahograf", "Tachograph", "Tahograf", 730, None, ["ice"]),
    ("driving_license","Driving License", "Permis de conducere", 3650, None, VEHICLE_TYPES),
]

# Engine & Fluids — PRO
COUNTERS_ENGINE = [
    ("oil_change", "Oil & Filter Change", "Schimb ulei+filtru", 365, 15000, ["ice","hev","phev"]),
    ("air_filter", "Engine Air Filter", "Filtru aer motor", 730, 30000, ["ice","hev","phev"]),
    ("fuel_filter", "Fuel Filter", "Filtru combustibil", 730, 30000, ["ice","hev","phev"]),
    ("cabin_filter", "Cabin Air Filter", "Filtru habitaclu", 365, 15000, VEHICLE_TYPES),
    ("spark_plugs", "Spark Plugs", "Bujii", 730, 30000, ["ice","hev"]),
    ("glow_plugs", "Glow Plugs (Diesel)", "Bujii incandescenta", 1460, 60000, ["ice"]),
    ("timing_belt", "Timing Belt/Chain", "Curea/Lant distributie",1825, 60000, ["ice","hev","phev"]),
    ("aux_belt", "Auxiliary Belt", "Curea accesorii", 1095, 60000, ["ice","hev","phev"]),
    ("engine_mounts", "Engine Mounts", "Suporti motor", 1825,100000, ["ice","hev","phev"]),
]

COUNTERS_FLUIDS = [
    ("coolant", "Coolant Flush", "Lichid racire", 1825, 60000, ["ice","hev","phev"]),
    ("brake_fluid", "Brake Fluid", "Lichid frana", 730, None, VEHICLE_TYPES),
    ("power_steering", "Power Steering Fluid", "Lichid directie", 1825, 60000, ["ice","hev"]),
    ("gearbox_oil", "Gearbox Oil", "Ulei cutie viteze", 1825, 60000, ["ice","hev","phev"]),
    ("differential_oil", "Differential Oil", "Ulei diferential", 1825, 60000, ["ice","hev"]),
    ("transfer_case", "Transfer Case Oil", "Ulei cutie transfer", 1825, 60000, ["ice"]),
    ("washer_fluid", "Washer Fluid", "Lichid spalator", 90, None, VEHICLE_TYPES),
]

COUNTERS_BRAKES = [
    ("brake_pads_front", "Front Brake Pads", "Placute frana fata", 730, 30000, ["ice","ev","hev","phev","moto_ice"]),
    ("brake_pads_rear", "Rear Brake Pads", "Placute frana spate", 730, 40000, ["ice","ev","hev","phev","moto_ice"]),
    ("brake_discs_front","Front Brake Discs", "Discuri frana fata", 1825, 80000, VEHICLE_TYPES_CAR),
    ("brake_discs_rear", "Rear Brake Discs", "Discuri frana spate", 1825,100000, VEHICLE_TYPES_CAR),
    ("brake_caliper_f", "Front Brake Caliper", "Etrier fata", 3650,150000, VEHICLE_TYPES_CAR),
    ("brake_caliper_r", "Rear Brake Caliper", "Etrier spate", 3650,150000, VEHICLE_TYPES_CAR),
    ("handbrake_cable", "Handbrake Cable", "Cablu frana mana", 1825, 80000, ["ice","hev","phev"]),
]

COUNTERS_SUSPENSION = [
    ("shock_absorbers", "Shock Absorbers", "Amortizoare", 1825, 80000, VEHICLE_TYPES_CAR),
    ("tie_rods", "Tie Rods", "Cap de bara", 1825, 80000, VEHICLE_TYPES_CAR),
    ("ball_joints", "Ball Joints", "Pivot/Articulatii", 1825, 80000, VEHICLE_TYPES_CAR),
    ("cv_joints", "CV Joints/Axle", "Planetare", 3650,100000, VEHICLE_TYPES_CAR),
    ("stabilizer_links", "Stabilizer Bar Links", "Bara stabilizatoare", 1825, 80000, VEHICLE_TYPES_CAR),
    ("wheel_bearings", "Wheel Bearings", "Rulmenti roti", 3650,100000, VEHICLE_TYPES_CAR),
]

COUNTERS_TYRES = [
    ("tyre_rotation", "Tyre Rotation", "Rotatie anvelope", 180, 10000, VEHICLE_TYPES),
    ("tyre_balancing", "Tyre Balancing", "Echilibrare anvelope", 365, 15000, VEHICLE_TYPES),
    ("wheel_alignment", "Wheel Alignment", "Geometrie roti", 365, 20000, VEHICLE_TYPES),
    ("tyres_summer", "Summer Tyres Replace", "Anvelope vara", 1825, 40000, VEHICLE_TYPES),
    ("tyres_winter", "Winter Tyres Replace", "Anvelope iarna", 1825, 40000, VEHICLE_TYPES),
    ("tyre_pressure", "Tyre Pressure Check", "Verificare presiune", 30, None, VEHICLE_TYPES),
]

COUNTERS_ELECTRICAL = [
    ("battery_12v", "12V Battery", "Baterie 12V", 1825, None, VEHICLE_TYPES),
    ("alternator", "Alternator", "Alternator", 3650,150000, ["ice","hev","phev"]),
    ("obd_diagnostic", "OBD Diagnostic", "Diagnostic OBD", 365, None, VEHICLE_TYPES),
]

COUNTERS_EV = [
    ("hv_battery_health","HV Battery Health", "Sanatate baterie HV", 365, None, VEHICLE_TYPES_EV_ALL),
    ("battery_coolant", "Battery Coolant Flush", "Lichid racire baterie", 1825, None, ["ev","phev"]),
    ("bms_calibration", "BMS Calibration", "Calibrare BMS", 365, None, VEHICLE_TYPES_EV_ALL),
    ("ota_update", "OTA Firmware Update", "Update firmware OTA", 90, None, VEHICLE_TYPES_EV_ALL),
    ("ev_cooling_pumps", "Cooling Pump Check", "Pompe racire EV", 1825, None, ["ev","phev"]),
    ("ev_diagnostic", "EV System Diagnostic", "Diagnostic EV", 365, None, VEHICLE_TYPES_EV_ALL),
    ("ev_brake_fluid", "Brake Fluid (EV annual)","Lichid frana EV", 365, None, VEHICLE_TYPES_EV_ALL),
]

COUNTERS_MOTO = [
    ("moto_oil", "Moto Oil & Filter", "Ulei+filtru moto", 180, 6000, ["moto_ice"]),
    ("moto_air_filter", "Moto Air Filter", "Filtru aer moto", 365, 15000, ["moto_ice"]),
    ("moto_spark_plugs", "Moto Spark Plugs", "Bujii moto", 730, 12000, ["moto_ice"]),
    ("chain_lube", "Chain Clean & Lube", "Lant curatare+ungere", 30, 800, ["moto_ice"]),
    ("chain_replace", "Chain & Sprockets", "Lant + Pinioane", 730, 20000, ["moto_ice"]),
    ("belt_drive", "Belt Drive", "Curea transmisie", 365, 20000, VEHICLE_TYPES_MOTO),
    ("fork_oil", "Fork Oil & Seals", "Ulei furca + etansari", 730, 20000, VEHICLE_TYPES_MOTO),
    ("rear_shock", "Rear Shock Inspection", "Amortizor spate moto", 1825, 40000, VEHICLE_TYPES_MOTO),
    ("moto_tyre_front", "Front Tyre", "Anvelopa fata moto", 730, 15000, VEHICLE_TYPES_MOTO),
    ("moto_tyre_rear", "Rear Tyre", "Anvelopa spate moto", 365, 10000, VEHICLE_TYPES_MOTO),
    ("moto_brake_f", "Front Brake Pads", "Placute fata moto", 365, 10000, VEHICLE_TYPES_MOTO),
    ("moto_brake_r", "Rear Brake Pads", "Placute spate moto", 365, 12000, VEHICLE_TYPES_MOTO),
    ("moto_brake_fluid", "Moto Brake Fluid", "Lichid frana moto", 730, None, VEHICLE_TYPES_MOTO),
    ("moto_clutch_fluid","Clutch Fluid", "Lichid ambreiaj", 730, None, ["moto_ice"]),
    ("moto_cables", "Cables & Controls", "Cabluri ambreiaj/accel", 365, None, ["moto_ice"]),
    ("moto_fasteners", "Fastener Check", "Verificare suruburi", 180, None, VEHICLE_TYPES_MOTO),
    ("steering_bearings","Steering Head Bearings", "Rulmenti directie moto",1825, 40000, VEHICLE_TYPES_MOTO),
    ("moto_battery", "Moto Battery", "Baterie moto", 365, None, VEHICLE_TYPES_MOTO),
]

ALL_COUNTERS = (
    COUNTERS_LEGAL + COUNTERS_ENGINE + COUNTERS_FLUIDS + COUNTERS_BRAKES
    + COUNTERS_SUSPENSION + COUNTERS_TYRES + COUNTERS_ELECTRICAL
    + COUNTERS_EV + COUNTERS_MOTO
)

# Status
STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_EXPIRED = "expired"
STATUS_UNKNOWN = "unknown"
WARNING_DAYS_DEFAULT = 30

# Entity attributes
ATTR_DAYS_REMAINING = "days_remaining"
ATTR_KM_REMAINING = "km_remaining"
ATTR_EXPIRY_DATE = "expiry_date"
ATTR_START_DATE = "start_date"
ATTR_LAST_DONE_DATE = "last_done_date"
ATTR_LAST_DONE_KM = "last_done_km"
ATTR_NEXT_DUE_DATE = "next_due_date"
ATTR_NEXT_DUE_KM = "next_due_km"
ATTR_PROGRESS_PCT = "progress_pct"
ATTR_LICENSE_TYPE = "license_type"
ATTR_VEHICLE_TYPE = "vehicle_type"

# Config flow keys
CONF_VEHICLE_NAME = "vehicle_name"
CONF_VEHICLE_TYPE = "vehicle_type"
CONF_LICENSE_PLATE = "license_plate"
CONF_VIN = "vin"
CONF_ODOMETER_ENTITY = "odometer_entity"
CONF_UNIT = "unit"
CONF_LICENSE_KEY = "license_key"
CONF_WARNING_DAYS = "warning_days"

UNIT_KM = "km"
UNIT_MILES = "mi"

# Notification settings
CONF_NOTIFICATIONS_ENABLED = "notifications_enabled"
CONF_DISMISSED_NOTIFICATIONS = "dismissed_notifications"
NOTIFICATIONS_ENABLED_DEFAULT = True
