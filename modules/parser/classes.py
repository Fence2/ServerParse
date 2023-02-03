import dataclasses

from abc import ABC, abstractmethod
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
        result = f"{self.category}: {self.name} - {str(self.card_price if not self.config_price else self.config_price)}"

        if self.no_sale_card_price != 0:
            result += f" - {str(self.no_sale_card_price if not self.no_sale_config_price else self.no_sale_config_price)}"

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
                SeleniumSupport.driver = webdriver.Chrome(service=Service(webdriver_path), options=options)
            except Exception as e:
                print("\nERROR\nОбновите ваш chromedriver драйвер!\nERROR\n")
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
