-- Seed historical incidents. Domain matches the Digital Twin simulator:
--   line-1: cnc / assembly / inspect (SKU-A), tool wears after ~400 parts
--   line-2: press / weld / inspect  (SKU-B), tool wears after ~300 parts
--   cascade: a long line-1 stop starves line-2 (~10 min later)
-- These give the Copilot a memory of prior root causes + fixes to retrieve.

INSERT INTO incidents
  (occurred_at, line_id, station_id, category, title, description, root_cause, resolution, downtime_min)
VALUES
  ('2026-05-12 02:40:00+00', 'line-1', 'line-1-cnc', 'mechanical',
   'Conveyor bearing seizure on CNC infeed',
   'Line-1 stopped for 26 min; OEE availability dropped sharply on night shift.',
   'Infeed conveyor bearing seized from lack of lubrication; ran past PM interval.',
   'Replaced bearing, re-greased, added bearing to weekly PM checklist.', 26),

  ('2026-05-13 14:05:00+00', 'line-1', 'line-1-cnc', 'quality',
   'Surface defect spike correlated with tool wear',
   'Scrap rate on line-1 climbed from ~3% to ~12%; mostly surface defects.',
   'CNC tool exceeded 400-part wear threshold; equipment_state went tool_worn.',
   'Indexed/replaced tool insert; reset wear counter; tightened tool-change cadence.', 0),

  ('2026-05-14 09:20:00+00', 'line-2', 'line-2-press', 'electrical',
   'Press VFD fault trips line-2',
   'Line-2 press tripped on overcurrent; 14 min unplanned stop.',
   'Variable-frequency drive overheated; cooling fan clogged with metal dust.',
   'Cleaned VFD cooling fan, reset fault, scheduled enclosure filter swap.', 14),

  ('2026-05-15 03:10:00+00', 'line-2', 'line-2-weld', 'quality',
   'Missing-component defects at weld station',
   'Cluster of missing_component scrap on line-2 during early-morning shift.',
   'Component feeder misfeed under vibration; parts welded without insert.',
   'Re-seated feeder track, added presence sensor check before weld.', 0),

  ('2026-05-16 11:45:00+00', 'line-1', 'line-1-assembly', 'material',
   'Material starvation backs up assembly',
   'Line-1 assembly idled 9 min waiting on parts from upstream CNC.',
   'CNC short stop upstream; buffer ran dry before CNC recovered.',
   'Raised inter-station buffer min level; no hardware fix needed.', 9),

  ('2026-05-16 12:05:00+00', 'line-2', 'line-2-press', 'material',
   'Cascade starvation from line-1 stop',
   'Line-2 backed up ~10 min after a long line-1 outage; classic cascade.',
   'Long line-1 mechanical stop starved shared upstream material to line-2.',
   'Decoupled with intermediate WIP buffer; documented cascade dependency.', 11),

  ('2026-05-17 22:30:00+00', 'line-1', 'line-1-cnc', 'setup',
   'Long changeover between SKU-A orders',
   'Setup time on line-1 order changeover ran to 10 min, above 4-6 min target.',
   'Fixture not pre-staged; operator hunted for correct tooling mid-changeover.',
   'Adopted SMED: pre-stage fixtures/tools on a changeover cart.', 10),

  ('2026-05-18 06:15:00+00', 'line-2', 'line-2-weld', 'electrical',
   'Weld controller comms dropout',
   'Line-2 weld controller lost comms; 7 min stop, intermittent.',
   'Loose ethernet connector on weld controller; vibration-induced dropout.',
   'Re-terminated connector with strain relief; added to inspection list.', 7),

  ('2026-05-19 15:50:00+00', 'line-1', 'line-1-inspect', 'quality',
   'Dimension defects after tool change',
   'Short burst of dimension defects right after a CNC tool change on line-1.',
   'New tool offset not re-zeroed; first parts machined out of tolerance.',
   'Added mandatory probe re-zero step to tool-change procedure.', 0),

  ('2026-05-20 04:25:00+00', 'line-2', 'line-2-press', 'mechanical',
   'Press hydraulic pressure loss',
   'Line-2 press lost forming pressure; 22 min stop, worst of the week.',
   'Hydraulic hose chafed through against frame; slow fluid loss then failure.',
   'Replaced hose, added abrasion sleeve and clamp; topped up reservoir.', 22),

  ('2026-05-21 10:00:00+00', 'line-1', 'line-1-cnc', 'mechanical',
   'Coolant pump failure raises scrap',
   'Line-1 ran hot; surface finish degraded, scrap edged up before stop.',
   'Coolant pump impeller failed; insufficient coolant to cutting zone.',
   'Swapped pump, flushed lines; correlated finish defects to coolant flow.', 18),

  ('2026-05-22 19:35:00+00', 'line-2', 'line-2-inspect', 'quality',
   'Color defects from incoming material lot',
   'Spike in color defects on line-2 isolated to one SKU-B material lot.',
   'Off-spec coating on a supplier lot; not a process fault.',
   'Quarantined lot, raised supplier NCR, released next lot after check.', 0);
