# 🌐 Paltro-SD01 — Multi-PC Team Roster & Cross-Department Release Matrix

> **Last Updated:** `2026-11-13 11:30:00`  
> **Departments Covered:** Software Dept (`SW`) · Firmware Dept (`FW`) · Electronics/Hardware (`HW`) · Rig QA (`QA`)  

## 👨‍💻 Active Engineering Team & Workstation Roster

| ID | Engineer Name | Role | Department | Workstation PC | Local Repo Root | Active Repo / WO | Status |
| :---: | :--- | :--- | :---: | :---: | :--- | :---: | :---: |
| `ENG-01` | **Paltro-SD01 (Lead)** | Lead Software Architect | `SOFTWARE` | `WS-PALTRO-MASTER` | `D:\Projects\Software Repo` | `HFRR-ADV / WO 2472` | `ONLINE` |
| `ENG-02` | **Software Engineer 2** | LabVIEW & DAQ Engineer | `SOFTWARE` | `SW-PC-02` | `D:\Projects\Software Repo` | `BOCLE / WO 2485` | `ONLINE` |
| `ENG-03` | **Software Engineer 3** | LabVIEW HMI & Reports Engineer | `SOFTWARE` | `SW-PC-03` | `C:\Projects\Software Repo` | `LAB-IQ-150 / WO 2487` | `ONLINE` |
| `ENG-04` | **Software Engineer 4** | Python Vision AI & Metrology | `SOFTWARE` | `SW-PC-04` | `D:\Projects\Software Repo` | `HFRR-ADV / WO 2486` | `ONLINE` |
| `ENG-05` | **Firmware Engineer 1** | Embedded MCU & Modbus Lead | `FIRMWARE` | `FW-PC-01` | `D:\Projects\Firmware Repo` | `FW-HFRR-ADV / FW-v3.2` | `ONLINE` |
| `ENG-06` | **QA & Rig Validation Engineer** | Bench Integration & Release QA | `QA_MECH` | `RIG-BENCH-PC-06` | `D:\Projects\Software Repo` | `LAB-IQ-350 / WO 2494` | `ONLINE` |

## 🔗 Cross-Department Linked Release Matrix (Software Release ↔ Firmware Release)

| Link ID | Rig / Platform | Software Work Order | SW Version | Linked Firmware Repo | Firmware Version | HW / PCB Rev | Compatibility | Verified By | Notes |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `REL-LINK-01` | **HFRR-ADV** | `WO 2472` | `v44` | `FW-HFRR-ADV` | **`FW-v3.2.0`** | `PCB-Rev-C` | `VERIFIED` | Paltro-SD01 (Lead) | Production release bundle: HFRR-ADV SW v44 + FW-v3.2.0 + Python Wear Scar AI |
| `REL-LINK-02` | **HFRR-ADV** | `WO 2486` | `v07` | `FW-HFRR-ADV` | **`FW-v3.2.0`** | `PCB-Rev-C` | `TESTING` | Software Engineer 4 | Bench validation with FW-v3.2.0 stroke controller |
| `REL-LINK-03` | **BOCLE** | `WO 2485` | `v03` | `FW-BOCLE` | **`FW-v2.4.1`** | `PCB-Rev-B` | `VERIFIED` | Software Engineer 2 | Closed milestone validated with BOCLE Firmware v2.4.1 |
| `REL-LINK-04` | **LAB-IQ-150** | `WO 2476` | `v07` | `FW-LAB-IQ-150` | **`FW-v1.9.0`** | `PCB-Rev-A` | `VERIFIED` | Software Engineer 3 | Validated release package for LAB-IQ 150 WO 2476 |
| `REL-LINK-05` | **LAB-IQ-350** | `WO 2494` | `v01` | `FW-LAB-IQ-350` | **`FW-v2.1.0`** | `PCB-Rev-B` | `INTEGRATION` | QA & Rig Validation Engineer | Software v01 + Firmware v2.1.0 joint integration test |
| `REL-LINK-06` | **AIRJET** | `Erosion Tester` | `v24` | `FW-AIRJET` | **`FW-v4.0.2`** | `PCB-Rev-D` | `VERIFIED` | Paltro-SD01 (Lead) | Locked production release v24 + FW-v4.0.2 |

## 🔌 Firmware Department Releases Registry

| Firmware ID | Target Rig | MCU / Controller | Firmware Version | Protocol | Checksum | Status | Release Notes |
| :---: | :---: | :--- | :---: | :--- | :---: | :---: | :--- |
| `FW-HFRR-ADV` | **HFRR-ADV** | STM32F4 / Industrial Controller | **`FW-v3.2.0`** | `Modbus RTU / Serial 115200` | `CRC-8A4F` | `RELEASED` | High-frequency stroke PID loop + RTD thermal interlocks |
| `FW-BOCLE` | **BOCLE** | Embedded Rig Controller | **`FW-v2.4.1`** | `NI-DAQmx / Serial Interlock` | `CRC-3C19` | `RELEASED` | Humidity & temperature loop stabilization + motor RPM ramp |
| `FW-LAB-IQ-150` | **LAB-IQ-150** | LAB-IQ 150 Control Board | **`FW-v1.9.0`** | `USB-Serial / DAQ` | `CRC-77D2` | `RELEASED` | Thermal cutoff safety watchdog & flow sensor calibration |
| `FW-LAB-IQ-350` | **LAB-IQ-350** | LAB-IQ 350 Mainboard | **`FW-v2.1.0`** | `Modbus / DAQ` | `CRC-51E0` | `TESTING` | Updated pressure transducer ADC filter for WO 2494 |
| `FW-B2V2` | **B2V2** | B2V2 Control Unit | **`FW-v1.4.0`** | `Serial / DAQ` | `CRC-19B8` | `RELEASED` | Baseline production firmware for WO 2470 |
| `FW-AIRJET` | **AIRJET** | Airjet Erosion Controller | **`FW-v4.0.2`** | `High-Speed Counter / DAQ` | `CRC-E401` | `RELEASED` | Synchronized with Erosion Tester Software v24 |
