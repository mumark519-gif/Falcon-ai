from __future__ import annotations
from app.platform.plugin_system import Plugin, manager

def install_builtin_plugins():
    manager.register(Plugin("core-research","1.0.0","Research and source synthesis",{}))
    manager.register(Plugin("core-coding","1.0.0","Repository and coding workflows",{}))
    manager.register(Plugin("core-multimodal","1.0.0","Image, audio, video and document workflows",{}))
    manager.register(Plugin("core-enterprise","1.0.0","Enterprise policy, billing and jobs",{}))
