# **Project 3: Factory Digital Twin (Enabler)**

**Timeline:** 4–6 weeks

**Scope:** Synthetic data generation platform

## **Core Features**

* **MES event generator:** Simulates production orders, equipment states, and line throughput, outputting configurable JSON events (e.g., production started/completed, downtime, quality events).  
* **Downtime simulator:** Creates realistic downtime scenarios with cascading effects and varying duration distributions.  
* **OEE calculator:** Establishes a ground truth OEE based on simulated events to validate dashboard calculations.  
* **Quality event generator:** Simulates defective parts correlated with equipment states (e.g., worn tools causing higher defect rates).  
* **Defect image generator (synthetic):** Creates a labeled dataset for YOLO training using either public datasets or synthetic generation via PIL/Albumentations.

## **Tech Stack**

* **Event generator:** Python (faker, random)  
* **Defect images:** PIL or Albumentations  
* **Output:** NATS events, images to MinIO  
* **Orchestration:** Docker Compose

## **Deliverables Structure**

* simulator/: Scripts for generating MES events, downtime, and quality data, plus configuration files.  
* synthetic-images/: Defect generator script, base image templates, and output directory.  
* oee-calculator/: OEE engine and validator to ensure it matches the dashboard.  
* docker-compose.yml and README.md.

## **Success Criteria**

* Successfully generate 1000+ realistic MES events.  
* Simulate a complete 24-hour factory operation.  
* Output events directly to NATS for consumption by FactoryOps.  
* Generate labeled defect images for VisionGuard.  
* Ensure the OEE calculator matches the dashboard's OEE calculations.  
* Ensure the simulation is repeatable via seeds.