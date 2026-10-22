# VM power-cycle runbook (vCenter)

Use this when a guest is hung, not when storage is the root cause.

1. Confirm the VM in vCenter (`get_vm`). Record host, cluster, and whether a snapshot exists.
2. If the guest still answers ping, prefer a graceful shutdown from the OS.
3. If it does not, take a snapshot only when disk space on the datastore is above 20% free.
4. Issue `power_action` with `reset` for a hung OS. Use `off` then `on` if reset is blocked by VMware Tools.
5. After boot, check IP and application health. Do not leave lab VMs powered on overnight.
6. Never power-cycle both nodes of an HA pair at the same time (`payments-api-01` and `payments-api-02`).
