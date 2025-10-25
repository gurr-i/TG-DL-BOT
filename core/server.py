from aiohttp import web
import asyncio
import os
import json
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Server metrics
server_metrics = {
    "start_time": time.time(),
    "requests_count": 0,
    "last_request": None
}

async def health_check(request):
    """Basic health check endpoint."""
    server_metrics["requests_count"] += 1
    server_metrics["last_request"] = datetime.now().isoformat()
    
    return web.Response(
        text="✅ Telegram Message Saver Bot is running!",
        content_type="text/plain"
    )

async def metrics_endpoint(request):
    """Detailed metrics endpoint."""
    try:
        from .performance import performance_optimizer
        perf_metrics = performance_optimizer.get_metrics()
    except ImportError:
        perf_metrics = {"error": "Performance metrics not available"}
    
    uptime = time.time() - server_metrics["start_time"]
    
    metrics = {
        "status": "healthy",
        "uptime_seconds": round(uptime, 2),
        "uptime_formatted": f"{int(uptime//3600)}h {int((uptime%3600)//60)}m {int(uptime%60)}s",
        "server": {
            "requests_count": server_metrics["requests_count"],
            "last_request": server_metrics["last_request"]
        },
        "performance": perf_metrics,
        "timestamp": datetime.now().isoformat()
    }
    
    return web.Response(
        text=json.dumps(metrics, indent=2),
        content_type="application/json"
    )

async def status_endpoint(request):
    """Simple status endpoint for monitoring."""
    return web.Response(
        text=json.dumps({
            "status": "ok",
            "service": "telegram-message-saver-bot",
            "version": "2.0.0",
            "timestamp": datetime.now().isoformat()
        }),
        content_type="application/json"
    )

async def run_server():
    """Start the health check and metrics server."""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    app.router.add_get('/metrics', metrics_endpoint)
    app.router.add_get('/status', status_endpoint)
    
    # Add CORS headers for web access
    async def add_cors_headers(request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    app.middlewares.append(add_cors_headers)
    
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"[SERVER] Starting health check server on port {port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"[OK] Health check server running on http://0.0.0.0:{port}")
    logger.info(f"[METRICS] Metrics available at http://0.0.0.0:{port}/metrics")

def start_server():
    """Start server in the current event loop."""
    loop = asyncio.get_event_loop()
    loop.create_task(run_server())