# Ansible Guide - DevOps Toolbox

## 1. Directory Structure

```text
ansible/
├── ansible.cfg                 # Global configuration & SSH pipelining
├── inventory/
│   ├── hosts.yml               # Node inventories (production, staging, monitoring)
│   └── group_vars/
│       └── all.yml             # Global baseline & security variables
├── roles/
│   ├── common/                 # Baseline packages, SSH hardening, UFW, Chrony
│   ├── docker_host/            # Docker CE daemon security & storage drivers
│   └── monitoring_agent/       # Node Exporter service unit and telemetry
└── playbooks/
    ├── site.yml                # Full infrastructure deployment
    ├── hardening.yml           # Kernel sysctl & filesystem security
    └── backup.yml              # Database backup automation & retention
```

---

## 2. Inventory Architecture

Managed hosts are organized in groups:
- **`production`**: Live application instances and PostgreSQL database hosts.
- **`staging`**: Pre-production integration nodes.
- **`monitoring`**: Telemetry and metrics aggregation hosts.

---

## 3. Playbook Execution Commands

### A. Syntax & Dry-Run Validation
Verify syntax and check changes without executing on live infrastructure:
```bash
# Check YAML syntax
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml --syntax-check

# Dry-run check mode with diffs
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml --check --diff
```

### B. Deploy Full Infrastructure
```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/site.yml
```

### C. Execute Hardening Playbook Only
```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/hardening.yml
```

### D. Execute Automated Backups
```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/backup.yml
```

---

## 4. Security Hardening Specs (CIS / ANSSI)
- **Port:** Configured to non-standard port 2222.
- **Root Login:** `PermitRootLogin no`.
- **Authentication:** `PasswordAuthentication no` (strictly SSH public key authentication).
- **Ciphers:** Strict modern cryptography (`chacha20-poly1305@openssh.com`, `aes256-gcm@openssh.com`).
- **Firewall Policy:** Default-deny incoming on UFW.
