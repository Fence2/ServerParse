import re
import time
import copy
import requests
import pandas as pd
from dataclasses import fields


class Patterns:
    NEW = re.compile(r"Нов[а-яё]{0,2}|New", flags=re.I)
    REF = re.compile(r"Used|Ref(?:urbish?)?(?:ed)?|(?:(?:\()?(?:\(\s)?\bб\s?\\?\/?\s?у\b(?:\s\))?(?:\))?)",  # noqa
                     flags=re.I)
    NUMERIC = re.compile(r"\d+(\.\d+)?")
    INT = re.compile(r"\d+")

    MULTIPLE = re.compile(r"^(\s*[x×х]+\s*)(\d{1,2})\D|^\d{1,2}(\s*([x×х]+|(шт|pc)\.?)\s*)", flags=re.I)
    FORM_FACTOR = re.compile(r"[SL]FF\b", flags=re.I)

    class CPU:
        brand = re.compile(r"INTEL|AMD", flags=re.I)
        genX = re.compile(r"X\d{4}", flags=re.I)
        metal = re.compile(r"Bronze|Silver|Gold|Platinum", flags=re.I)
        genE = re.compile(r"\bE\d\D", flags=re.I)
        model = re.compile(r"\d{4}[a-uw-z]*", flags=re.I)
        version = re.compile(r"v\d\b", flags=re.I)

    class RAM:
        ddr = re.compile(r"DDR\d", flags=re.I)
        capacity = re.compile(r"\d+ *GB", flags=re.I)
        freqHZ = re.compile(r"\d+ *\wHZ", flags=re.I)
        freqPC = re.compile(r"PC\dL?[- ]\d{4,5}", flags=re.I)
        dimm = re.compile(r"\w{1,2}DIMM", flags=re.I)  # noqa
        ecc = re.compile(r"[ЕE][СC]{2}", flags=re.I)
        not_ecc = re.compile(r"NO[NT]\s*[ЕE][СC]{2}", flags=re.I)

    class TRAY:
        small_form_fact = re.compile(r"2.5|SFF", flags=re.I)
        large_form_fact = re.compile(r"3.5|LFF", flags=re.I)
        is_adapter = re.compile(r"Переходник|Адаптер|Adapter", flags=re.I)

    class RAID:
        model = re.compile(r"ASR.+?\s|LSI..+?\s", flags=re.I)

    class SERVER:
        brand = re.compile(r"Supermicro|HP|DELL", flags=re.I)
        model = re.compile(r"(?:DL|R)\d{3}\w*", flags=re.I)
        supermicro_model = re.compile(r"\d{4}\S*", flags=re.I)  # noqa
        gen = re.compile(r"G\d{1,2}\b", flags=re.I)
        units = re.compile(r"\b\dU", flags=re.I)
        trays = re.compile(r"\d{1,2}[ -]*[SL]FF", flags=re.I)

    class FULLSERVER:  # noqa
        HP = re.compile(r"(HP)|(DL\d{3}[pр ])|(G\d)|(\d{1,2}[ -]*[SL]FF)", flags=re.I)
        DELL = re.compile(r"(DELL)|(R\d{3}\w*)|(\d{1,2}[ -]*[SL]FF)", flags=re.I)
        SUPERMICRO = re.compile(r"(Supermicro)|(\d{4})", flags=re.I)  # noqa

    class MIXED:
        rus_ENG = re.compile(r"[а-яё][a-z]", flags=re.I)
        eng_RUS = re.compile(r"[a-z][а-яё]", flags=re.I)

    class CATEGORY:
        cpu = re.compile(r"(?!.*вентилят)(.*\bcpu\b|.*\bпроцессор)(?!.*вентилят)", flags=re.I)
        ram = re.compile(
            r"(?!.*контрол+[а-яё]+|.*к[эе]ш|.*батар)(.*оперативн[а-яё]+\s+памят[а-яё]+|.*\bram\b)(?!.*контрол+[а-яё]+|.*к[эе]ш|.*батар)",
            flags=re.I)
        hdd = re.compile(r"\bкорзин[\wа-яё] на|hdd", flags=re.I)
        trays = re.compile(r"\bсалазк[\wа-яё]", flags=re.I)
        raid = re.compile(r"(?!.*к[эе]ш|.*батар)(.*\braid\b|.*\bр[еэ][ий]д\b)(?!.*к[эе]ш|.*батар)", flags=re.I)
        network = re.compile(r"сетев[\wа-яё]+ карт[\wа-яё]|network", flags=re.I)
        rails = re.compile(r"монтаж и подключение|\bрельс|креплен[а-яё]+ для сервер[а-яё]* в стойк[а-яё]+", flags=re.I)
        idrac = re.compile(r"удал[её]нн[\wа-яё]+\s+(\bуправлен[\wа-яё]+|\bадминистриров[а-яё]+)", flags=re.I)
        psu = re.compile(r"\bpsu\b|\bблок[а-яё]*\sпитан[а-яё]*", flags=re.I)

        all_ru = {
            cpu: "Процессоры",
            ram: "Оперативная память",
            hdd: "Жёсткие диски",
            trays: "Салазки",
            raid: "RAID-контроллер",
            network: "Сетевая карта",
            rails: "Рельсы",
            idrac: "Удалённое управление",
            psu: "Блок питания"
        }


