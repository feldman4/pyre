# rpyc client
import rpyc


class ClientService(rpyc.Service):
    def exposed_foo(self):
        return "foo"

conn = rpyc.connect("localhost", 12345, service = ClientService)

bgsrv = rpyc.BgServingThread(conn)

def blah():
    print 'asdf'