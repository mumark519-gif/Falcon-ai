from __future__ import annotations
from app.platform.plugin_system import manager
from app.plugins.builtin import install_builtin_plugins
class FalconPluginRegistry:
    def initialize(self): install_builtin_plugins(); return manager.list()
registry=FalconPluginRegistry()
