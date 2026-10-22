# Change window and access

- Production power actions: 01:00–04:00 IST only, with a change ticket.
- Lab cluster `lab-shared` can be changed any time.
- InfraGPT talks to **mock** vCenter and Prism APIs in this repo. It must not be pointed at a live hypervisor without a separate credentials vault and change control.
- Always retrieve the VM with `get_vm` before `power_action`.
- After any simulated action, state that it was a mock and list the resulting power state.
