# LCP x TCS — Operating Context for AI Agent
This document is the operational **source of truth** for an AI agent supporting a hybrid **NEMT brokerage (LCP)** + **in-house fleet (TCS)**. It converts operating knowledge into **machine-usable rules** that optimize for:

- **Zero Missed Trips**
- **Minimize Late Trips**
- **Maximize fleet utilization (TPH) without breaking service**
- **Minimize deadhead + idle time**
- **Reduce vendor cost exposure**
- **Protect reimbursement + compliance (no-show, courtesy call, documentation)**

---

## 1. Core Service Standards
### Hard Rules
- **Zero Missed Trips:** No trip may be left unassigned or unrecovered.  
  - *Why:* patient safety + “must-serve” contract risk + performance penalties.
- **On-Time Standard (baseline):** Build routing to arrive **before appointment time**, typically with a **15-minute early-arrival buffer**.  
  - *Why:* late arrivals trigger complaints, denials, and contract scrutiny.
- **Return / Will-Call Requirement:** Must pick up return trips within **60 minutes** of member request (contract baseline).  
  - *Why:* explicit contract compliance + high complaint sensitivity.
- **Call Center SLA:** Answer **85% of calls within 30 seconds** (staffing math anchored here).  
  - *Why:* if intake backs up, the entire system fails downstream.
- **Golden No-Show Rule:** A trip **cannot be finalized as a “No-Show”** without:
  - a logged **courtesy call attempt** via LCP, and
  - verification of **correct location** (Samsara GPS + address validation), and
  - **dispatch approval** when required by policy/contract.  
  - *Why:* protects reimbursement and prevents false no-shows.

### Late Definition (needs a single enterprise-wide standard)
- **Candidate standard (common):** “Late” = arrival **>15 minutes** after scheduled pickup time (or outside the contract pickup window).  
- **Contract baseline already used:** 15-minute early-arrival expectation for appointment compliance.  
- **Action:** lock one definition across LCP/TCS and encode it.

### Operational Definitions
- **Missed Trip:** Member not transported due to provider failure resulting in missed appointment or failed transport.
- **Late Trip:** Pickup/drop occurs outside allowed contractual window.
- **At-Risk Trip:** Current ETA indicates pickup will fall outside allowed window.
- **Will-Call / 2-Leg:** Return trip triggered when member is ready; pickup time is variable.

---

## 2. Operating Model (Broker vs In-House)
### LCP (Broker / Orchestrator)
Responsible for:
- Call intake + scheduling
- Member eligibility verification + data integrity
- Vendor network management + compliance enforcement
- Claims/grievances support + reimbursement protection (no-show/courtesy call rules)
- Reassignment when any provider fails (including TCS)

### TCS (In-House Fleet / Execution Engine)
Responsible for:
- Driver staffing + vehicle readiness
- Route execution (day-of)
- Dispatch + real-time recovery
- Pole driver staging + rapid response
- Maximizing efficiency **without** creating late/missed trips

### Portfolio Allocation Logic
- **Target baseline:** TCS executes ~**60%** of total trips (example: 2,600/day → 1,560 TCS / 1,040 vendor).  
  - *Why:* control, reliability, cost discipline.
- **Waterfall assignment rule:**
  1) Assign to **TCS** if it can be done **without increasing late risk** and within capacity rules  
  2) Otherwise assign to **vendors** for overflow, fringe geography, specialty capacity, surge relief  
  3) If day-of failure occurs, recover via **pole drivers** or **high-reliability vendor backup**

---

## 3. Trip Types + Definitions
### Mobility / Vehicle Fit
- **Ambulatory (Ambu):** Walks independently (or cane/walker). Highest shared-ride potential.
- **Wheelchair (WC):** Requires lift/ramp-equipped vehicle. Lower shared-ride flexibility.
- **(If applicable) Stretcher:** Specialized; treat as separate capacity class. *(Unknown if used in your ops.)*

### Trip Timing Class
- **1-Leg (Outbound / to appointment):** Fixed time anchor (appointment time). Must be **pre-assigned**.
- **2-Leg (Return / Will-Call):** Triggered when member is ready; high variance.

