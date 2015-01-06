import time
import rpyc
from rpyc.utils.server import ThreadedServer
from threading import Thread


class A():
    def blah(self):
        print 'asdf'

a = A()

class ServerService(rpyc.Service):
    def exposed_bar(self):
        return a

# start the rpyc server
server = ThreadedServer(ServerService, port=12345,
                        protocol_config={"allow_all_attrs": True,
                                         "allow_setattr": True})
t = Thread(target=server.start)
t.daemon = True
t.start()

while True:
    A.func()
    time.sleep(0.5)