def search_from_pattern(pattern: re.Pattern, search_str: str) -> str | None:
    """
    Возвращает None, если паттерн не найден. Иначе возвращает найденную строку
    """
    result = pattern.search(search_str)
    if result is None:
        return None

    return result.group().upper()


def normalize_category_name(category_name: str) -> str:
    i = 1
    for pattern, correct_str in Patterns.CATEGORY.all_ru.items():
        if i not in (1, 2, 5):
            if pattern.search(category_name) is not None:
                return correct_str
        else:
            if pattern.match(category_name) is not None:
                return correct_str

        i += 1

    return category_name


def sub_not_digits(word: str):
    digits = re.sub(r"\D+", "", word)
    if len(digits):
        digits = int(digits)
    return digits


def search_for_mixed_cyrillic_and_latin(comp_name):
    all_rus_eng = Patterns.MIXED.rus_ENG.findall(comp_name)
    all_eng_rus = Patterns.MIXED.eng_RUS.findall(comp_name)
    if len(all_rus_eng) + len(all_eng_rus) > 0:
        print()
        print("\n".join(["НАЙДЕНЫ КРИВЫЕ НАЗВАНИЯ СО СМЕШАННОЙ КИРИЛЛИЦЕЙ И ЛАТИНИЦЕЙ"] * 3))
        print(comp_name)
        if len(all_rus_eng) > 0:
            print(f"\tRU_EN - {all_rus_eng}, index = {[comp_name.index(p) for p in all_rus_eng]}")

        if len(all_eng_rus) > 0:
            print(f"\tEN_RU - {all_eng_rus}, index = {[comp_name.index(p) for p in all_eng_rus]}")

        print()


def add_info_to_trays_and_rails(category: str, comp, server):
    comp_is_adapter = search_from_pattern(Patterns.TRAY.is_adapter, comp.name)

    comp_brand = search_from_pattern(Patterns.SERVER.brand, comp.name)
    comp_model = search_from_pattern(Patterns.SERVER.model, comp.name)
    comp_gen = search_from_pattern(Patterns.SERVER.gen, comp.name)
    comp_units = search_from_pattern(Patterns.SERVER.units, comp.name)
    comp_trays = search_from_pattern(Patterns.FORM_FACTOR, comp.name)

    server_trays = search_from_pattern(Patterns.FORM_FACTOR, server.name)

    brand_ok = server.brand is not None and comp_brand is None
    model_ok = server.model is not None and comp_model is None
    gen_ok = server.generation is not None and comp_gen is None
    units_ok = server.units is not None and comp_units is None
    form_factor_ok = server_trays is not None and comp_trays is None

    if "рельсы" in category.lower():
        if brand_ok and server.brand not in comp.name.upper():
            comp.name += f" {server.brand}"
        if model_ok and server.brand.lower() != "supermicro" and server.model not in comp.name.upper():  # noqa
            comp.name += f" {server.model}"
        if gen_ok and server.generation not in comp.name.upper():
            comp.name += f" {server.generation}"
        if units_ok:
            comp.name += f" {server.units}"
        if form_factor_ok:
            comp.name += f" {server_trays}"

    if "салазки" in category.lower() and comp_is_adapter is None:
        if brand_ok and server.brand not in comp.name.upper():
            comp.name += f" {server.brand}"

        if server.brand == "DELL" or comp_brand == "DELL":
            if model_ok and server.model not in comp.name.upper():
                comp.name += f" {server.model}"

        if server.brand == "HP" or comp_brand == "HP":
            if gen_ok and server.generation not in comp.name.upper():
                comp.name += f" {server.generation}"

    return comp.name


