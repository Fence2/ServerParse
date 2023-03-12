import re
from pathlib import Path
from dataclasses import dataclass, field
from modules.parser.tools import Patterns, search_from_pattern, sub_not_digits, get_options, get_unique_name, get_attrs


@dataclass(slots=True, kw_only=True)
class CServer:
    @dataclass(slots=True, kw_only=True)
    class PSU:
        amount: str = ""
        power: str = ""

    @dataclass(slots=True, kw_only=True)
    class RAID:
        model: str = ""
        speed: str = ""

    @dataclass(slots=True, kw_only=True)
    class NETWORK:
        model: str = ""

    @dataclass(slots=True, kw_only=True)
    class IDRAC:
        model: str = ""

    brand: str = ""
    model: str = ""
    gen: str = ""
    trays_amount: str = ""
    trays_form_factor: str = ""

    psu: PSU = field(default_factory=PSU)
    raid: RAID = field(default_factory=RAID)
    network: NETWORK = field(default_factory=NETWORK)
    idrac: IDRAC = field(default_factory=IDRAC)


def get_servers_specs_keys(all_servers):
    for server in all_servers:
        if server.category > 3 or len(server.components) == 0:
            continue

        server.key = CServer(
            brand=server.brand,
            model=server.model,
            gen=str(sub_not_digits(server.generation)) if server.generation is not None else ''
        )
        if "SFF" in server.name.upper() or "2.5" in server.name:
            server.key.trays_form_factor = "SFF"
            server.name = server.name.replace("2.5", "SFF")
        elif "LFF" in server.name.upper() or "3.5" in server.name:
            server.key.trays_form_factor = "LFF"
            server.name = server.name.replace("3.5", "LFF")

        trays = search_from_pattern(Patterns.SERVER.trays, server.name)
        server.key.trays_amount = str(sub_not_digits(trays)) if trays is not None else ''

    return all_servers


def get_gs_server_item(gs_server):
    server_item = CServer(
        brand=gs_server.get('Manufacturer', ''),
        model=gs_server.get('Model', ''),
        gen=gs_server.get('Generation', ''),
        trays_amount=gs_server.get('[Slots] Quantity', ''),
        trays_form_factor=gs_server.get('[Slots] Form-factor', ''),
    )

    if server_item.brand.lower() == "supermicro":
        server_item.model = str(sub_not_digits(server_item.model))

    server_item.psu.amount = gs_server.get('[PSU] Quantity', '')
    server_item.psu.power = gs_server.get('[PSU] Power', '')
    server_item.raid.model = gs_server.get('[RAID] Model', '')
    server_item.raid.speed = gs_server.get('[RAID] Bandwidth (Gb/s)', '')
    server_item.network.model = gs_server.get('[Network] Model', '')
    server_item.idrac.model = gs_server.get('[IDRAC]', '')

    return server_item


def get_server_name(server_item: CServer, gs_servers_final: dict):
    server_name = list()
    if len(server_item.brand):
        server_name.append(f"{server_item.brand}")
    if len(server_item.model):
        server_name.append(f"{server_item.model}")
    if len(server_item.gen):
        server_name.append(f"G{server_item.gen}")
    if len(server_item.trays_amount):
        server_name.append(f"{server_item.trays_amount}{server_item.trays_form_factor}")

    server_name = " ".join([i for i in server_name if len(i.strip())])

    return get_unique_name(server_name, gs_servers_final)


