import asyncio
import json
import datetime
from aiohttp import web

async def handle_index(request):
    return web.FileResponse('index.html')

async def handle_message(request):
    return web.FileResponse('message.html')

async def handle_static(request):
    file_path = request.match_info['file_path']
    return web.FileResponse(file_path)

async def handle_form(request):
    data = await request.post()
    message = {
        "datetime": str(datetime.datetime.now()),
        "username": data.get('username'),
        "message": data.get('message')
    }
    message_bytes = json.dumps(message).encode('utf-8')
    # Send message to UDP server
    transport, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: UDPClientProtocol(message_bytes),
        remote_addr=('127.0.0.1', 5000)
    )
    return web.HTTPFound('/')

class UDPClientProtocol:
    def __init__(self, message):
        self.message = message

    def connection_made(self, transport):
        transport.sendto(self.message)
        transport.close()

async def error_404(request, response):
    return web.FileResponse('error.html', status=404)

async def main():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_get('/message', handle_message)
    app.router.add_post('/message', handle_form)
    app.router.add_get('/static/{file_path}', handle_static)
    app.router.add_error_handler(404, error_404)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3000)
    await site.start()

async def udp_server():
    transport, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
        UDPServerProtocol,
        local_addr=('127.0.0.1', 5000)
    )

class UDPServerProtocol:
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        message = data.decode('utf-8')
        try:
            message_dict = json.loads(message)
            with open('storage/data.json', 'a') as f:
                json.dump({message_dict['datetime']: {"username": message_dict['username'], "message": message_dict['message']}}, f)
                f.write('\n')
        except json.JSONDecodeError:
            print("Error decoding JSON:", message)

async def start_servers():
    await asyncio.gather(main(), udp_server())

if __name__ == "__main__":
    asyncio.run(start_servers())
