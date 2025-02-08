import os
import sys
import importlib.util
import logging

logger = logging.getLogger(__name__)

def get_plugins_dir(default_dir='plugins'):
    if getattr(sys, 'frozen', False):
        # When running as an executable, use the folder alongside the exe.
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, default_dir)

def load_plugins(plugin_api, plugins_dir=None):
    if plugins_dir is None:
        plugins_dir = get_plugins_dir()
    if not os.path.exists(plugins_dir):
        logger.info(f"No plugins directory found at '{plugins_dir}'.")
        return
    for filename in os.listdir(plugins_dir):
        if (filename.endswith('.py') and not filename.startswith('_') and 
            filename != 'plugin_manager.py'):
            module_path = os.path.join(plugins_dir, filename)
            module_name = os.path.splitext(filename)[0]
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                if hasattr(module, 'register_plugin'):
                    module.register_plugin(plugin_api)
                    logger.info(f"Plugin '{module_name}' loaded successfully.")
                else:
                    logger.warning(f"Plugin '{module_name}' does not have a register_plugin() function.")
            except Exception as e:
                logger.error(f"Error loading plugin '{module_name}': {e}")