### Clinical / Priority Class (operational meaning)
- **Critical Care (Dialysis / oncology / life-sustaining):** Highest priority; near-zero lateness tolerance.
- **ABA / Pathways / recurring therapy:** Predictable recurring schedules → ideal for stable pre-routed anchors.
- **Urgent care / hospital discharge returns:** High urgency will-calls; requires “nearest appropriate vehicle” logic.

### Geography Class
- **Urban:** High density; higher TPH; higher cancellation volatility; more will-call pressure.
- **Rural:** Lower density; higher deadhead tolerance; fewer substitutes.
- **Long-distance:** **>50 miles**; different cancellation/no-show thresholds and wait reimbursement logic.

---

## 4. Dispatch + Trip Assignment Workflow
### Pre-Day (Planning)
- **Goal:** 100% of **1-Legs** (outbound) routed + assigned **day prior** (target: 24 hours in advance).  
  - *Why:* stable routes reduce day-of chaos and late cascades.
- Recurring trips (dialysis, ABA, etc.) serve as **route anchors**.

### Day-Of (Execution)
Dispatch monitors:
- RouteGenie: planned assignment + trip statuses (“plan of record” for billing/status)
- Samsara: GPS truth for ETA, location verification, safety

### Dispatch Intervention Triggers
- **At-risk threshold:** If a driver’s predicted ETA indicates **>10–15 minutes behind schedule** for the next pickup → dispatcher must intervene.  
  - Interventions: ping driver, resequence, strip trip, deploy pole, vendor backup.

### Recovery Logic (non-negotiable)
- If TCS cannot fulfill a trip, it must be **handed back immediately** to LCP for reassignment (avoid “silent failures”).

---

## 5. Roles, Responsibilities, and Hand-offs
### LCP Roles
- **Call Center / CSR**
  - Answer SLA, schedule trips, update changes, run courtesy calls.
- **Trip Assignment**
  - Allocate trips to TCS vs vendors; reassign failures quickly.
- **Vendor Management**
  - Compliance and performance enforcement; high-risk vendors throttled.

### TCS Roles
- **Trip Assignment (planning)**
  - Build routes, assign drivers/vehicles, apply overbooking rules intelligently.
- **Dispatch (day-of)**
  - Run live board, manage will-calls, recover at-risk trips, deploy pole drivers.
- **Drivers**
  - Execute safely/on-time, document timestamps, attempt member contact per policy.

### Hand-offs (define explicitly)
- **Candidate handoff:** LCP delivers “clean manifest” to TCS the evening before service day (example given: 6:00 PM).  
  - **Unknown:** confirm exact time + what constitutes “clean” (fields required).

---

## 6. Tech Stack + “System of Record” Definitions
### RouteGenie (Plan + Billing System of Record)
Used for:
- scheduling, routing, driver assignment, trip status tracking, billing manifests  
Rule:
- **If it isn’t in RouteGenie, it doesn’t exist for billing/status.**

### Samsara (Execution / GPS Ground Truth)
Used for:
- real-time vehicle location, ETA reality checks, idle time, safety  
Rule:
- **If RouteGenie timestamps conflict with reality, use Samsara GPS breadcrumbs to validate what actually happened.**

### Eligibility / Member Data System (HIPAA-compliant)
- Daily eligibility/member files feed the intake + scheduling layer  
Rule:
- **If member/destination not in system, trip cannot be executed or billed correctly. “Stop-and-fix.”**

---

## 7. Key Constraints from Contracts / Compliance
### Timing / Cancellation / No-Show (contract baseline)
- **Return pickup:** within **1 hour** of member call for return.
- **Broker cancellation notice (to vendor):**
  - Local (<50 mi): notify ≥ **1 hour** before To-Be-Ready
  - Long-distance (>50 mi): notify ≥ **2 hours** before To-Be-Ready
- **No-Show definition triggers (baseline):**
  - Late cancel: <1 hour local / <2 hours long-distance, OR
  - Member not present **10 minutes after arrival time**, OR
  - Cancel-at-door (follow procedure)
- **Courtesy call gate:** Driver/vendor must contact LCP so CSR can attempt courtesy call before finalizing no-show.

### Courtesy Call Standard (operational)
- **Candidate:** driver calls member **5–10 minutes before arrival** (or upon arriving if no answer).  
  - *Why:* improves ready rate, reduces curb idle, and protects no-show validity.
  - **Unknown:** confirm mandated timing by contract/partner.

