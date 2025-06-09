class PluginAPI:
    def __init__(self, app):
        self.app = app

    def add_tab(self, title, frame):
        self.app.add_plugin_tab(title, frame)

    def register_hook(self, hook_name, callback):
        self.app.hooks.register(hook_name, callback)

    def trigger_hook(self, hook_name, *args, **kwargs):
        self.app.hooks.trigger(hook_name, *args, **kwargs)

    def collect(self, hook_name, *args, **kwargs):
        return self.app.hooks.collect(hook_name, *args, **kwargs)

    def get_main_window(self):
        return self.app.root
