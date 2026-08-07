import random
from datetime import date
from hashlib import md5

from nonebot.plugin import PluginMetadata
from nonebot_plugin_uninfo import Uninfo

from Scripts.Config import config
from Scripts.Extensions import Command
from Scripts.Globals import render_template
from Scripts.Messages import messages
from Scripts.Utils import turn_message_text

__plugin_meta__ = PluginMetadata(
    name='今日人品',
    description='根据用户与日期生成稳定的今日人品和宜忌。',
    usage='.luck',
)


class LuckCommand(Command):
    '''查看今日人品值。'''

    name = 'luck'
    description = '查看今日人品值。'
    usage = '.luck'

    async def handler(self, session: Uninfo):
        luck_data = self.get_luck_data(session)
        return await turn_message_text(self.luck_handler(luck_data))

    async def image_handler(self, session: Uninfo) -> bytes:
        '''渲染今日人品为图片，返回 PNG 字节（由框架在图像模式发送）。'''
        luck_data = self.get_luck_data(session)
        return await render_template('Luck', (500, 0), **luck_data)

    def get_luck_data(self, session: Uninfo) -> dict:
        bad_things = messages.commands.luck.bad_things
        good_things = messages.commands.luck.good_things
        user_id = str(session.user.id)
        scene_id = str(session.scene.id)
        seed_hash = md5(f'{date.today()} {scene_id} {user_id}'.encode())
        random.seed(seed := int(seed_hash.hexdigest(), 16))
        luck_point = random.randint(10, 100)
        tips = messages.commands.luck.tip_low
        if luck_point > 90:
            tips = messages.commands.luck.tip_max
        elif luck_point > 60:
            tips = messages.commands.luck.tip_high
        elif luck_point > 30:
            tips = messages.commands.luck.tip_mid
        bad_thing = bad_things[(seed & int(scene_id.replace('-', '0'), 32)) % len(bad_things)]
        good_thing = good_things[(seed ^ int(scene_id.replace('-', '0'), 32)) % len(good_things)]
        if bad_thing.startswith(good_thing[:2]):
            bad_thing = bad_things[bad_things.index(bad_thing) - 1]
        return {
            'luck_point': luck_point,
            'tips': tips,
            'good_thing': good_thing,
            'bad_thing': bad_thing,
        }

    def luck_handler(self, data: dict):
        yield messages.commands.luck.result.format(point=data['luck_point'], tips=data['tips'])
        yield messages.commands.luck.good.format(thing=data['good_thing'])
        yield messages.commands.luck.bad.format(thing=data['bad_thing'])