def get_today_full_date_str() -> str:
    from datetime import datetime

    current_time = datetime.now()
    now_time_str = current_time.strftime("%d-%m-%Y %H.%M.%S")
    return now_time_str


def get_today_day_and_month():
    from datetime import datetime

    current_time = datetime.now()
    now_time_str = current_time.strftime("%d.%m")
    return now_time_str


def format_excel_columns_width(active_ws):
    dims = {}
    for row in active_ws.rows:
        for cell in row:
            if cell.value:
                dims[cell.column_letter] = max((dims.get(cell.column_letter, 0), len(str(cell.value))))
    for col, value in dims.items():
        active_ws.column_dimensions[col].width = value + 4

    return active_ws


def format_price(str_price: str) -> int:
    """
    Функция обрабатывает поступающую строку, удаляя все нечисловые символы, и возвращает целое число.

    Если в строке не найдены числовые символы, функция возвращает 0.
    """

    if re.search(r"\d+", str_price) is not None:
        str_price = re.sub(r"[^\d.,]", "", str_price)
        str_price = re.sub(r"[.,]\d*", "", str_price)
        return int(str_price)
    else:
        return 0


def format_name(name: str) -> str:
    name = re.sub(r"(Gen\s*)(?P<gen>\d)", r"G\g<gen>", name, flags=re.I).strip()
    name = re.sub(r"(?P<num>\d{1,2})([xх]?)(?P<slff>\wFF)", r"\g<num>\g<slff>", name, flags=re.I).strip()
    name = re.sub(r"Registered", "REG", name, flags=re.I)
    name = re.sub(r" {2}", " ", name).strip()
    search_for_mixed_cyrillic_and_latin(name)
    return name


def new_or_ref(condition):
    return bool(search_from_pattern(Patterns.NEW, condition))


def get_server_category(server) -> int:
    """
    Функция возвращает категорию сервера, где:

    1 - Нужные нам HP
    2 - Нужные нам Dell
    3 - Нужные нам Supermicro

    4 - Неподходящие HP
    5 - Неподходящие Dell
    6 - Неподходящие Supermicro

    7 - Все остальные серверы
    """

    match server.brand:
        case 'HP':
            good_model = server.model is not None and re.search(r"DL3\d\d\D?", server.model, flags=re.I) is not None
            result = 1 if good_model else 4
        case 'DELL':
            good_model = server.model is not None and re.search(r"R[567]\d\d\w*", server.model, flags=re.I)
            result = 2 if good_model else 5
        case 'SUPERMICRO':  # noqa
            result = 3 if re.search(r"\d{4}", server.name, flags=re.I) is not None else 6
        case _:
            result = 7

    return result


def sort_products_by_category_and_name(products):
    products.sort(key=lambda item: (item.category, item.name))




def print_dict(item: dict, offset=''):
    """
    Функция красивого вывода содержимого словаря с подсчётом уникальных значений
    """
    if not offset:
        print(f"Всего элементов словаря:", len(item))
        print(f"Уникальных значений:", len(set(item.values())))

    for k, v in dict(sorted(item.items(), key=lambda x: x[1], reverse=True)).items():
        print(f"{offset}{k}: {v}")

    print()


def products_group_by_category(products: list) -> dict:
    result = dict()
    for p in products:
        result[p.category] = result.get(p.category, 0) + 1
    return result


def requests_try_to_get_max_5x(url: str, headers: dict = None, session=None):
    tries = 0
    while tries < 5:
        if tries:
            print("Попытка №", tries + 1)
        response = None
        try:
            if session is None:
                response = requests.get(url, headers=headers) if headers is not None else requests.get(url)
            else:
                response = session.get(url, headers=headers) if headers is not None else session.get(url)
        except requests.exceptions.ConnectTimeout:
            print("Не удалось загрузить страницу -", url)
        if response is not None and response.ok:
            if session is None:
                return response
            else:
                return response, session
        else:
            time.sleep(2)
            tries += 1

    if session is None:
        return None
    else:
        return None, session


