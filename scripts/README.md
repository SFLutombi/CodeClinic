# CodeClinic Scripts

This directory contains automation scripts for easy CodeClinic setup and management.

## 🚀 Quick Start Scripts

### 1. Docker Compose Startup (Recommended)
```bash
./scripts/start-docker.sh
```
**Best for**: Quick setup with minimal configuration
- Starts all services with Docker Compose
- Automatic health checks
- Easy cleanup with Ctrl+C

### 2. Manual Setup Script
```bash
./scripts/start-codeclinic.sh
```
**Best for**: Development and customization
- Manual Docker container management
- Individual service control
- Detailed logging and debugging

## 📋 What Each Script Does

### `start-docker.sh`
- ✅ Checks Docker and Docker Compose installation
- ✅ Verifies Docker permissions
- ✅ Starts all services with `docker-compose up -d`
- ✅ Tests service health
- ✅ Provides cleanup on exit

### `start-codeclinic.sh`
- ✅ Checks Docker installation and permissions
- ✅ Starts Redis container
- ✅ Starts single ZAP instance
- ✅ Installs Python dependencies
- ✅ Starts backend and frontend manually
- ✅ Tests scanning system
- ✅ Provides cleanup on exit

## 🔧 Prerequisites

Both scripts require:
- **Docker** installed and running
- **Docker Compose** (for start-docker.sh)
- **Internet connection** for downloading images
- **Ports 3000, 8000, 8080, 6379** available

## 🛠️ Troubleshooting

### Docker Permission Issues
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or restart
# Or run with sudo (not recommended)
sudo ./scripts/start-docker.sh
```

### Port Conflicts
```bash
# Check what's using the ports
sudo netstat -tulpn | grep :3000
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :8080
sudo netstat -tulpn | grep :6379

# Stop conflicting services
sudo systemctl stop [service-name]
```

### Clean Restart
```bash
# Stop all containers
docker-compose down

# Remove all containers and images
docker system prune -a

# Restart with script
./scripts/start-docker.sh
```

## 📊 Service URLs

After successful startup:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ZAP Interface**: http://localhost:8080
- **Health Check**: http://localhost:8000/health

## 🎯 Usage Tips

1. **First Time**: Use `start-docker.sh` for easiest setup
2. **Development**: Use `start-codeclinic.sh` for more control
3. **Production**: Use `docker-compose up -d` directly
4. **Debugging**: Check logs with `docker-compose logs -f`
5. **Cleanup**: Press Ctrl+C or run `docker-compose down`
