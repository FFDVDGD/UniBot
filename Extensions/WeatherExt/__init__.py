'''WeatherExt 扩展：演示 API 服务注册与新增指令。'''

from typing import override

from pydantic import BaseModel, Field
from nonebot_plugin_alconna import Match
from nonebot_plugin_uninfo import Uninfo

from Scripts.Extensions import (
    Command,
    Extension,
    Service,
    SubCommand,
)


class WeatherConfig(BaseModel):
    '''天气扩展配置。'''

    api_key: str = Field(default='', description='天气服务 API Key')
    city: str = Field(default='Shanghai', min_length=1, description='默认城市')


# 创建唯一扩展实例，能力经实例装饰器登记
extension = Extension(config_model=WeatherConfig)


@extension.register_service
class WeatherService(Service):
    '''演示 API 服务：返回模拟天气数据。

    由 Loader 无参实例化并注册到扩展 api；配置经 extension.config 读取。
    '''

    name = 'weather'

    def get_weather(self, city: str | None = None) -> dict:
        '''返回指定城市（或默认城市）的模拟天气。'''
        default_city = extension.config_value.city
        target_city = city or default_city
        return {
            'city': target_city,
            'temperature': 26,
            'condition': '晴',
            'source': 'demo',
        }


@extension.register_command
class WeatherCommand(Command):
    '''天气指令。'''

    name = 'weather'
    description = '查询天气。'
    usage = '.weather [城市]'

    @override
    def declare(self) -> None:
        '''声明参数与子命令。'''
        self.register_option('city', str, default='Shanghai', description='要查询的城市')

    @override
    async def handler(self, session: Uninfo, city: Match[str]) -> str | None:
        '''处理 weather 主命令。

        可选参数声明了默认值（'Shanghai'），框架在构建时直接注入 Alconna，
        未提供时 `city.result` 即为默认值，可直接使用。
        '''
        assert extension.api is not None
        service = extension.api.get(WeatherService)
        if service is None:
            return None
        data = service.get_weather(city.result)
        return f'{data["city"]} 当前 {data["temperature"]}°C，{data["condition"]}！'

    class Today(SubCommand['WeatherCommand']):
        '''查询今天的天气。'''

        name = 'today'
        description = '查询今天的天气'

        @override
        async def handler(self) -> str | None:
            '''处理 weather today 子命令。'''
            assert extension.api is not None
            service = extension.api.get(WeatherService)
            if service is None:
                return None
            data = service.get_weather()
            return f'今天 {data["city"]}：{data["condition"]}，{data["temperature"]}°C！'