#!/bin/bash
# Quick restart script for backend

echo "🔄 Stopping backend..."
pkill -f "python.*main.py"
sleep 2

echo "🚀 Starting backend..."
cd /home/thang/Documents/ecommerce-backend
./run.sh &

sleep 2
echo "✅ Backend restarted!"
echo "📊 Check status with: ps aux | grep main.py"
