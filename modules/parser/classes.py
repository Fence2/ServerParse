import dataclasses
import json
import pickle

from abc import ABC, abstractmethod
from pathlib import Path

from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from .tools import *


@dataclass(order=True)
class Component:
    category: str
    name: str
    new: bool

    checked: bool = False
    checked_amount: int = 0

    price: int = 0

    no_sale_price: int = 0

    resource: str | list = ""

    def __repr__(self) -> str:
        result = f"{self.category}: {self.name} - {str(self.price)}"

        if self.no_sale_price != 0:
            result += f" - {str(self.no_sale_price)}"

        return result

    def to_dict(self):
        return dataclasses.asdict(self)


@dataclass(order=True)
class Server:
    name: str
    new: bool

    card_price: int = 0
    no_sale_card_price: int = 0

    config_price: int = 0
    no_sale_config_price: int = 0

    config_url: str = ""

    components: list[Component] = field(default_factory=list)
    category: int = 0
    brand: str = None
    model: str = None
    generation: str = None
    units: str = None

    def __repr__(self) -> str:
        result = f"{self.category}: {self.name}{' NEW' if self.new else ''} - " \
                 f"{str(self.card_price if not self.config_price else self.config_price)}"

        if self.no_sale_card_price != 0:
            result += f" - " \
                      f"{str(self.no_sale_card_price if not self.no_sale_config_price else self.no_sale_config_price)}"

        return result

    def get_specs_from_name(self):
        # BRAND
        self.brand = search_from_pattern(Patterns.SERVER.brand, self.name)
        if self.brand == "HP":
            self.name = re.sub(r"Gen", "G", self.name, flags=re.I)

        # MODEL
        if self.brand == "SUPERMICRO":  # noqa
            self.model = search_from_pattern(Patterns.SERVER.supermicro_model, self.name)
        else:
            self.model = search_from_pattern(Patterns.SERVER.model, self.name)
            if self.model is not None and self.brand == "HP":
                self.model = re.sub(r"[pр]", "", self.model, flags=re.I)
                self.name = re.sub(search_from_pattern(Patterns.SERVER.model, self.name), self.model, self.name,
                                   flags=re.I)

        # GENERATION
        self.generation = search_from_pattern(Patterns.SERVER.gen, self.name)

        # UNITS
        self.units = search_from_pattern(Patterns.SERVER.units, self.name)

        # CATEGORY
        self.category = get_server_category(self)

    def to_dict(self):
        return dataclasses.asdict(self)


class SeleniumSupport(ABC):
    __slots__ = ("driver",)

    def __init__(self, webdriver_path: str = None, launch=False):
        if webdriver_path is not None and launch:
            from selenium.webdriver.support.ui import Select  # noqa
            from selenium.webdriver.common.by import By  # noqa
            from selenium.webdriver.chrome.service import Service  # noqa
            from selenium.webdriver.chrome.options import Options  # noqa
            from selenium import webdriver  # noqa

            options = Options()
            options.page_load_strategy = 'eager'
            options.add_argument("window-size=1800,1000")
            try:
                SeleniumSupport.driver = webdriver.Chrome(service=Service(), options=options)
                SeleniumSupport.driver.get("https://www.google.com/?hl=RU")
            except Exception as e:
                print("\nERROR\nСвяжитесь с разработчиком парсеров!\nERROR\n")
                print(e)
                SeleniumSupport.driver = None
                print()
        else:
            SeleniumSupport.driver = None


class AbstractCatalog(SeleniumSupport):
    @staticmethod
    @abstractmethod
    def get_components() -> list[Component]:
        pass

    @staticmethod
    @abstractmethod
    def get_servers() -> list[Server]:
        pass


class AbstractConfigurator(SeleniumSupport):
    @staticmethod
    @abstractmethod
    def get_config_components_categories_html(config_soup: BeautifulSoup) -> list[dict[str, BeautifulSoup]]:
        pass

    # @staticmethod
    # @abstractmethod
    # def get_components_from_categories(categories_html: dict, server: Server) -> list[Component]:
    #     pass

    @staticmethod
    @abstractmethod
    def get_config_components(servers: list[Server]) -> (list[Server], list[Component]):
        pass


