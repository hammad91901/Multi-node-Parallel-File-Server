@echo off
echo Starting Multi-Node File Server Setup...
echo.
echo This will start 3 server nodes and a load balancer
echo.
echo Starting Node 1 on port 8080...
start "Node 1" cmd /k "python server/enhanced_server.py --port 8080 --node-id node1"
timeout /t 2 /nobreak >nul

echo Starting Node 2 on port 8081...
start "Node 2" cmd /k "python server/enhanced_server.py --port 8081 --node-id node2"
timeout /t 2 /nobreak >nul

echo Starting Node 3 on port 8082...
start "Node 3" cmd /k "python server/enhanced_server.py --port 8082 --node-id node3"
timeout /t 2 /nobreak >nul

echo Starting Load Balancer on port 8000...
start "Load Balancer" cmd /k "python server/load_balancer.py --port 8000"

echo.
echo All nodes started!
echo Connect to load balancer at localhost:8000
echo Or connect directly to nodes at localhost:8080, 8081, 8082
pause

