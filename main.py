import os
import re
from pathlib import Path

from modules.parser import tools

PARSERS = {
    "1": "ServerMall.ru",
    "2": "ittelo.ru",
    "3": "WestComp.ru",
    "4": "ServerGate.ru",
    "5": "Nord-Server.ru",
    "6": "Sale-Server.ru",
    "7": "shop.nag.ru (Только комплектующие)",
}


def main():
    print("Добро пожаловать в парсер комплектующих и серверов!")
    while True:
        print("Введите номер конкурента и нажмите Enter")
        print("Если необходимо спарсить только каталог, добавьте знак тире возле номера парсера.")
        print('Примеры корректного выбора парсера: "6", "5-", "-2"\n')
        for n, name in PARSERS.items():
            print(f"\t{n} - {name}")
        print()

        choice = input().strip()
        only_catalog = False
        # choice = "7"  # TODO_ UNDO
        if "-" in choice:
            only_catalog = True
        choice = choice.replace("-", "")

        if re.fullmatch(r"\d+", choice) and choice in PARSERS:
            break
        else:
            print("Ошибка. Введен неподходящий номер парсера. Попробуйте еще раз\n")

    match choice:
        case "1":
            from servermall import Parser, catalog, configurator, data_prettify  # noqa
            from servermall.constants import CATEGORIES, CONFIG_CATEGORIES
            parser_name = "ServerMall"
        case "2":
            from ittelo import Parser, catalog, configurator, data_prettify  # noqa
            from ittelo.constants import CATEGORIES, CONFIG_CATEGORIES
            parser_name = "ittelo"
        case "3":
            from westcomp import Parser, catalog, configurator, data_prettify  # noqa
            from westcomp.constants import CATEGORIES, CONFIG_CATEGORIES
            parser_name = "WestComp"
        case "4":
            from servergate import Parser, catalog, configurator, data_prettify  # noqa
            from servergate.constants import CATEGORIES, CONFIG_CATEGORIES
            parser_name = "ServerGate"
        case "5":
            from nord_server import Parser, catalog, configurator, data_prettify  # noqa
            from nord_server.constants import CATEGORIES, CONFIG_CATEGORIES
            parser_name = "Nord_Server"
        case "6":
            from sale_server import Parser, catalog, configurator, data_prettify  # noqa
            from sale_server.constants import CATEGORIES, CONFIG_CATEGORIES
            parser_name = "Sale_Server"
        case "7":
            from shop_nag import Parser, catalog, configurator, data_prettify  # noqa
            from shop_nag.constants import CATEGORIES, CONFIG_CATEGORIES
            parser_name = "Shop_Nag"
        case _:
            print("Введен неправильный номер. Попробуйте заново.")
            return

    folder_to_save = Path.cwd() / f'Data/{parser_name}/{tools.get_today_day_and_month()}/'
    folder_to_save.mkdir(parents=True, exist_ok=True)
    webdriver_path = "./chromedriver.exe"
    nds = False

    match choice:
        case "1":
            parser = Parser(
                folder_to_save,
                webdriver_path,
                catalog_selenium=True,
                config_selenium=True
            )
        case "2":
            parser = Parser(folder_to_save)
        case "3":
            parser = Parser(
                folder_to_save,
                webdriver_path,
                config_selenium=True
            )
            nds = True
        case "4":
            parser = Parser(
                folder_to_save,
                webdriver_path,
                config_selenium=True
            )
        case "5":
            parser = Parser(folder_to_save)
        case "6":
            parser = Parser(folder_to_save)
        case "7":
            parser = Parser(
                folder_to_save,
                webdriver_path,
                catalog_selenium=True
            )
        case _:
            return

    tools.launch_parser(
        parser=parser,
        folder_to_save=folder_to_save,
        categories=CATEGORIES,
        config_categories=CONFIG_CATEGORIES,
        nds=nds,
        get_only_catalog=only_catalog
    )

    print(f"Завершён парсинг {parser_name}. Проверьте консоль!")


if __name__ == '__main__':
    main()
    print()
    os.system("pause")