### Documentation / “Clean Manifest”
- Arrive/Load/Unload timestamps must be captured digitally.
- Manual entries require a **reason code** (if your system supports it).  
  - *Why:* billing defensibility + audit readiness.

### Credentialing / Vendor Compliance Themes
- Insurance (LCP additional insured + cancellation notice)
- OIG/SAM checks, background/drug/MVR
- Vehicle inspections, driver logs, W-9, etc.  
  - *Why:* compliance gating; non-compliance = operational + contract risk.

---

## 8. Capacity + Scheduling Logic
### Trips Per Hour (TPH) Standards (strong internal anchor)
- **Urban ambulatory:** target ~**2.0 TPH** (range 1.8–2.2 acceptable)
- **Other mixes (WC/non-urban):** target ~**1.0 TPH** (range 1.0–1.2)  
- *Why:* capacity planning + cost per trip discipline.

### Cancellation Reality → Overbooking Rules
- **Overall cancels:** ~**9%** (baseline)
- **Urban ambulatory cancels:** ~**30%** (baseline)
- **Overbook policy:**
  - Schedule ~**9% more trips overall**
  - Schedule ~**30% more in urban ambulatory**
  - Only overbook beyond safe limits if **pole capacity exists**  
- *Why:* otherwise you underutilize fixed-cost assets; but overbooking without recovery capacity creates late cascades.

### Pole Drivers (standby capacity)
- Definition: staged drivers with no pre-assigned manifest used for:
  - will-calls, emergency recoveries, vendor fall-offs, call-offs, sudden spikes
- Rule: pole capacity is the **shock absorber** that protects the 1-hour return requirement.

### Breaks / Off-road Controls
- Stagger breaks to maintain coverage.
- **Unknown:** maximum % of drivers allowed off-road simultaneously by zone/time window.

---

## 9. Metrics That Matter (KPIs + thresholds)
### Reliability KPIs
- **Missed Trip Rate:** target = **0 (near-zero)**; every missed trip triggers root cause + corrective action.
- **On-Time Performance (OTP):** target typically **>95%**, aspirational **>98%** in stable zones. *(Confirm contract target.)*
- **Will-Call Wait Time:** average + P90 from request → vehicle arrival (must protect 60-minute compliance).

### Dispatch KPIs
- **Dispatch Response / Recovery Speed:** target **<15 minutes** to resolve an at-risk/unassigned trip.
- **Dispatch Minutes:** accumulated delay/recovery burden across a segment; if it exceeds threshold, offload.

### Efficiency KPIs
- **Deadhead % / Deadhead miles:** key profitability driver.  
  - Candidate target: **<20%** (if used internally). *(Unknown: confirm official target.)*
- **Pole utilization:** too high = understaffed; too low = wasted buffer.

### Financial Protection KPIs
- **No-show documentation compliance:** courtesy call logged + wait protocol met + GPS validation.
- **Wait-time reimbursement eligibility:** especially for long-distance rules (contract dependent).

---

## 10. Geographic / Territory Model
### Zones
- **Urban metros (examples):** Indianapolis, Gary, South Bend, Fort Wayne, Evansville, Muncie, Clarksville.
- Operational primitive:
  - Urban: dense, volatile, will-calls → prioritize TCS + pole staging
  - Rural/long distance: sparse, expensive reposition → consider vendors or specialty long-haul units

### Staging Points
- Define “discharge hubs” and high-frequency facilities where pole drivers stage to reduce return response time.  
- **Unknown:** list of approved staging points + radius rules.

---

## 11. Failure Modes + Playbooks (what breaks + what to do)
### Return Uncertainty (Will-call surge)
- Playbook:
  - stage poles near discharge hubs
  - prioritize by “minutes since request”
  - re-route nearest appropriate unit
- Objective: protect **60-minute compliance**

### Overbooking → Late Cascades
- Playbook:
  - cap overbooking by zone + driver type
  - offload low-priority ambulatory to vendors early
  - keep critical care protected

### Silent Unfulfilled Trips
- Playbook:
  - enforce a “hand-back timer” from TCS to LCP when coverage fails (immediate escalation)

### Driver Call-Off / No-Show
- Playbook:
  - move first trips to pole drivers
  - notify impacted members
  - re-optimize board; farm overflow to vendors immediately

