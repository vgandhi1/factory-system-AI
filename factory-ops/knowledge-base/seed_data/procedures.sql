-- Runbook procedures per downtime category. The Copilot retrieves the matching
-- procedure to recommend a next action alongside its root-cause hypothesis.

INSERT INTO procedures (category, title, body) VALUES
  ('mechanical',
   'Mechanical stop response',
   'Lock out / tag out the affected station. Inspect bearings, belts, hoses, and '
   'lubrication points for the failure mode. Check the PM log: a stop on a '
   'component past its interval points to a missed preventive task. After repair, '
   'reset the wear/PM counter and add the failed component to the weekly checklist.'),

  ('electrical',
   'Electrical / drive fault response',
   'Read the drive (VFD) or controller fault code before resetting. Overcurrent / '
   'overtemp faults usually mean blocked cooling or a clogged filter, not a bad '
   'drive. Check connectors and strain relief for vibration-induced comms dropouts. '
   'Reset only after the cause is found; log the fault code for trend analysis.'),

  ('material',
   'Material starvation response',
   'Confirm whether the stop is local or a cascade from an upstream line (line-1 '
   'long stops starve line-2 ~10 min later). Raise the inter-station buffer minimum '
   'to decouple short upstream stops. For cascades, add intermediate WIP so a single '
   'outage does not propagate downstream.'),

  ('quality',
   'Quality-event response',
   'Pull the defect_type breakdown and correlate with equipment_state. A surface/'
   'dimension spike tracking tool_worn means the tool passed its wear threshold '
   '(line-1 ~400 parts, line-2 ~300) — index or replace it and reset the counter. '
   'After any tool change, re-zero offsets/probe before running production. '
   'Color/missing-component clusters often trace to incoming material or feeder '
   'misfeeds, not the process — check the lot and feeder track.'),

  ('setup',
   'Changeover / setup reduction',
   'Target 4-6 min per changeover. Apply SMED: pre-stage fixtures, tooling, and the '
   'first-article gauge on a changeover cart before the run ends (external setup). '
   'Keep only the unavoidable internal steps inside the stop. A changeover above '
   'target usually means tooling was hunted for mid-stop.'),

  ('break',
   'Planned break handling',
   'Scheduled breaks are planned downtime and should not be counted against '
   'availability the same way as unplanned stops. Stagger breaks across stations '
   'where staffing allows to keep the line flowing.');
