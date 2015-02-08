import types


class CentralDispatch(object):
    def __init__(self):
        # make weakly referenced
        self.targets = {}
        self.listeners = {}

    def modify_target(self, target_method):
        def modified_func(*args, **kwargs):
            central_dispatcher = target_method.im_self.__getattribute__("_central_dispatch")
            central_dispatcher.notify(target_method)
            # kludge, not sure why self argument is supplied twice
            return target_method(*args[1:], **kwargs)
        return modified_func

    def update_in_place(self, new_method, old_method):
        parent = old_method.im_self
        method_name = old_method.__str__().split('.')[1].split(' ')[0]
        parent.__setattr__(method_name, types.MethodType(new_method, parent))
        parent._central_dispatch = self

    def watch(self, target_method, listener):
        # modify function to contain listener
        if "_central_dispatch" not in target_method.__dict__.keys():
            self.update_in_place(self.modify_target(target_method), target_method)
        # track listeners associated with target method
        if target_method in self.listeners.keys():
            self.targets[target_method].append(listener)
        else:
            self.targets[target_method] = [listener]
        # track target methods associated with listener
        if listener in self.listeners.keys():
            self.listeners[listener].append(target_method)
        else:
            self.listeners[listener] = [target_method]

    def stop_listening(self, listener):
        if listener in self.listeners.keys():
            for target_method in self.listeners[listener]:
                self.targets[target_method].remove(listener)
        self.listeners.pop(listener)

    def notify(self, target_method):
        # figure out calling method
        for listener in self.targets[target_method]:
            listener()

central_dispatch = CentralDispatch()


def main():
    class Test(object):
        def add(self, a):
            return a + 2

        def sub(self, b):
            return b - 2

    class Listener(object):
        def subscribe(self, target_method):
            central_dispatch.watch(target_method, self.heard_it)

        def heard_it(self):
            print "heard it"

    l = Listener()
    t = Test()

    l.subscribe(t.add)
    t.add(3)

    central_dispatch.stop_listening(l.heard_it)
    print "the sound of silence"
    t.add(4)

    print "central_dispatch.targets = {}".format(central_dispatch.targets)
    print "central_dispatch.listeners = {}".format(central_dispatch.listeners)


if __name__ == '__main__':
    main()

#
# def convert_func(foo):
#     def new_func(*args, **kwargs):
#         fname = foo.__str__().split('.')[1].split(' ')[0]
#         listeners = foo.im_self.__getattribute__("_listeners_" + fname)
#         output = foo(*args[1:], **kwargs)
#         for listener in listeners:
#             # print listener
#             listener()
#         return output
#
#     return new_func
#
# class Test(object):
#     def add(self, a):
#         print self
#         print a
#         return a + 2
#     def sub(self, b):
#         return b - 2
#
#
# class Listener(object):
#     def subscribe(self, target_method):
#         parent = target_method.im_self
#         method_name = target_method.__str__().split('.')[1].split(' ')[0]
#         listener_name = "_listeners_" + method_name
#         if listener_name in parent.__dict__.keys():
#             parent.__getattr__(listener_name).append(self.heard_it)
#         else:
#             parent.__setattr__(listener_name, [self.heard_it])
#         parent.__setattr__(method_name, types.MethodType(convert_func(target_method), parent))
#     def heard_it(self):
#         print "heard it"
#
# l = Listener()
# t = Test()
#
# l.subscribe(t.add)
# t.add(3)