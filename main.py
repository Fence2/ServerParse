import os
import re
from pathlib import Path

from modules.parser import tools


def main():
    print("Добро пожаловать в парсер комплектующих и серверов!")
    while True:
        print(
            "Введите номер конкурента и нажмите Enter\n\n"
            "\t1 - ServerMall.ru\n"
            "\t2 - ittelo.ru\n"
            "\t3 - WestComp.ru\n"
            "\t4 - ServerGate.ru\n"
            "\t5 - Nord-Server.ru\n"
            "\n"
        )
        choice = input().strip()
        # choice = "1"

        if re.fullmatch(r"\d+", choice):
            break
        else:
            print("Ошибка. Нужно ввести только номер:")

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
        case _:
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
        case _:
            return

    tools.launch_parser(
        parser=parser,
        folder_to_save=folder_to_save,
        categories=CATEGORIES,
        config_categories=CONFIG_CATEGORIES,
        nds=nds
    )

    print(f"Завершён парсинг {parser_name}. Проверьте консоль!")

    # try:
    #     from win10toast import ToastNotifier
    #     toast = ToastNotifier()
    #     toast.show_toast(
    #         "Окончание парсинг",
    #         f"Завершён парсинг {parser_name}. Проверьте консоль!",
    #         duration=8
    #     )
    # except Exception:
    #     pass


if __name__ == '__main__':
    main()
    print()
    os.system("pause")
