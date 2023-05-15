from modules.parser import *
from bs4 import BeautifulSoup


class Configurator(AbstractConfigurator):
    delay = 3

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_config_components(servers: list[Server]):
        return servers

    @staticmethod
    def get_config_components_categories_html(config_soup: BeautifulSoup) -> dict[str, dict]:
        """
        Функция собирает категории комплектующих конфигуратора и возвращает их в виде словаря:

        {
            "Оперативная память": category -> BeautifulSoup,

            "Процессоры": category -> BeautifulSoup,

            ...
        }
        """
        categories = dict()
        return categories

    @staticmethod
    def get_components_from_categories(categories_html: dict, server: Server) -> list[Component]:
        """
        Метод для получения комплектующих из каждой категории конфигуратора
        """

        cfg_components = list()
        return cfg_components
