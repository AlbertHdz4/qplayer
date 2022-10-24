
import socket

class PublisherClient:

    def __init__(self, server_host, server_port=9193):
        self.server_host = server_host
        self.server_port = server_port

    def publish(self, msg):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.server_host, self.server_port))
            s.sendall(b"P"+bytes(str(msg+"\r\n"),'utf8'))

class DummyPublisherClient:

    def __init__(self):
        pass

    def publish(self, msg):
        print(msg)

if __name__ == "__main__":

    p = PublisherClient("192.168.52.2")

    p.publish("Message 1")
    p.publish("Message 2")