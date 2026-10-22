# Cluster capacity and HA

- `prod-west-01` is the payments cluster (HA + DRS on, 8 hosts).
- `prod-east-01` hosts checkout (HA + DRS on, 6 hosts).
- `lab-shared` has HA off. Treat lab power actions as low risk.
- Nutanix `prism-prod-a` is the primary AHV cluster (4 nodes, AOS 6.8). Memory at 74% is elevated; CPU at 61% is normal.
- Snapshot-backed VMs (`checkout-web-01`, `batch-etl-01`) should be consolidated before storage work.
- If Nutanix storage used exceeds 70%, pause non-prod snapshots and review compression ratio (healthy ~2.0).
