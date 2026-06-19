// Package model mirrors the Digital Twin event contract (EVENT_CONTRACT.md /
// twin/events.py). The Go structs here are the consumer side of that contract;
// keep SchemaVersion in sync and bump handling when the Twin bumps its version.
package model

import (
	"encoding/json"
	"fmt"
	"time"
)

const SchemaVersion = 1

// Envelope is the common wrapper around every event.
type Envelope struct {
	SchemaVersion int             `json:"schema_version"`
	EventID       string          `json:"event_id"`
	EventType     string          `json:"event_type"`
	TS            string          `json:"ts"`
	LineID        string          `json:"line_id"`
	StationID     string          `json:"station_id"`
	Payload       json.RawMessage `json:"payload"`
}

func (e Envelope) Time() (time.Time, error) {
	return time.Parse(time.RFC3339Nano, e.TS)
}

// Typed payloads.

type ProductionStarted struct {
	OrderID    string `json:"order_id"`
	ProductSKU string `json:"product_sku"`
	TargetQty  uint32 `json:"target_qty"`
}

type ProductionCompleted struct {
	OrderID          string  `json:"order_id"`
	GoodQty          uint32  `json:"good_qty"`
	ScrapQty         uint32  `json:"scrap_qty"`
	IdealCycleTimeS  float64 `json:"ideal_cycle_time_s"`
	ActualCycleTimeS float64 `json:"actual_cycle_time_s"`
}

type DowntimeStarted struct {
	DowntimeID string `json:"downtime_id"`
	Category   string `json:"category"`
	Planned    bool   `json:"planned"`
	Reason     string `json:"reason"`
}

type DowntimeEnded struct {
	DowntimeID string  `json:"downtime_id"`
	DurationS  float64 `json:"duration_s"`
}

type QualityEvent struct {
	PartID         string  `json:"part_id"`
	Result         string  `json:"result"`
	DefectType     string  `json:"defect_type"`
	Confidence     float64 `json:"confidence"`
	ImageRef       string  `json:"image_ref"`
	EquipmentState string  `json:"equipment_state"`
}

// Row variants the sink can persist. Decode converts an Envelope into exactly
// one of the table-shaped rows below.

type ProductionRow struct {
	TS               time.Time
	EventID          string
	EventType        string
	LineID           string
	StationID        string
	OrderID          string
	ProductSKU       string
	TargetQty        uint32
	GoodQty          uint32
	ScrapQty         uint32
	IdealCycleTimeS  float64
	ActualCycleTimeS float64
}

type DowntimeRow struct {
	TS         time.Time
	EventID    string
	EventType  string
	LineID     string
	StationID  string
	DowntimeID string
	Category   string
	Planned    uint8
	Reason     string
	DurationS  float64
}

type QualityRow struct {
	TS             time.Time
	EventID        string
	LineID         string
	StationID      string
	PartID         string
	Result         string
	DefectType     string
	Confidence     float64
	ImageRef       string
	EquipmentState string
}

// Decoded is a tagged union: exactly one pointer is non-nil.
type Decoded struct {
	Production *ProductionRow
	Downtime   *DowntimeRow
	Quality    *QualityRow
}

// Decode parses raw NATS bytes into a typed row based on event_type.
func Decode(data []byte) (Decoded, error) {
	var e Envelope
	if err := json.Unmarshal(data, &e); err != nil {
		return Decoded{}, fmt.Errorf("envelope: %w", err)
	}
	if e.SchemaVersion != SchemaVersion {
		return Decoded{}, fmt.Errorf("unsupported schema_version %d", e.SchemaVersion)
	}
	ts, err := e.Time()
	if err != nil {
		return Decoded{}, fmt.Errorf("ts %q: %w", e.TS, err)
	}

	switch e.EventType {
	case "production_started":
		var p ProductionStarted
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return Decoded{}, err
		}
		return Decoded{Production: &ProductionRow{
			TS: ts, EventID: e.EventID, EventType: e.EventType,
			LineID: e.LineID, StationID: e.StationID,
			OrderID: p.OrderID, ProductSKU: p.ProductSKU, TargetQty: p.TargetQty,
		}}, nil

	case "production_completed":
		var p ProductionCompleted
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return Decoded{}, err
		}
		return Decoded{Production: &ProductionRow{
			TS: ts, EventID: e.EventID, EventType: e.EventType,
			LineID: e.LineID, StationID: e.StationID,
			OrderID: p.OrderID, GoodQty: p.GoodQty, ScrapQty: p.ScrapQty,
			IdealCycleTimeS: p.IdealCycleTimeS, ActualCycleTimeS: p.ActualCycleTimeS,
		}}, nil

	case "downtime_started":
		var p DowntimeStarted
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return Decoded{}, err
		}
		return Decoded{Downtime: &DowntimeRow{
			TS: ts, EventID: e.EventID, EventType: e.EventType,
			LineID: e.LineID, StationID: e.StationID,
			DowntimeID: p.DowntimeID, Category: p.Category,
			Planned: b2u8(p.Planned), Reason: p.Reason,
		}}, nil

	case "downtime_ended":
		var p DowntimeEnded
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return Decoded{}, err
		}
		return Decoded{Downtime: &DowntimeRow{
			TS: ts, EventID: e.EventID, EventType: e.EventType,
			LineID: e.LineID, StationID: e.StationID,
			DowntimeID: p.DowntimeID, DurationS: p.DurationS,
		}}, nil

	case "quality_event":
		var p QualityEvent
		if err := json.Unmarshal(e.Payload, &p); err != nil {
			return Decoded{}, err
		}
		return Decoded{Quality: &QualityRow{
			TS: ts, EventID: e.EventID,
			LineID: e.LineID, StationID: e.StationID,
			PartID: p.PartID, Result: p.Result, DefectType: p.DefectType,
			Confidence: p.Confidence, ImageRef: p.ImageRef,
			EquipmentState: p.EquipmentState,
		}}, nil

	default:
		return Decoded{}, fmt.Errorf("unknown event_type %q", e.EventType)
	}
}

func b2u8(b bool) uint8 {
	if b {
		return 1
	}
	return 0
}