def configure_psu(gs_server, psu, end_price):
    psu_excel_row = ['', "Блоки питания", '', '', '']
    PSU_OK = False
    chosen_comp = None
    try:
        if len(gs_server.psu.amount) and gs_server.psu.amount.isnumeric():
            psu_name = "Нет подходящего"
            psu_price = ""

            if not isinstance(gs_server.psu.amount, list):
                psu_amount = [gs_server.psu.amount]
            else:
                psu_amount = gs_server.psu.amount

            # psu_amount = [int(i) for i in psu_amount]

            if len(gs_server.psu.power):
                if not isinstance(gs_server.psu.power, list):
                    psu_power = [gs_server.psu.power]
                else:
                    psu_power = gs_server.psu.power

                # psu_power = [int(i) for i in psu_amount]
            else:
                psu_power = None

            for comp in psu:
                good_amount = "2" in psu_amount and "2" in comp.name[:4] or \
                              "1" in psu_amount and "2" not in comp.name[:4]
                good_power = True if psu_power is None else any(
                    [i in comp.name for i in psu_power])

                good_psu = good_amount and good_power
                if good_psu:
                    psu_price = comp.price
                    psu_name = comp.name
                    PSU_OK = True
                    chosen_comp = comp
                    break
            else:
                if "2" in psu_amount:
                    for comp in psu:
                        good_power = True if psu_power is None else any(
                            [i in comp.name for i in psu_power])

                        if good_power:
                            if "2" not in comp.name[:4]:
                                psu_price = comp.price * 2
                                psu_name = "2x " + comp.name
                            else:
                                psu_price = comp.price
                                psu_name = comp.name
                            PSU_OK = True
                            chosen_comp = comp
                            break

            if PSU_OK:
                end_price += psu_price
                # print(f"    Добавлена стоимость: {psu_name} = {psu_price}")
            else:
                psu_excel_row[0] = 'BAD'
                amount_str = (str(gs_server.psu.amount) + "x ") if len(gs_server.psu.amount) else ''
                power_str = (str(gs_server.psu.power) + "W") if len(gs_server.psu.power) else ''
                psu_excel_row[4] = f'Должно быть: {amount_str}{power_str}'

                if len(psu):
                    psu_name = psu[0].name
                    chosen_comp = psu[0]
                    psu_price = psu[0].price
                    end_price += psu_price
                # print(f"    [BAD] Добавлена стоимость: {psu_name} = {psu_price}")

            if chosen_comp is not None:
                chosen_comp.checked = False
            psu_excel_row[2] = psu_name
            psu_excel_row[3] = psu_price
        else:
            PSU_OK = True
            psu_excel_row = []
    except Exception as e:
        print(f"Ошибка в обработке PSU\n{e} - ")
        PSU_OK = False
        psu_excel_row[0] = 'ERROR'
    finally:
        return psu_excel_row, PSU_OK, end_price


def configure_raid(gs_server, raid, end_price):
    raid_excel_row = ['', "Raid-контроллер", '', '', '']
    RAID_OK = False
    chosen_comp = None
    try:
        if len(gs_server.raid.model):
            raid_name = "Нет подходящего"
            raid_price = ""

            if not isinstance(gs_server.raid.model, list):
                raid_model = [gs_server.raid.model]
            else:
                raid_model = gs_server.raid.model

            if len(gs_server.raid.speed):
                if not isinstance(gs_server.raid.speed, list):
                    raid_speed = [gs_server.raid.speed]
                else:
                    raid_speed = gs_server.raid.speed
            else:
                raid_speed = None

            for comp in raid:
                good_model = any([i.lower() in comp.name.lower() for i in raid_model])

                comp_speed_gb = re.findall(r"\d+ ?GB", comp.name, flags=re.I)
                comp_speed_mb = re.findall(r"\d+ ?MB", comp.name, flags=re.I)
                if len(comp_speed_gb):
                    comp_speed = str(sub_not_digits(comp_speed_gb[0]))
                elif len(comp_speed_mb):
                    comp_speed = str(sub_not_digits(comp_speed_mb[0]))[0]
                else:
                    comp_speed = None

                good_speed = True if raid_speed is None else comp_speed is None or comp_speed in raid_speed

                good_raid = good_model and good_speed
                if good_raid:
                    raid_price = comp.price
                    raid_name = comp.name
                    RAID_OK = True
                    chosen_comp = comp
                    break

            if RAID_OK:
                end_price += raid_price
                # print(f"    Добавлена стоимость: {raid_name} = {raid_price}")
            else:
                if "Cheapest" not in raid:
                    raid_excel_row[0] = 'BAD'
                    model_str = (str(gs_server.raid.model) + " ") if len(gs_server.raid.model) else ''
                    speed_str = (str(gs_server.raid.speed) + "Gb/s") if len(gs_server.raid.speed) else ''
                    raid_excel_row[4] = f'Должно быть: {model_str}{speed_str}'
                    # print(f"    [BAD] Добавлена стоимость: {raid_name} = {raid_price}")
                else:
                    RAID_OK = True
                    # print(f"    Добавлена стоимость: {raid_name} = {raid_price}")
                if len(raid):
                    raid_name = raid[0].name
                    raid_price = raid[0].price
                    chosen_comp = raid[0]
                    end_price += raid_price

            if chosen_comp is not None:
                chosen_comp.checked = False
            raid_excel_row[2] = raid_name
            raid_excel_row[3] = raid_price
        else:
            RAID_OK = True
            raid_excel_row = []
    except Exception as e:
        print(f"Ошибка в обработке RAID\n{e} - ")
        RAID_OK = False
        raid_excel_row[0] = 'ERROR'
    finally:
        return raid_excel_row, RAID_OK, end_price