### Vehicle Breakdown
- Playbook:
  - dispatch rescue vehicle
  - transload member if WC; if ambulatory, consider rideshare bridge **only if contract allows**
  - protect critical trips first

### No-show incorrectly issued
- Playbook:
  - no-show cannot finalize without courtesy call log + wait time + GPS validation
  - flag for compliance review if missing

### Member/destination not in system
- Playbook:
  - stop-and-fix: verify eligibility + create/repair record before execution

---

## 12. Decision Rules (if/then) the agent must follow
### Assignment Waterfall
- **IF** trip can be serviced by TCS without increasing late risk **THEN** assign to TCS  
- **ELSE** assign to vendor (overflow/fringe/surge/specialty) early

### Will-Call Control
- **IF** will-call request logged **THEN** assign within dispatch response target (≤15 minutes)
- **IF** elapsed time since request ≥45 minutes **THEN** escalate priority (strip/re-route/pole)
- **IF** no appropriate TCS unit can arrive within 20 minutes **THEN** assign highest-rated vendor capable of modality

### Critical Care Protection
- **IF** trip is Dialysis/Critical Care **THEN** treat as top priority; protect from offloads that risk lateness  
- **IF** dialysis trip at risk of >15 minutes late **THEN** preempt standard ambulatory pickups to recover  
- **IF** assigning dialysis to vendors **THEN** avoid vendors with OTP history <95% *(candidate rule; confirm threshold)*

### At-Risk Intervention
- **IF** driver projected >10–15 minutes behind for next pickup **THEN** intervene:
  - ping, resequence, strip trip, deploy pole, or vendor backup

### No-Show Gating
- **IF** driver requests no-show **AND** courtesy call not logged **THEN** deny + instruct contact via LCP
- **IF** member not present 10 minutes after arrival **AND** courtesy call attempted **THEN** proceed per policy with dispatch approval when required
- **IF** 1-leg no-show confirmed **THEN** cancel 2-leg to prevent deadhead waste *(confirm if this is your policy)*

### Long-Distance Threshold
- **IF** trip distance >50 miles **THEN** apply 2-hour cancel/no-show thresholds; else 1-hour

---

## 13. Data Objects + Fields the agent should expect
### Trip Object
- TripID, LegID, MemberID
- LegType (1-leg/2-leg)
- MobilityType (Ambu/WC/[Stretcher?])
- Program/ServiceLevel (Pathways/ABA/Dialysis/etc.)
- PickupAddress, DropoffAddress
- AppointmentTime, ToBeReadyTime
- PickupWindowStart/End (if used)
- StatusCode (Pending/Assigned/EnRoute/Arrived/Loaded/Dropped/Cancelled/NoShow)
- SpecialInstructions

### Timing Object
- Timestamp_Planned (RG)
- Timestamp_Actual_Arrive (GPS validated)
- Timestamp_Load, Timestamp_Unload
- WillCall_Request_Timestamp
- Dispatch_Assigned_Timestamp

### Resource Object
- DriverID, VehicleID/VIN
- VehicleType (Ambu/WC), capacity
- PoleStatus (Y/N)
- CurrentLocation (Samsara), ETA

### Compliance Object
- VendorComplianceStatus, InsuranceStatus
- DriverChecklistStatus
- CourtesyCallLogStatus
- NoShowApprovalStatus

### Financial Object
- LoadedMiles, DeadheadMiles
- WaitTimeMinutes
- NoShowFeeEligibility
- ReimbursementCode/RateTableRef

## SCHEDULING CONTEXT GUIDELINES
When generating a schedule, the automated Python engine will cross-reference `history_leg1.csv` and `history_leg2.csv`.
1. **The 1-Hour SLA Rule:** For Leg 2 trips, the engine will utilize the full 1-hour contractual window from the `TBR time` (To Be Ready time) to bundle trips efficiently.
2. **Urban Density Priority:** The engine must prioritize the `LCP 04 (INDIANAPOLIS)` territory first, anchoring drivers in specific Zip Codes (e.g., 46202, 46219) to eliminate deadhead miles.
3. **Shift Constraints:** Drivers operate in 7-8 hour shifts. The bot must not schedule a pickup that would force a drop-off beyond the 8-hour mark.

---
