# 🔄 Workspace Restoration Guide

**Last Backup:** 2026-03-13  
**Backup Location:** `hsidrive:/OpenClaw_Backups/`

---

## Quick Restore (If You Have rclone Configured)

### Step 1: Verify rclone Access
```bash
rclone listremotes
# Should show: hsidrive:
```

If `hsidrive` is missing, reconfigure:
```bash
rclone config
# Follow prompts to add Google Drive remote named "hsidrive"
```

---

### Step 2: Create Fresh Workspace Directory
```bash
# Option A: Restore to same location (wipe existing)
rm -rf /root/.openclaw/workspace
mkdir -p /root/.openclaw/workspace

# Option B: Restore to new location (keep existing as backup)
mkdir -p /root/.openclaw/workspace_restored
```

---

### Step 3: Download and Extract Main Backup
```bash
cd /root/.openclaw

# Download the backup
rclone copy hsidrive:/OpenClaw_Backups/workspace_backup_2026-03-13.tar.gz .

# Extract it
tar -xzf workspace_backup_2026-03-13.tar.gz -C workspace/

# Clean up the tarball
rm workspace_backup_2026-03-13.tar.gz
```

---

### Step 4: Restore Memory Files
```bash
# Download memory folder
rclone copy hsidrive:/OpenClaw_Backups/memory/ /root/.openclaw/workspace/memory/
```

---

### Step 5: Reinstall Dependencies
```bash
cd /root/.openclaw/workspace

# Install Node.js dependencies
npm install

# Verify Python is available
python3 --version
pip3 --version
```

---

### Step 6: Verify Restoration
```bash
# Check key files exist
ls -la /root/.openclaw/workspace/SOUL.md
ls -la /root/.openclaw/workspace/USER.md
ls -la /root/.openclaw/workspace/memory/

# Check OpenClaw status
openclaw status

# List workspace contents
ls -la /root/.openclaw/workspace/
```

---

## Full Restore (If Starting from Scratch)

### Prerequisites

#### 1. Install OpenClaw
```bash
npm install -g openclaw
```

#### 2. Install rclone
```bash
# Linux
curl https://rclone.org/install.sh | sudo bash

# macOS
brew install rclone
```

#### 3. Configure Google Drive in rclone
```bash
rclone config
```
Follow the prompts:
1. `n` → New remote
2. Name: `hsidrive`
3. Storage type: `google drive`
4. Accept defaults for client ID/secret
5. Scope: `drive` (full access)
6. Complete OAuth flow in browser
7. Confirm and save

---

### Restore Steps

```bash
# 1. Create workspace directory
mkdir -p /root/.openclaw/workspace
cd /root/.openclaw/workspace

# 2. Download backup
rclone copy hsidrive:/OpenClaw_Backups/workspace_backup_2026-03-13.tar.gz .

# 3. Extract
tar -xzf workspace_backup_2026-03-13.tar.gz

# 4. Restore memory files
mkdir -p memory
rclone copy hsidrive:/OpenClaw_Backups/memory/ ./memory/

# 5. Install dependencies
npm install

# 6. Verify
openclaw status
ls -la
```

---

## Post-Restore Checklist

- [ ] OpenClaw gateway running: `openclaw gateway status`
- [ ] Key identity files present: `SOUL.md`, `USER.md`, `IDENTITY.md`
- [ ] Memory files restored: `ls memory/`
- [ ] Python dependencies available (if needed): `pip3 list`
- [ ] Node dependencies installed: `ls node_modules/`
- [ ] Cron jobs still active: `openclaw cron list`
- [ ] Test a simple command: `openclaw --version`

---

## Troubleshooting

### rclone says "remote not found"
```bash
rclone config
# Re-add the hsidrive remote
```

### Permission denied on extract
```bash
sudo chown -R $USER:$USER /root/.openclaw/workspace
```

### npm install fails
```bash
# Check Node version
node --version  # Should be v18+

# Clear cache and retry
npm cache clean --force
npm install
```

### Memory files missing
```bash
# Manually download each file
rclone copy hsidrive:/OpenClaw_Backups/memory/2026-03-10-hsi-analyzer.md ./memory/
# ... repeat for other files
```

---

## Backup Schedule

Current backups are **manual**. To automate:

```bash
# Add to crontab (weekly, Sundays at 2 AM)
crontab -e

# Add this line:
0 2 * * 0 cd /root/.openclaw/workspace && tar --exclude='node_modules' --exclude='.git' --exclude='__pycache__' -czf backup_$(date +\%Y-\%m-\%d).tar.gz . && rclone copy backup_*.tar.gz hsidrive:/OpenClaw_Backups/
```

---

## Contact / Notes

- **Backup remote:** `hsidrive` (Google Drive)
- **Backup folder:** `/OpenClaw_Backups/`
- **Last verified:** 2026-03-13

---

*Keep this file with your important documents. It's your recovery key.*