def configure_network(gs_server, network, end_price):
    network_excel_row = ['', "Сетевая карта", '', '', '']
    NETWORK_OK = False
    chosen_comp = None

    try:
        if len(gs_server.network.model):
            network_name = "Нет подходящего"
            network_price = ""

            if not isinstance(gs_server.network.model, list):
                network_model = [gs_server.network.model]
            else:
                network_model = gs_server.network.model

            for comp in network:
                good_model = any([i.lower() in comp.name.lower() for i in network_model])

                good_network = good_model
                if good_network:
                    network_price = comp.price
                    network_name = comp.name
                    NETWORK_OK = True
                    chosen_comp = comp
                    break

            if NETWORK_OK:
                end_price += network_price
                # print(f"    Добавлена стоимость: {network_name} = {network_price}")
            else:
                if "Cheapest" not in network_model:
                    network_excel_row[0] = 'BAD'
                    model_str = (str(gs_server.network.model) + " ") if len(gs_server.network.model) else ''
                    network_excel_row[4] = f'Должно быть: {model_str}'
                    # print(f"    [BAD] Добавлена стоимость: {network_name} = {network_price}")
                else:
                    NETWORK_OK = True
                    # print(f"    Добавлена стоимость: {network_name} = {network_price}")
                if len(network):
                    network_name = network[0].name
                    network_price = network[0].price
                    chosen_comp = network[0]
                    end_price += network_price

            if chosen_comp is not None:
                chosen_comp.checked = False
            network_excel_row[2] = network_name
            network_excel_row[3] = network_price
        else:
            NETWORK_OK = True
            network_excel_row = []
    except Exception as e:
        print(f"Ошибка в обработке NETWORK\n{e} - ")
        NETWORK_OK = False
        network_excel_row[0] = 'ERROR'
    finally:
        return network_excel_row, NETWORK_OK, end_price


def configure_idrac(gs_server, idrac, end_price):
    idrac_excel_row = ['', "Удалённое управление", '', '', '']
    IDRAC_OK = False
    chosen_comp = None
    try:
        if len(gs_server.idrac.model):
            idrac_name = "Нет подходящего"
            idrac_price = ""

            if not isinstance(gs_server.idrac.model, list):
                idrac_model = [gs_server.idrac.model]
            else:
                idrac_model = gs_server.idrac.model

            for comp in idrac:
                good_model = any([i.lower() in comp.name.lower() for i in idrac_model])

                good_idrac = good_model
                if good_idrac:
                    idrac_price = comp.price
                    idrac_name = comp.name
                    IDRAC_OK = True
                    chosen_comp = comp
                    break

            if IDRAC_OK:
                end_price += idrac_price
                # print(f"    Добавлена стоимость: {idrac_name} = {idrac_price}")
            else:
                if "Cheapest" not in idrac:
                    idrac_excel_row[0] = 'BAD'
                    model_str = (str(gs_server.idrac.model) + " ") if len(gs_server.idrac.model) else ''
                    idrac_excel_row[4] = f'Должно быть: {model_str}'
                    # print(f"    [BAD] Добавлена стоимость: {idrac_name} = {idrac_price}")
                else:
                    IDRAC_OK = True
                    # print(f"    Добавлена стоимость: {idrac_name} = {idrac_price}")
                if len(idrac):
                    idrac_name = idrac[0].name
                    idrac_price = idrac[0].price
                    chosen_comp = idrac[0]
                    end_price += idrac_price

            if chosen_comp is not None:
                chosen_comp.checked = False
            idrac_excel_row[2] = idrac_name
            idrac_excel_row[3] = idrac_price
        else:
            IDRAC_OK = True
            idrac_excel_row = []
    except Exception as e:
        print(f"Ошибка в обработке IDRAC\n{e} - ")
        IDRAC_OK = False
        idrac_excel_row[0] = 'ERROR'
    finally:
        return idrac_excel_row, IDRAC_OK, end_price


def servers_process(all_servers):
    server_options = get_options(Path.cwd() / "Options.xlsx",
                                 sheet_name="SERVER")

    if server_options is None:
        return {}, {}, {}, {}

    if not len(all_servers):
        gs_servers_final = dict()
        for gs_option in server_options:
            gs_server = get_gs_server_item(gs_option)
            server_name = get_server_name(gs_server, gs_servers_final)
            gs_servers_final[server_name] = 0

        return gs_servers_final, {}, {}, {}

    all_servers = get_servers_specs_keys(all_servers)

    gs_servers_final, good, partial, bad = configure_servers(all_servers, server_options)

    return gs_servers_final, good, partial, bad


