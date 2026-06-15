# 🚗 Vehicle Manager for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/albuster-prog/vehicle-manager-ha.svg)](https://github.com/albuster-prog/vehicle-manager-ha/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Pro%20License-yellow.svg)](https://www.buymeacoffee.com/vehiclemanagerha)

> **The most complete vehicle maintenance tracker for Home Assistant.**  
> Track legal documents (RCA, CASCO, ITP, Vignette) and 60+ maintenance items for ICE cars, Electric Vehicles, Hybrids and Motorcycles — with proper status logic, HA sensors, warnings and automations.

---

## ✨ Features

### 🆓 Free Tier (1 vehicle)
- ✅ RCA Insurance — days remaining, expiry date, status
- ✅ CASCO Insurance — days remaining, expiry date, status
- ✅ ITP / Vehicle Inspection — status tracking
- ✅ Road Vignette (Rovinietă) — days remaining
- ✅ Driving License expiry reminder
- ✅ Tachograph (for freight vehicles)
- ✅ Binary sensor warnings (ON when expiring soon or expired)
- ✅ Status: **OK / Warning / Expired / Not Configured**
- ✅ Correct status logic: start_date in the future = still VALID *(fixes the Car Manager România bug)*

### 💎 Pro Tier (unlimited vehicles — Lifetime License)
Everything in Free, plus:
- ✅ **Unlimited vehicles**
- ✅ **60+ maintenance counters** per vehicle (see full list below)
- ✅ Per-km and per-time tracking (whichever exhausts first)
- ✅ "Mark as Done" button per counter (saves today's date + current odometer)
- ✅ Odometer integration (reads km from any HA sensor)
- ✅ Progress % attribute for dashboard cards
- ✅ Days remaining + km remaining attributes
- ✅ Automatic warning at configurable threshold (default: 30 days)

---

## 🔧 Supported Vehicle Types

| Type | Code | Description |
|------|------|-------------|
| 🚗 ICE Car | `ice` | Gasoline / Diesel |
| ⚡ EV Car | `ev` | Electric Vehicle |
| 🔋 Hybrid | `hev` | Hybrid (HEV) |
| 🔌 Plug-in Hybrid | `phev` | Plug-in Hybrid (PHEV) |
| 🏍️ Motorcycle ICE | `moto_ice` | Motorcycle — gasoline |
| ⚡ Motorcycle EV | `moto_ev` | Motorcycle — electric |

---

## 📋 Full Maintenance Counter List (Pro)

### 📄 Legal Documents (Free + Pro)
RCA · CASCO · ITP · ITP EV · Road Vignette · Tachograph · Driving License

### 🔧 Engine (ICE / HEV / PHEV)
Oil & Filter · Engine Air Filter · Fuel Filter · Cabin Air Filter · Spark Plugs · Glow Plugs · Timing Belt/Chain · Auxiliary Belt · Engine Mounts

### 💧 Fluids
Coolant · Brake Fluid · Power Steering Fluid · Gearbox Oil · Differential Oil · Transfer Case Oil · Washer Fluid

### 🛑 Brakes
Front/Rear Brake Pads · Front/Rear Brake Discs · Front/Rear Brake Calipers · Handbrake Cable

### 🔩 Suspension & Steering
Shock Absorbers · Tie Rods · Ball Joints · CV Joints/Axle · Stabilizer Bar Links · Wheel Bearings

### 🏎️ Tyres
Tyre Rotation · Tyre Balancing · Wheel Alignment · Summer Tyres · Winter Tyres · Tyre Pressure

### ⚡ Electrical
12V Battery · Alternator · OBD Diagnostic

### 🔋 EV-Specific
HV Battery Health · Battery Coolant Flush · BMS Calibration · OTA Firmware Update · EV Cooling Pump · EV System Diagnostic · Brake Fluid (annual)

### 🏍️ Motorcycle
Moto Oil & Filter · Air Filter · Spark Plugs · Chain Clean & Lube · Chain & Sprockets · Belt Drive · Fork Oil & Seals · Rear Shock · Front/Rear Tyres · Front/Rear Brake Pads · Brake Fluid · Clutch Fluid · Cables & Controls · Fastener Check · Steering Head Bearings · Battery

---

## 📦 Installation

### Via HACS (recommended)
1. Open HACS → ⋮ menu → **Custom repositories**
2. Add URL: `https://github.com/albuster-prog/vehicle-manager-ha` — Category: **Integration**
3. Search for **Vehicle Manager** and install
4. Restart Home Assistant
5. Go to **Settings → Devices & Services → Add Integration → Vehicle Manager**

### Manual
1. Copy `custom_components/vehicle_manager/` to your HA `custom_components/` folder
2. Restart Home Assistant
3. Add the integration via **Settings → Devices & Services**

---

## ⚙️ Configuration

### Step 1 — Vehicle Info
- Vehicle name, type, license plate, VIN
- Optional: odometer sensor entity (for km-based tracking)
- Distance unit (km / miles)
- Warning days threshold (default: 30)

### Step 2 — License Key
- Leave blank for **Free tier** (legal documents only, 1 vehicle)
- Enter your Pro key for **unlimited vehicles + all maintenance counters**

### Updating document dates (Options flow)
Go to **Settings → Devices & Services → Vehicle Manager → Configure → Update Legal Document**:
- Select document (RCA, CASCO, ITP, Rovinieta...)
- Enter start date and expiry date

### Marking maintenance as done
Use the **"Done Today"** button for each maintenance counter — it automatically saves today's date and current odometer reading.

---

## 🤖 Automation Example

```yaml
automation:
  - alias: "Notify when RCA expires soon"
    trigger:
      - platform: state
        entity_id: binary_sensor.kia_eniro_rca_warning
        to: "on"
    action:
      - service: notify.mobile_app_phone
        data:
          title: "⚠️ RCA Insurance"
          message: >
            RCA expires in {{ state_attr('sensor.kia_eniro_rca', 'days_remaining') }} days
            ({{ state_attr('sensor.kia_eniro_rca', 'expiry_date') }})
```

---

## 📊 Dashboard Card Example

```yaml
type: entities
title: Kia eNiro — Legal Documents
entities:
  - entity: sensor.kia_eniro_rca
    name: RCA Insurance
  - entity: sensor.kia_eniro_casco
    name: CASCO Insurance
  - entity: sensor.kia_eniro_itp_ev
    name: ITP
  - entity: sensor.kia_eniro_rovinieta
    name: Road Vignette
```

---

## 💎 Pro License

Get a **lifetime Pro license** for unlimited vehicles and all 60+ maintenance counters:

👉 **[Buy Me a Coffee — Vehicle Manager Pro](https://www.buymeacoffee.com/vehiclemanagerha)**

After purchase, you will receive a license key in the format: `VM-XXXX-XXXX-XXXX-XXXX`

Enter it in the integration setup or via **Configure → Update License Key**.

---

## 🐛 Known Issues Fixed

This integration fixes the **Car Manager România bug** where:
> `start_date` in the future (e.g. insurance starting tomorrow) caused status to show "neconfigurat" instead of "ok"

Our `sensor.py` correctly handles: if `start_date <= expiry_date` and `expiry_date > today` → **status = OK**.

---

## 📝 License

MIT License — see [LICENSE](LICENSE)

---

## 🙏 Contributing

Issues and PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon).

If this integration helps you, consider supporting development:  
☕ [Buy Me a Coffee](https://www.buymeacoffee.com/vehiclemanagerha)
