import asyncio

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class NotificationServerWorker(QObject):
    signal_back = pyqtSignal(int)

    def __init__(self, loop: asyncio.AbstractEventLoop, parent=None):
        super(NotificationServerWorker, self).__init__(parent)
        self.text = "Task1 not configured"
        self.loop = loop
        self.subscriber_writers = []

    @pyqtSlot(str)
    def broadcast(self, txt):
        for subscriber in self.subscriber_writers:
            caddr = subscriber.get_extra_info('peername')
            print(f"Send: {txt!r} to {caddr!r}")
            subscriber.write(bytes(txt, 'utf8'))
            await subscriber.drain()

    async def handle_message(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        if message[0] == "S": # From subscriber
            self.subscriber_writers.append(writer)
            print(f"Subscribed {addr!r}")

        """
        if message[0] == "P": # From publisher
            data = message[1:]
            for subscriber in self.subscriber_writers:
                caddr = subscriber.get_extra_info('peername')
                print(f"Send: {data!r} to {caddr!r}")
                subscriber.write(bytes(data,'utf8'))
                await subscriber.drain()
            writer.close()
        """

    async def start_server(self):
        subscriber_server = await asyncio.start_server(self.handle_message, "192.168.52.2", 9193)

        addrs = ', '.join(str(sock.getsockname()) for sock in subscriber_server.sockets)
        print(f'Serving on {addrs}')

        async with subscriber_server:
            await subscriber_server.serve_forever()

    def serve(self):
        asyncio.ensure_future(self.start_server(), loop=self.loop)