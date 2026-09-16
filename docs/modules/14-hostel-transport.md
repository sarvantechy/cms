# Hostel and Transport

**Status:** Planned and hidden from current navigation.

## Purpose
Manage accommodation, beds, mess, visitors, incidents, vehicles, routes, stops, capacity, and effective-dated student allocations.

## Roles
- Hostel Warden: manage buildings, occupancy, attendance, visitors, and incidents.
- Transport Manager: manage vehicles, routes, stops, and allocations.
- Student/Guardian: view own or linked allocations.

## Workflow
1. Configure facilities, capacity, routes, and stops.
2. Request and approve effective-dated allocations.
3. Record operational attendance, visitors, and incidents.
4. Link applicable charges to the fees module.
5. End or transfer allocations without deleting history.

## Core Rules
- Capacity is enforced transactionally.
- Historical allocations remain effective-dated.
- Operational roles cannot access unrelated student records.

## Data
HostelBuilding, Room, Bed, HostelAllocation, MessPlan, Visitor, Incident, Vehicle, Route, Stop, and TransportAllocation.

## Current UI Behavior
No hostel or transport screen exists.

## Production Completion
Build facility maps, allocation queues, attendance/visitor workflows, route planning, capacity views, student self-service, and fee integration.

## Acceptance Criteria
- Beds and vehicle capacity cannot be oversubscribed.
- Allocations are tenant and student scoped.
- Charges reconcile with active effective allocations.
