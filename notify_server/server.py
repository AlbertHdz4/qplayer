import asyncio


class NotificationServer:
    def __init__(self):
        self.subscriber_writers = []

    async def handle_message(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        if message[0] == "S": # From subscriber
            self.subscriber_writers.append(writer)
            print(f"Subscribed {addr!r}")

        if message[0] == "P": # From publisher
            data = message[1:]
            for subscriber in self.subscriber_writers:
                caddr = subscriber.get_extra_info('peername')
                print(f"Send: {data!r} to {caddr!r}")
                subscriber.write(bytes(data,'utf8'))
                await subscriber.drain()
            writer.close()

    async def main(self):
        suscriber_server = await asyncio.start_server(self.handle_message, "localhost", 9193)

        addrs = ', '.join(str(sock.getsockname()) for sock in suscriber_server.sockets)
        print(f'Serving on {addrs}')

        async with suscriber_server:
            await suscriber_server.serve_forever()

    def start(self):
        asyncio.run(self.main())


ns = NotificationServer()
ns.start()