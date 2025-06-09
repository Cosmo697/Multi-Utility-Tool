class Hooks:
    def __init__(self):
        self._hooks = {}

    def register(self, hook_name, callback):
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def trigger(self, hook_name, *args, **kwargs):
        for callback in self._hooks.get(hook_name, []):
            callback(*args, **kwargs)

    def collect(self, hook_name, *args, **kwargs):
        results = []
        for callback in self._hooks.get(hook_name, []):
            try:
                results.append(callback(*args, **kwargs))
            except Exception as exc:
                import logging
                logging.getLogger(__name__).error("Hook %s failed: %s", hook_name, exc)
        return results
