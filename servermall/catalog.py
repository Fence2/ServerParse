import bs4
from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup
import random


# def categories_and_components(tag):
#     if 'class' in tag.attrs:
#         class_ = tag['class']
#         if "items-counter" in class_ and tag.text != "":
#             return True
#
#         if "items-grid" in class_:
#             return True


class Catalog(AbstractCatalog):
    delay = 20

    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_components() -> list[Component]:
        """
        Функция возвращает комплектующие в виде списка:
        [
            Component,

            Component,

            ...
        ]
        """
        components = list()
        return components

    @staticmethod
    def get_servers() -> list[Server]:
        servers = list()

        Catalog.driver = selenium_try_to_get_max_5x(Catalog.driver, MAIN_URL, True)
        time.sleep(Catalog.delay)

        random.shuffle(RANDOM_URL)

        for url in RANDOM_URL[:random.randint(2, 5)]:
            Catalog.driver = selenium_try_to_get_max_5x(Catalog.driver, url, True)
            time.sleep(Catalog.delay)

        catalog_urls = [CATALOG_CONFIGURATORS_HP_URL, CATALOG_CONFIGURATORS_DELL_URL]
        random.shuffle(catalog_urls)
        for url in catalog_urls:
            catalog = selenium_try_to_get_max_5x(
                driver=Catalog.driver,
                url=url,
                lambda_condition=lambda tag: tag.name == "h1" and "сервер" in tag.text.lower()
            )
            time.sleep(Catalog.delay)
            soup = BeautifulSoup(catalog.page_source, "lxml")
            pages = soup.find(class_="pager").ul.findAll("li")[-1].string
            pages = int(pages)

            print("Страниц с товарами:", pages)
            for page in range(1, pages + 1):
                if page != 1:
                    page_url = url + f"?PAGEN_1={page}"
                    catalog = selenium_try_to_get_max_5x(
                        driver=catalog,
                        url=page_url,
                        lambda_condition=lambda tag: tag.name == "h1" and "сервер" in tag.text.lower()
                    )
                    time.sleep(Catalog.delay)
                    page_soup = BeautifulSoup(catalog.page_source, "lxml").body
                else:
                    page_soup = soup
                page_servers_cards = page_soup.find(
                    class_="products-wrapper").find_all(class_="product-card__inner")
                card: bs4.Tag
                for card in page_servers_cards:
                    try:
                        name = card.find_all("span", class_='product-card__model')[-1]
                        name = name.text.strip()
                        name = format_name(name)
                    except Exception as e:
                        print("Ошибка! Нет названия у сервера")
                        continue

                    try:
                        condition = card.find("span", class_="product-card__type").text.strip()
                    except Exception as e:
                        condition = "REFURBISHED"
                    finally:
                        condition = new_or_ref(condition)

                    try:
                        price = card.find("span", class_="product-card__total-price").text.strip()
                        price = format_price(price)
                    except Exception as e:
                        price = 0

                    try:
                        buttons = card.find_all("a", recursive=False)
                        for button in buttons[::1]:
                            if button.attrs.get("href", "").startswith("/config/"):
                                config_url = MAIN_URL + button.attrs['href'].strip()
                                break
                        else:
                            config_url = ""
                    except Exception as e:
                        config_url = ""

                    server = Server(
                        name=name,
                        new=condition,
                        card_price=price,
                        config_url=config_url
                    )
                    server.get_specs_from_name()
                    servers.append(server)

                print(f"\tТоваров на {page} странице:", len(page_servers_cards))

        print(f"\nВсего найдено: {len(servers)} серверов\n")
        servers.sort(key=lambda server: server.card_price)
        servers.sort(key=lambda server: (server.new, server.category, server.name, server.card_price))
        return servers
