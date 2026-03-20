# Docker Desktop Installation Guide for Windows

## 📋 Prerequisites Check

Your system status:
- ✅ Windows 11 (compatible)
- ✅ Python 3.13.5 installed
- ✅ Node.js 24.14.0 installed
- ⏳ WSL 2 (Windows Subsystem for Linux) - Being installed

---

## 🚀 Installation Steps

### **Step 1: Ensure WSL 2 is Installed** (Already Running)
The system is installing WSL 2. Once complete, restart your computer.

To verify after restart:
```powershell
wsl --version
```

Should show: `WSL version: 2.x.x`

---

### **Step 2: Download Docker Desktop**

**Option A: Direct Download (Recommended)**
1. Go to: https://www.docker.com/products/docker-desktop
2. Click **"Download for Windows"**
3. Save the installer to your Downloads folder
4. Wait for download to complete (~750 MB)

**Option B: Direct Link (Latest Stable)**
```
https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe
```

---

### **Step 3: Install Docker Desktop**

1. **Open Windows Explorer** and navigate to your Downloads folder
2. **Double-click** `Docker Desktop Installer.exe`
3. **Windows SmartScreen Warning** (if shown):
   - Click **"More info"**
   - Click **"Run anyway"**
4. **Installation Window** will open:
   - ✅ Keep default settings
   - ✅ Click **"Install"**
5. **Enter Windows Password** when prompted (administrator access required)
6. **Wait for installation** (2-5 minutes)
7. **Restart Computer** when prompted

---

### **Step 4: Verify Installation**

After restart, open PowerShell and run:

```powershell
docker --version
docker run hello-world
```

Expected output:
```
Docker version 27.x.x, build xxxxx
Hello from Docker!
```

---

## 🐳 Starting Docker Services for FinShield AI

Once Docker is installed and running, start the project infrastructure:

```powershell
# Navigate to project
cd "C:\Users\gsuni\OneDrive\Desktop\AI_Project\Temp\AI-Financial-Intelligence-Fraud-Detection-\AI-Financial-Intelligence-Fraud-Detection-"

# Start services
docker compose up -d

# Verify services running
docker ps
```

Expected containers:
- ✅ `postgresql-16`
- ✅ `redis-7`
- ✅ `mailhog`

---

## 🔧 Troubleshooting

### Docker won't start after installation
**Solution**: 
1. Restart Windows
2. Open Docker Desktop from Start Menu (may take 1-2 minutes to start)
3. Check system tray for Docker icon
4. Try commands again in PowerShell

### "Permission Denied" error
**Solution**: 
1. Right-click PowerShell
2. Select "Run as Administrator"
3. Run docker commands again

### WSL Error after Docker install
**Solution**:
```powershell
# Update WSL kernel
wsl --update

# Set WSL 2 as default
wsl --set-default-version 2

# Restart Docker Desktop
```

### Disk space issues
Docker requires ~10 GB free space. Check:
```powershell
Get-Volume | Where-Object {$_.DriveLetter -eq 'C'} | Select-Object SizeRemaining, Size
```

---

## ✅ After Installation

Once Docker is running, execute the quick start:

```powershell
$projectRoot = "C:\Users\gsuni\OneDrive\Desktop\AI_Project\Temp\AI-Financial-Intelligence-Fraud-Detection-\AI-Financial-Intelligence-Fraud-Detection-"

# Start infrastructure
docker compose up -d

# Backend setup (in new PowerShell window)
Set-Location "$projectRoot\backend"
poetry run alembic upgrade head
poetry run python scripts/seed_data.py
poetry run uvicorn app.main:app --reload --port 8000

# Frontend setup (in another new PowerShell window)
Set-Location "$projectRoot\frontend"
npm run dev
```

Then open http://localhost:3000 and login!

---

## 📞 Need Help?

If Docker installation fails:
1. Check: https://docs.docker.com/desktop/troubleshoot/
2. Download older version: https://docs.docker.com/desktop/release-notes/
3. Full uninstall and reinstall

**Docker Desktop is essential** for running PostgreSQL, Redis, and MailHog without manual setup.

---

Last Updated: March 20, 2026
