# Nutanix predictive disk failure

Prism alert "Disk in node reported predictive failure" is a hardware replacement, not a reboot.

1. Open `nutanix_alerts` and confirm severity is critical.
2. Check `nutanix_capacity`. Do not start a disk pull if storage used is above 85% or free space is under 10 TB on a 4-node cluster.
3. Put the node in maintenance through Prism (AHV). Wait until data is rebuilt.
4. Replace the disk, then exit maintenance. Replication lag on `prism-dr-b` should stay under 5 minutes.
5. CVM memory above 80% is a separate warning — do not reboot the CVM as a disk fix.
