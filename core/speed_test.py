import speedtest
import time
from datetime import datetime
import asyncio

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

def get_readable_file_size(size_in_bytes):
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    return f'{round(size_in_bytes, 2)}{SIZE_UNITS[min(index, len(SIZE_UNITS)-1)]}'

def speed_convert(size, byte=True):
    if not byte:
        size = size / 8
    units = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s"]
    power = 1024
    index = 0
    while size > power and index < len(units)-1:
        size /= power
        index += 1
    return f"{round(size, 2)} {units[index]}"

async def run_speedtest(client=None, message=None):
    if client and message:
        try:
            status_msg = await message.reply_text("🚀 Running Internet Speed Test...")
        except Exception as e:
            print(f"Failed to send initial message: {e}")
            return None
    
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        
        best = st.results.server
        server_info = f"🌍 {best['sponsor']} ({best['name']}, {best['country']})"
        
        if client and message:
            await status_msg.edit_text(f"🔍 Best server found:\n{server_info}\n\n📥 Testing download speed...")
        
        download = st.download()
        if client and message:
            await status_msg.edit_text(f"⬆️ Testing upload speed...")
        upload = st.upload()
        
        st.results.share()
        result = st.results.dict()
        
        results_text = (
            f"✅ SPEEDTEST by OOKLA:\n"
            f"📥 Download Speed: {speed_convert(result['download'], False)}\n"
            f"⬆️ Upload Speed: {speed_convert(result['upload'], False)}\n"
            f"📶 Ping: {result['ping']} ms\n"
            f"📤 Data Sent: {get_readable_file_size(result['bytes_sent'])}\n"
            f"📥 Data Received: {get_readable_file_size(result['bytes_received'])}\n"
            f"🕒 Timestamp: {result['timestamp']}\n\n"
            f"🌐 Server Info:\n"
            f"🏷 Name: {result['server']['name']}\n"
            f"📍 Country: {result['server']['country']}\n"
            f"👨‍💼 Sponsor: {result['server']['sponsor']}\n"
            f"🕰 Latency: {result['server']['latency']} ms\n\n"
            f"👤 Client Info:\n"
            f"🌐 IP Address: {result['client']['ip']}\n"
            f"📍 Country: {result['client']['country']}\n"
            f"🏢 ISP: {result['client']['isp']}\n"
            f"⭐ ISP Rating: {result['client'].get('isprating', 'N/A')}\n\n"
            f"📸 Shareable Result: {result['share'] if result['share'] else 'N/A'}"
        )
        
        # Clean up status message
        if client and message:
            try:
                await status_msg.delete()
            except Exception:
                pass
            
        return results_text

    except Exception as e:
        error_msg = f"❌ Error during speed test: {str(e)}"
        if client and message:
            try:
                await message.reply_text(error_msg)
            except Exception as reply_error:
                print(f"Failed to send error message: {reply_error}")
        else:
            print(error_msg)
        return None

async def main():
    await run_speedtest()

if __name__ == "__main__":
    asyncio.run(main())