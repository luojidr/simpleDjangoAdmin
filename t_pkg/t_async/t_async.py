import traceback
import socket
from selectors import DefaultSelector, EVENT_WRITE, EVENT_READ


from asyncio import futures, tasks

selector = DefaultSelector()
stopped = False
urls_todo = ["/user/messageCount/3070"]


class Crawler:
    def __init__(self, url):
        self.url = url
        self.sock = None
        self.response = b""

    def fetch(self):
        self.sock = socket.socket()
        self.sock.setblocking(True)

        try:
            self.sock.connect(("cuth.com", 443))
        except BlockingIOError:
            print(traceback.format_exc())

        selector.register(self.sock.fileno(), EVENT_WRITE, self.connected)

    def connected(self, key, mask):
        selector.unregister(key.fd)
        self.sock.send("GET {0} HTTP/1.1\r\n".format(self.url).encode())

        self.sock.send("Connection:keep-alive\r\n".encode())
        self.sock.send("application/json, text/plain, */*\r\n".encode())
        self.sock.send("authorization: WX_JWT\r\n".encode())
        self.sock.send("User-Agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Mobile Safari/537.36\r\n".encode())
        selector.register(key.fd, EVENT_READ, self.read_response)

    def read_response(self, key, mask):
        global stopped

        chunk = self.sock.recv(4096)
        if chunk:
            self.response += chunk
        else:
            selector.unregister(key.fd)
            urls_todo.remove(self.url)

            if not urls_todo:
                stopped = True

            print(self.url, ":", self.response)


def loop():
    while not stopped:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback(event_key, event_mask)


if __name__ == "__main__":
    import time
    start = time.time()

    for url in urls_todo:
        crawler = Crawler(url)
        crawler.fetch()


    loop()
    print(time.time() - start)






