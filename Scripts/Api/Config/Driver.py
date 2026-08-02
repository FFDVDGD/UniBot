'''NoneBot DRIVER 字段的解析与维护工具。

负责在安装/卸载适配器时，自动维护 `.env` 中 DRIVER 的额外驱动项。
所有写操作通过 `config_manager` 落盘。
'''

from Scripts.Managers import config_manager

from .Adapters import ADAPTER_DRIVERS, BASE_DRIVER


def get_required_drivers(module_name: str) -> list[str]:
    '''获取指定适配器模块所需的额外驱动列表'''
    return ADAPTER_DRIVERS.get(module_name, [])


def parse_driver(driver_value: str | list | None) -> list[str]:
    '''将 DRIVER 配置解析为驱动列表'''
    if not driver_value:
        return [BASE_DRIVER]
    items = driver_value if isinstance(driver_value, list) else driver_value.split('+')
    drivers = []
    for item in items:
        item = item.strip()
        if item:
            drivers.append(item)
    if BASE_DRIVER not in drivers:
        drivers.append(BASE_DRIVER)
    return drivers


def format_driver(drivers: list[str]) -> str:
    '''将驱动列表格式化为 DRIVER 字符串'''
    return '+'.join(drivers)


def merge_driver(required_drivers: list[str]) -> tuple[str, list[str]]:
    '''
    将所需驱动合并到当前 DRIVER 配置中。
    返回 (新 DRIVER 字符串, 新增的驱动列表)。
    '''
    current = config_manager.environment.get('DRIVER', BASE_DRIVER)
    current_drivers = parse_driver(current)
    added = [driver for driver in required_drivers if driver not in current_drivers]
    if not added:
        return current, []
    new_drivers = current_drivers + added
    new_value = format_driver(new_drivers)
    config_manager.update_env({'DRIVER': new_value})
    return new_value, added


def shrink_driver(redundant_drivers: list[str]) -> tuple[str, list[str]]:
    '''
    从当前 DRIVER 配置中移除多余驱动（前提：剩余已注册适配器都不再需要）。
    返回 (新 DRIVER 字符串, 实际移除的驱动列表)。
    '''
    current = config_manager.environment.get('DRIVER', BASE_DRIVER)
    current_drivers = parse_driver(current)
    removed = [driver for driver in redundant_drivers if driver in current_drivers]
    if not removed:
        return current, []
    new_drivers = [driver for driver in current_drivers if driver not in removed]
    if BASE_DRIVER not in new_drivers:
        new_drivers.append(BASE_DRIVER)
    new_value = format_driver(new_drivers)
    config_manager.update_env({'DRIVER': new_value})
    return new_value, removed


def compute_redundant_drivers(uninstalling_module: str) -> list[str]:
    '''
    计算卸载某适配器后可以移除的驱动：
    即该适配器需要、但其他仍注册的适配器都不再需要的驱动。
    '''
    target_drivers = set(get_required_drivers(uninstalling_module))
    if not target_drivers:
        return []
    project_data = config_manager.read_pyproject()
    registered_modules = {
        adapter.get('module_name')
        for adapter in project_data.get('tool', {}).get('nonebot', {}).get('adapters', [])
        if isinstance(adapter, dict)
        and adapter.get('module_name')
        and adapter.get('module_name') != uninstalling_module
    }
    still_needed: set[str] = set()
    for module_name in registered_modules:
        if module_name:
            still_needed.update(get_required_drivers(module_name))
    return sorted(target_drivers - still_needed)
