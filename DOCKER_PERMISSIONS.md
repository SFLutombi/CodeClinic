# 🔧 Docker Permissions Fix

## The Problem
When you run `./scripts/start-codeclinic.sh`, you might see:
```
[ERROR] Docker permission denied!
```

This happens because Docker requires special permissions to access the Docker daemon.

## ✅ The Solution

### **Option 1: Fix Permissions (Recommended)**
```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and log back in (or restart your computer)
# Then try again:
./scripts/start-codeclinic.sh
```

### **Option 2: Quick Fix (Temporary)**
```bash
# Run with sudo (not recommended for production)
sudo ./scripts/start-codeclinic.sh
```

### **Option 3: New Terminal Session**
Sometimes just opening a new terminal works:
```bash
# Open a new terminal and try:
./scripts/start-codeclinic.sh
```

## 🔍 Why This Happens

1. **Docker Group**: Your user needs to be in the `docker` group
2. **Session Restart**: Group changes require a new login session
3. **Security**: Docker has special permissions for security reasons

## ✅ Verify It's Fixed

After fixing, test with:
```bash
docker ps
```

If this works without `sudo`, you're good to go!

## 🚀 Then Start CodeClinic

```bash
./scripts/start-codeclinic.sh
```

This will start:
- 4 ZAP workers in parallel
- Redis for coordination  
- Backend API with parallel scanning
- Frontend application

**Performance**: Up to 4-8x faster scanning! 🚀
