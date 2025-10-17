from aiohttp import web
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

async def health_check(request):
    return web.Response(text="Bot is running!")

async def run_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get('PORT', 3000))
    logger.info(f"Starting health check server on port {port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    logger.info(f"Server started successfully on port {port}")

def start_server():
    loop = asyncio.get_event_loop()
    loop.create_task(run_server())