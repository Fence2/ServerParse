from .parser_dataclasses import *


def get_all_components_to_delete(server: Server) -> list:
    comp: Component
    cpu_ram = list()
    for comp in server.components:
        if comp.category not in ["Процессоры", "Оперативная память"]:
            continue

        if comp.price == 0:
            cpu_ram.append(comp)

    return cpu_ram


def post_process_all(servers: list[Server], cpu_ram: dict):
    comps_to_delete = set()
    for server in servers:
        for comp in get_all_components_to_delete(server):
            comps_to_delete.add(comp.name)

    print()

    'HPE 16Gb (2x8Gb) DDR3-12800 - Прямо такой нет. Есть 2 разных. Вычесть среднее?'
    'HPE 64Gb (4х16Gb) DDR3-14900 - Такой нет'
    'HPE 32Gb (2x16Gb)  DDR4 2133MHz (726722-B21) - Есть именно такая, но не везде'
    'HPE 64Gb (2x32Gb) DDR4 2666MHz (815100-B21) - Такой нет'

    '2 x Xeon E5-2620v2 6-core  (2.1GHz, 15Mb, 80W, LGA2011) - Нет'
    '2 x Xeon E5-2620v3   6-core (2.4GHz, Haswell-EP, 15 МБ, 85W) - Есть'
    '2 x Xeon E5-2430Lv2 6-core (2.4 GHz, Ivy Bridge EN, 15Mb, 60W) - Есть'
    '2x Intel Xeon Gold 6132 2.6GHz 14-Core (LGA3647, 19.25MB,140W) - Нет'