def selenium_try_to_get_max_5x(driver, url, lambda_condition=True):
    import selenium.common.exceptions  # noqa
    from selenium.webdriver.support.wait import WebDriverWait  # noqa
    from bs4 import BeautifulSoup

    def is_page_loaded(html):
        soup = BeautifulSoup(html.page_source, "lxml")
        check_results = soup.find_all(lambda_condition, limit=3)
        return len(check_results)

    tries = 0
    while tries < 5:
        try:
            if tries:
                print(f"Попытка №{tries + 1}")
            driver.get(url)
            time.sleep(0.3)
            try:
                WebDriverWait(driver, 15).until(is_page_loaded)
            except selenium.common.exceptions.TimeoutException:
                pass
            time.sleep(0.2)
            return driver
        except selenium.common.exceptions.TimeoutException:
            tries += 1
            print(f"Не удалось загрузить страницу {url}\nПробуем ещё раз.")
    return None


def get_sheets(path):
    try:
        xlsx = pd.ExcelFile(path)

        return xlsx.sheet_names
    except Exception as e:
        print("Не удалось получить список листов из файла Options.xlsx")
        print(e)
        return None


def get_options(path, sheet_name):
    try:
        _options = pd.read_excel(path, sheet_name=sheet_name)
        _options = _options.to_dict(orient="records")
        for i, row in enumerate(_options):
            for k, v in row.items():
                v = str(v).strip()
                if v == "nan":
                    v = ''
                if re.fullmatch(r"\d+\.0", v):
                    v = v.replace(".0", "")
                if ',' in v:
                    v = [i.strip() for i in v.split(",")]
                elif '.' in v:
                    v = [i.strip() for i in v.split(".")]
                elif Patterns.NUMERIC.fullmatch(v) is not None:
                    float_num = search_from_pattern(Patterns.NUMERIC, v)
                    float_num = round(float(float_num), 3)
                    int_num = int(search_from_pattern(Patterns.INT, v))
                    if float_num == float(int_num):
                        v = int_num
                    else:
                        v = float_num
                    v = str(v)

                _options[i][k] = v

        return _options
    except Exception as e:
        print("Не найден файл Options.xlsx с листом", sheet_name)
        print(e)
        return None


def get_unique_name(name, list_of_names):
    if name in list_of_names:
        k = 1
        while k < 100:
            if f"{name} ({k})" not in list_of_names:
                name = f"{name} ({k})"
                break
            k += 1

    return name


def get_attrs(class_item):
    return tuple(f.name for f in fields(class_item))


def prettify_ram(comp, nord_server=False):
    ddr = search_from_pattern(Patterns.RAM.ddr, comp.name)
    if ddr is None:
        freqPC = search_from_pattern(Patterns.RAM.freqPC, comp.name)
        if freqPC is not None:
            ddr = str(sub_not_digits(freqPC[:3]))
            comp.name += f" DDR{ddr}"
        elif nord_server:  # ТОЛЬКО ДЛЯ NORD-SERVER
            ddr = "3"
            comp.name += f" DDR{ddr}"
        else:
            ddr = "?"
    else:
        ddr = str(sub_not_digits(ddr))

    freqHZ = search_from_pattern(Patterns.RAM.freqHZ, comp.name)
    freqPC = search_from_pattern(Patterns.RAM.freqPC, comp.name)
    if freqHZ is None and freqPC is None:
        freq_no_pc = search_from_pattern(re.compile(r"\D([1-5]\d{4}|[6-9]\d{3})\D"), comp.name)
        if freq_no_pc is not None:
            freq_no_pc = str(sub_not_digits(freq_no_pc))

            comp.name = comp.name.replace(freq_no_pc, f"PC{ddr}-{freq_no_pc}")
        else:
            freq_4_digits = search_from_pattern(re.compile(r"[1-3]\d{3}\D"), comp.name)
            if freq_4_digits is not None:
                freq_4_digits = str(sub_not_digits(freq_4_digits))
                comp.name = comp.name.replace(freq_4_digits, f"{freq_4_digits}MHZ")


def standard_prettify_components(_components, nord_server=False):
    components = copy.deepcopy(_components)
    for comp in components:
        multiple = search_from_pattern(Patterns.MULTIPLE, comp.name)
        if multiple:
            multiple_amount = sub_not_digits(multiple)
            if multiple_amount:
                comp.name = Patterns.MULTIPLE.sub(f"{multiple_amount}x ", comp.name)
        if comp.category.lower() == "оперативная память":
            prettify_ram(comp, nord_server=nord_server)
        elif "процессор" in comp.category.lower():
            if re.search(r"xeon|gold|silver|bronze|platinum", comp.name, flags=re.I) and \
                    "intel" not in comp.name.lower():
                comp.name = f"Intel {comp.name}"

    return components