def configure_servers(all_servers, server_options):
    gs_servers_final = dict()
    good_servers_excel = dict()
    partial_servers_excel = dict()
    bad_servers_excel = dict()

    for gs_option in server_options:
        gs_server = get_gs_server_item(gs_option)
        if len(gs_server.brand) == 0 or len(gs_server.brand) == 0:
            continue

        server_name = get_server_name(gs_server, gs_servers_final)

        parser_server = None
        for server in all_servers:
            good = list()
            for attr in get_attrs(CServer)[:5]:
                server_value = getattr(server.key, attr)
                if server_value is None:
                    good.append(False)
                    continue
                if len(getattr(gs_server, attr)):
                    if attr == "model" and gs_server.brand.lower() == "supermicro":
                        if isinstance(getattr(gs_server, attr), str):
                            good.append(sub_not_digits(server_value.upper()) ==
                                        sub_not_digits(getattr(gs_server, attr).upper()))
                        else:
                            good.append(
                                server_value in [str(sub_not_digits(i)) for i in getattr(gs_server, attr)])
                    else:
                        if isinstance(getattr(gs_server, attr), str):
                            good.append(server_value.upper() == getattr(gs_server, attr).upper())
                        else:
                            good.append(server_value in getattr(gs_server, attr))

            good = all(good)
            if good:
                parser_server = server
                break

        if parser_server is None:
            gs_servers_final[server_name] = 0
        else:
            server = parser_server
            end_price = server.config_price

            not_excluded_comps = [comp for comp in server.components if comp.checked]

            psu = [comp for comp in server.components if "блок" in comp.category.lower()]
            if len(psu):
                psu.sort(key=lambda x: x.price)

            raid = [comp for comp in server.components if "raid" in comp.category.lower()]
            if len(raid):
                raid.sort(key=lambda x: x.price)

            network = [comp for comp in server.components if "сетев" in comp.category.lower()]
            if len(network):
                network.sort(key=lambda x: x.price)

            idrac = [comp for comp in server.components if
                     re.search(r"удал[её]нн", comp.category, flags=re.I) is not None]
            if len(idrac):
                idrac.sort(key=lambda x: x.price)

            for comp in psu + raid + network + idrac:
                if comp in not_excluded_comps:
                    not_excluded_comps.remove(comp)

            print("Сервер к обработке:", server.name, end=" - ")
            # print(f"    psu={len(psu)}")
            # print(f"    raid={len(raid)}")
            # print(f"    network={len(network)}")
            # print(f"    idrac={len(idrac)}")
            # print()

            psu_excel_row, PSU_OK, end_price = configure_psu(gs_server, psu, end_price)

            raid_excel_row, RAID_OK, end_price = configure_raid(gs_server, raid, end_price)

            network_excel_row, NETWORK_OK, end_price = configure_network(gs_server, network, end_price)

            idrac_excel_row, IDRAC_OK, end_price = configure_idrac(gs_server, idrac, end_price)

            excel_server = [
                [(server.name, server.config_url), "", "ИТОГОВАЯ СТОИМОСТЬ", end_price],
                ['', 'Платформа', 'Цена без всего', server.config_price],
            ]

            not_excluded_comps_rows = list()
            _bad_categories_pattern = re.compile(
                r"процессор|"
                r"оперативная\s+памят|"
                r"плашк\w?\s+памят\w?|"
                r"рельс\w?|"
                r"видеокарт|"
                r"ж[её]стк\w+\s+диск\w?\b",
                flags=re.I
            )
            for comp in not_excluded_comps:
                lower_category = comp.category.lower()
                if _bad_categories_pattern.search(lower_category):
                    not_excluded_comps_rows.append(
                        ['BAD', comp.category, f"{comp.checked_amount}x {comp.name}", comp.price,
                         "Стоимость этого комплектующего вероятно нужно найти и вычесть!"]
                    )

            if len(psu_excel_row):
                excel_server.append(psu_excel_row)
            if len(raid_excel_row):
                excel_server.append(raid_excel_row)
            if len(network_excel_row):
                excel_server.append(network_excel_row)
            if len(idrac_excel_row):
                excel_server.append(idrac_excel_row)
            if len(not_excluded_comps_rows):
                excel_server.extend(not_excluded_comps_rows)
                BAD_COMPS = True
            else:
                BAD_COMPS = False
            excel_server.append([''])

            if PSU_OK + RAID_OK + NETWORK_OK + IDRAC_OK - BAD_COMPS == 4:
                print("+++Хороший сервер!+++")
                good_servers_excel[server_name] = excel_server
                gs_servers_final[server_name] = end_price
            elif PSU_OK + RAID_OK + NETWORK_OK + IDRAC_OK - BAD_COMPS > 0:
                print("-+-Частично хороший сервер-+-")
                partial_servers_excel[server_name] = excel_server
                gs_servers_final[server_name] = 0
            else:
                print("---Плохой сервер---")
                bad_servers_excel[server_name] = excel_server
                gs_servers_final[server_name] = 0

    return gs_servers_final, good_servers_excel, partial_servers_excel, bad_servers_excel
