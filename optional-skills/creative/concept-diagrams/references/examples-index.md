# Examples Index & Request-to-Type Quick Reference

## Examples Reference

The `examples/` directory ships 15 complete, tested diagrams. Browse them for working patterns before writing a new diagram of a similar type:

| File | Type | Demonstrates |
|------|------|--------------|
| `hospital-emergency-department-flow.md` | Flowchart | Priority routing with semantic colors |
| `feature-film-production-pipeline.md` | Flowchart | Phased workflow, horizontal sub-flows |
| `automated-password-reset-flow.md` | Flowchart | Auth flow with error branches |
| `autonomous-llm-research-agent-flow.md` | Flowchart | Loop-back arrows, decision branches |
| `place-order-uml-sequence.md` | Sequence | UML sequence diagram style |
| `commercial-aircraft-structure.md` | Physical | Paths, polygons, ellipses for realistic shapes |
| `wind-turbine-structure.md` | Physical cross-section | Underground/above-ground separation, color coding |
| `smartphone-layer-anatomy.md` | Exploded view | Alternating left/right labels, layered components |
| `apartment-floor-plan-conversion.md` | Floor plan | Walls, doors, proposed changes in dotted red |
| `banana-journey-tree-to-smoothie.md` | Narrative journey | Winding path, progressive state changes |
| `cpu-ooo-microarchitecture.md` | Hardware pipeline | Fan-out, memory hierarchy sidebar |
| `sn2-reaction-mechanism.md` | Chemistry | Molecules, curved arrows, energy profile |
| `smart-city-infrastructure.md` | Hub-spoke | Semantic line styles per system |
| `electricity-grid-flow.md` | Multi-stage flow | Voltage hierarchy, flow markers |
| `ml-benchmark-grouped-bar-chart.md` | Chart | Grouped bars, dual axis |

Load any example with:
```
skill_view(name="concept-diagrams", file_path="examples/<filename>")
```

## Quick Reference: What to Use When

| User says | Diagram type | Suggested colors |
|-----------|--------------|------------------|
| "show the pipeline" | Flowchart | gray start/end, purple steps, red errors, teal deploy |
| "draw the data flow" | Data pipeline (left-right) | gray sources, purple processing, teal sinks |
| "visualize the system" | Structural (containment) | purple container, teal services, coral data |
| "map the endpoints" | API tree | purple root, one ramp per resource group |
| "show the services" | Microservice topology | gray ingress, teal services, purple bus, coral workers |
| "draw the aircraft/vehicle" | Physical | paths, polygons, ellipses for realistic shapes |
| "smart city / IoT" | Hub-spoke integration | semantic line styles per subsystem |
| "show the dashboard" | UI mockup | dark screen, chart colors: teal, purple, coral for alerts |
| "power grid / electricity" | Multi-stage flow | voltage hierarchy (HV/MV/LV line weights) |
| "wind turbine / turbine" | Physical cross-section | foundation + tower cutaway + nacelle color-coded |
| "journey of X / lifecycle" | Narrative journey | winding path, progressive state changes |
| "layers of X / exploded" | Exploded layer view | vertical stack, alternating labels |
| "CPU / pipeline" | Hardware pipeline | vertical stages, fan-out to execution ports |
| "floor plan / apartment" | Floor plan | walls, doors, proposed changes in dotted red |
| "reaction mechanism" | Chemistry | atoms, bonds, curved arrows, transition state, energy profile |
