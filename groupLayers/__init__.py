# -*- coding: utf-8 -*-


def classFactory(iface):
    from .plugin import MainPlugin
    return MainPlugin(iface)