def standard_prettify_components_cfg(_components: list, nord_server=False):
    pretty_components = dict()
    components = copy.deepcopy(_components)
    for comp in components:
        multiple = search_from_pattern(Patterns.MULTIPLE, comp.name)
        if multiple:
            multiple_amount = sub_not_digits(multiple)
            if multiple_amount:
                comp.price //= multiple_amount
                comp.name = Patterns.MULTIPLE.sub("", comp.name)
        if comp.category.lower() == "оперативная память":
            prettify_ram(comp, nord_server=nord_server)
        elif "процессор" in comp.category.lower():
            if re.search(r"xeon|gold|silver|bronze|platinum", comp.name, flags=re.I) and \
                    "intel" not in comp.name.lower():
                comp.name = f"Intel {comp.name}"

        unique_name = f"{comp.name}|{int(comp.new)}|{comp.price}|{comp.no_sale_price}"
        if unique_name in pretty_components:
            pretty_components[unique_name].resource.append(comp.resource)
            continue

        comp.resource = [comp.resource]

        pretty_components[unique_name] = comp

    pretty_components = list(pretty_components.values())
    pretty_components.sort(key=lambda x: (x.category, x.name, x.price))

    return pretty_components


def standard_prettify_server(server):
    server.name = re.sub(
        r"(?P<amount>\d{1,2})\D?(?P<form_factor>[SL]FF)",
        r"\g<amount>\g<form_factor>",
        server.name,
        flags=re.I
    )

    if server.config_price == 0:
        server.config_price = server.card_price

    for comp in server.components:
        if comp.checked and comp.price != 0:
            server.config_price -= comp.price * comp.checked_amount
            comp.checked = False

    return server


def _get_items_by_category(components, categories_dict, nds):
    from modules.galtsystems_data_processor.universal_dataclass import ExcelItem
    result = {k: list() for k in categories_dict.values()}
    result["other_comp"] = list()

    for comp in components:
        if not comp.price > 0 or 'количество процессоров' in comp.category.lower():
            continue

        if nds:
            comp.price = int(comp.price * 1.1)
            comp.no_sale_price = int(comp.no_sale_price * 1.1)

        excel_item = ExcelItem(
            name=comp.name,
            price=comp.price,
            new=comp.new,
            no_sale_price=comp.no_sale_price,
            category=comp.category
        )

        if comp.category in categories_dict.keys():
            key_category = categories_dict[comp.category]
        else:
            key_category = "other_comp"

        result[key_category].append(excel_item)

    return result


def _get_servers_by_category(servers, nds):
    if nds:
        for server in servers:
            server.card_price = int(server.card_price * 1.1)
            server.config_price = int(server.config_price * 1.1)
            for comp in server.components:
                comp.price = int(comp.price * 1.1)
                comp.no_sale_price = int(comp.no_sale_price * 1.1)

    result = {
        'servers': [server for server in servers if server.category < 4 and server.config_price > 0],
        'other_servers': [server for server in servers if server.category > 3 and server.config_price > 0]
    }

    return result


def _get_components_by_catalog(parser, components=True, servers_list=False, servers_configs=False):
    return parser.start(
        get_new_components=components,
        get_new_servers_list=servers_list,
        get_new_servers_configs=servers_configs)


def _get_servers(parser, components=False, servers_list=True, servers_configs=True):
    return parser.start(
        get_new_components=components,
        get_new_servers_list=servers_list,
        get_new_servers_configs=servers_configs)


def launch_parser(
        parser,
        folder_to_save,
        categories,
        config_categories,
        nds=False
):
    from modules.galtsystems_data_processor import components_process, servers_process
    components = _get_components_by_catalog(
        parser,
        # 0, 0, 0
    )['components']

    parser_data = _get_servers(
        parser,
        # 0, 0, 0
    )
    servers, config_components = parser_data['servers'], parser_data['config_components']
    print("Обработка полученных данных...")
    components_to_process = _get_items_by_category(components, categories, nds)
    config_components_to_process = _get_items_by_category(config_components, config_categories, nds)
    servers_to_process = _get_servers_by_category(servers, nds)
    components_process.process_components(
        **components_to_process,
        folder_to_save=folder_to_save,
        filename="Components"
    )

    components_process.process_components(
        **config_components_to_process,
        folder_to_save=folder_to_save,
        filename="Components_from_configurators"
    )
    servers_process.process_servers(
        **servers_to_process,
        folder_to_save=folder_to_save,
        filename="Servers"
    )

# def log(log_str, log_type="DEBUG"):
#     from ..
#     today = get_today_day_and_month()
#     if os.path.exists()
