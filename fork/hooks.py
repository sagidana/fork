class Hooks():
    registry = {}

    @staticmethod
    def register(name, callback):
        if name not in Hooks.registry:
            Hooks.registry[name] = []

        Hooks.registry[name].append(callback)

    @staticmethod
    def unregister(name, callback):
        if name not in Hooks.registry: return

        Hooks.registry[name].remove(callback)

    @staticmethod
    def execute(name, args):
        if name not in Hooks.registry: return

        for cb in Hooks.registry[name]: cb(args)