class MainParser:
    def __init__(self, *, module, work_folder, webdriver_path=None, catalog_selenium=False, config_selenium=False):
        self.module = module
        self.work_folder = work_folder
        self.components_file_bin = work_folder / "components.bin"
        self.components_file_json = work_folder / "components.json"
        self.servers_list_file_bin = work_folder / "servers_list.bin"
        self.servers_with_conf_list_bin = work_folder / "servers_confs.bin"
        self.configs_components_bin = work_folder / "configs_components.bin"

        self.webdriver_path = webdriver_path
        self.catalog_selenium = catalog_selenium
        self.config_selenium = config_selenium
        self.catalog = None
        self.configurator = None

    def start(
            self,
            get_new_components=True,
            get_new_servers_list=True,
            get_new_servers_configs=True,

    ):
        print(f"\nПарсер {self.module.__name__}\n")
        components = list()
        servers = list()
        servers_with_configs = list()
        config_components = list()

        if get_new_components:
            # Комплектующие: Получение
            print("Комплектующие: Получение")

            self.catalog = self.module.catalog.Catalog(
                webdriver_path=self.webdriver_path,
                launch=self.catalog_selenium
            )

            components = self.catalog.get_components()

            # Комплектующие: Сохранение
            print("Комплектующие: Сохранение..", end="")
            components_json = [comp.to_dict() for comp in components]

            with open(self.components_file_json, "w", encoding="utf-8") as file:
                json.dump(components_json, file, ensure_ascii=False)

            with open(self.components_file_bin, "wb") as file:
                pickle.dump(components, file)
            print("...Успешное сохранение!\n")

            if len(components):
                components = self.module.data_prettify.prettify_components(components)
        else:
            if Path(self.components_file_bin).is_file():
                with open(self.components_file_bin, "rb") as file:
                    components = pickle.load(file)

        if get_new_servers_list or \
                get_new_servers_configs or \
                (get_new_components + get_new_servers_list + get_new_servers_configs == 0):
            if get_new_servers_list:
                # Серверы: Получение
                print("Серверы: Получение")
                self.catalog = self.module.catalog.Catalog(
                    webdriver_path=self.webdriver_path,
                    launch=self.catalog_selenium
                ) if self.catalog is None else self.catalog

                servers = self.catalog.get_servers()

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
                # Конфигураторы: Получение
                try:
                    self.catalog.driver.close()
                except Exception:
                    pass
                print("Конфигураторы: Получение")
                self.configurator = self.module.configurator.Configurator(
                    webdriver_path=self.webdriver_path,
                    launch=self.config_selenium
                )

                servers_with_configs = self.configurator.get_config_components(servers)
                print(f"\nЗагружены данные всех серверов\n")

                # Конфигураторы: Сохранение
                print("Конфигураторы: Сохранение..", end="")

                with open(self.servers_with_conf_list_bin, "wb") as file:
                    pickle.dump(servers_with_configs, file)

                if len(servers_with_configs):
                    servers_with_configs, config_components = self.module.data_prettify.prettify_servers(
                        servers_with_configs)
                    print(f"Уникальных комплектующих из конфигураторов: {len(config_components)}\n")

                with open(self.configs_components_bin, "wb") as file:
                    pickle.dump(config_components, file)
                print("...Успешное сохранение!\n")
            else:
                servers_with_configs = servers
                if Path(self.servers_with_conf_list_bin).is_file():
                    with open(self.servers_with_conf_list_bin, "rb") as file:
                        servers_with_configs = pickle.load(file)

                if Path(self.configs_components_bin).is_file():
                    with open(self.configs_components_bin, "rb") as file:
                        config_components = pickle.load(file)
                    if len(config_components) == 0:
                        _, config_components = self.module.data_prettify.prettify_servers(
                            servers_with_configs)

        return {'components': components, 'servers': servers_with_configs, 'config_components': config_components}
