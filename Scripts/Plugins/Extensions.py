from nonebot import require

require('nonebot_plugin_uninfo')
require('nonebot_plugin_alconna')

from Scripts.Extensions import command_manager, extension_manager


extension_manager.load()
command_manager.build()