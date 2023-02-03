# -*- coding: utf-8 -*-

import json
import pickle
from pathlib import Path

import nord_server.catalog
import nord_server.configurator
import nord_server.data_prettify
from modules.parser_tools import *


class Parser:
    def __init__(self, work_folder, webdriver_path_if_needed=None):
        self.work_folder = work_folder
        self.components_file_bin = work_folder / "components.bin"
        self.components_file_json = work_folder / "components.json"
        self.servers_list_file_bin = work_folder / "servers_list.bin"
        self.servers_with_conf_list_bin = work_folder / "servers_confs.bin"
        self.configs_components_bin = work_folder / "configs_components.bin"

        self.webdriver_path = webdriver_path_if_needed

    def start(
            self,
            get_new_components=True,
            get_new_servers_list=True,
            get_new_servers_configs=True,

    ):
        components = list()
        servers = list()
        servers_with_configs = list()
        config_components = list()
        catalog = configurator = None

        if get_new_components:
            # Комплектующие: Получение
            print("Комплектующие: Получение")

            catalog = nord_server.catalog.Catalog()

            components = catalog.get_components()

            # Комплектующие: Сохранение
            print("Комплектующие: Сохранение..", end="")
            components_json = [comp.to_dict() for comp in components]

            with open(self.components_file_json, "w", encoding="utf-8") as file:
                json.dump(components_json, file, ensure_ascii=False)

            with open(self.components_file_bin, "wb") as file:
                pickle.dump(components, file)
            print("...Успешное сохранение!\n")
        else:
            if Path(self.components_file_bin).is_file():
                with open(self.components_file_bin, "rb") as file:
                    components = pickle.load(file)

        if get_new_servers_list:
            # Серверы: Получение
            print("Серверы: Получение")
            catalog = nord_server.catalog.Catalog(self.webdriver_path, False) if catalog is None else catalog
            servers = catalog.get_servers()

            # Серверы: Сохранение
            print("Серверы: Сохранение..", end="")

            with open(self.servers_list_file_bin, "wb") as file:
                pickle.dump(servers, file)
            print("...Успешное сохранение!\n")
        else:
            if Path(self.servers_list_file_bin).is_file():
                with open(self.servers_list_file_bin, "rb") as file:
                    servers = pickle.load(file)

        if get_new_servers_configs:
            configurator = nord_server.configurator.Configurator(self.webdriver_path)

            # DEBUG
            # import random
            # servers_to_check = random.choices(servers_urls, k=5)
            # servers = configurator.get_config_components(servers_to_check)

            # Конфигураторы: Получение
            servers_with_configs, config_components = configurator.get_config_components(servers)
            print(f"\nЗагружены данные всех серверов\n")

            # Конфигураторы: Сохранение
            print("Конфигураторы: Сохранение..", end="")

            with open(self.servers_with_conf_list_bin, "wb") as file:
                pickle.dump(servers_with_configs, file)

            with open(self.configs_components_bin, "wb") as file:
                pickle.dump(config_components, file)
            print("...Успешное сохранение!\n")

        else:
            if Path(self.servers_with_conf_list_bin).is_file():
                with open(self.servers_with_conf_list_bin, "rb") as file:
                    servers_with_configs = pickle.load(file)

            if Path(self.configs_components_bin).is_file():
                with open(self.configs_components_bin, "rb") as file:
                    config_components = pickle.load(file)

        if len(components):
            components = nord_server.data_prettify.prettify_components(components)

        if len(servers_with_configs):
            servers_with_configs, config_components = nord_server.data_prettify.prettify_servers(servers_with_configs)

        print("Уникальных комплектующих из конфигураторов:", len(config_components))

        print("УСПЕШНОЕ ЗАВЕРШЕНИЕ ПАРСИНГА")
        return {'components': components, 'servers': servers_with_configs, 'config_components': config_components}
