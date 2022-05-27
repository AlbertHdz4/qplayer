import asyncio
import argparse


class NotificationServer:
    def __init__(self, server_address, server_port):
        self.subscriber_writers = []
        self.server_address = server_address
        self.server_port = server_port

    async def handle_message(self, reader, writer):
        data = await reader.readline()
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        # PROTOCOL: messages starting with S are requests for subscription
        #           messages starting with P are publications

        if message[0] == "S": # From subscriber
            self.subscriber_writers.append(writer)
            print(f"Subscribed {addr!r}")
            print("===Current Clients===")
            for subscriber in self.subscriber_writers:
                caddr = subscriber.get_extra_info('peername')
                print(f"{caddr!r}")
            print("===Current Clients===")

        if message[0] == "P": # From publisher
            data = message[1:]
            dead_subscribers = [] # list of dead clients
            for subscriber in self.subscriber_writers:
                caddr = subscriber.get_extra_info('peername')
                print(f"Send: {data!r} to {caddr!r}")
                subscriber.write(bytes(data,'utf8'))
                try:
                    await subscriber.drain()
                except ConnectionResetError:
                    print(f"Client from {caddr!r} removed")
                    dead_subscribers.append(subscriber)

            # We remove the dead clients in a separate loop to not make a mess
            for dead_subscriber in dead_subscribers:
                self.subscriber_writers.remove(dead_subscriber)
            writer.close()

    async def main(self):
        suscriber_server = await asyncio.start_server(self.handle_message, self.server_address, self.server_port)

        addrs = ', '.join(str(sock.getsockname()) for sock in suscriber_server.sockets)
        print(f'Serving on {addrs}')

        async with suscriber_server:
            await suscriber_server.serve_forever()

    def start(self):
        asyncio.run(self.main())

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Notification Server')
    parser.add_argument('--address', help='IP address to bind the server to.')
    parser.add_argument('--port', help='Port to operate the server on', nargs='?', default=9193, type=int)
    args = parser.parse_args()

    print(args)

    ns = NotificationServer(args.address, args.port)
    ns.start()