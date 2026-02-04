#!/bin/bash
echo "Starting ClusterIQ Frontend..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi
npm run dev

