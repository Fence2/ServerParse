from modules.parser import *
from .constants import *
from bs4 import BeautifulSoup


class Configurator(AbstractConfigurator):
    def __init__(self, webdriver_path: str = None, launch=False):
        super().__init__(webdriver_path, launch)

    @staticmethod
    def get_config_components_categories_html(config_soup: BeautifulSoup) -> list:
        """
        Функция собирает категории комплектующих конфигуратора и возвращает их в виде словаря:

        {
            "Оперативная память": category -> BeautifulSoup,

            "Процессоры": category -> BeautifulSoup,

            ...
        }
        """
        config = config_soup.find_all("div", recursive=False)
        categories = config[0].find_all(class_="item", recursive=False)
        categories_list = list()
        for category in categories:
            try:
                category_name = category.find("label").text.strip()
                lower_name = category_name.lower()
                if "рельсы" in lower_name:
                    category_name = "Рельсы"
                elif "сетевой адаптер" in lower_name:
                    category_name = "Сетевой адаптер"
                elif "процессор" in lower_name:
                    category_name = "Процессоры"
                elif "память" in lower_name and re.search("ssd|hdd", lower_name) is None:
                    category_name = "Оперативная память"
                elif "raid" in lower_name and "кэш" not in lower_name:
                    category_name = "RAID контроллер"
                elif "салазки" in lower_name:
                    category_name = "Салазки"

                categories_list.append({
                    "name": category_name,
                    "items": category.find("select")
                })

                ram_quantity = category.find("div", class_="sum_amount")
                if ram_quantity is not None:
                    ram_quantity = ram_quantity.text.strip()
                    ram_quantity = sub_not_digits(ram_quantity)
                    categories_list[-1]['quantity'] = ram_quantity
            except AttributeError:
                pass

        if len(config) == 2 and config[1].text.strip() != "":
            trays = config[1].find(class_="item").find_all("select")
            for tray in trays:
                categories_list.append({
                    "name": "Салазки",
                    "items": tray
                })

        return categories_list

    @staticmethod
    def get_components_from_category(item, server: Server) -> list[Component]:
        """
        Функция возвращает список комплектующих из 1 категории конфигуратора

        {
            component -> Component,

            component -> Component,

            ...
        }
        """
        result = list()
        category_name = item['name']
        category_soup = item['items']
        quantity = item.get('quantity', None)
        components_soups = category_soup.find_all("option")
        selected = True
        for i, comp in enumerate(components_soups):
            name = comp.string.strip()
            if name.lower() == "нет":
                selected = False
                continue
            if name.lower() == "выберите значение":
                if "салазки" in category_name.lower():
                    selected = False
                continue
            name = re.sub("HPЕ", "HPE", name, flags=re.I)
            name = re.sub(r"ТB\s", "TB ", name, flags=re.I)
            name = re.sub(r"\+?\s*?\d+\s*?руб(лей)?\.?", "", name, flags=re.I)
            name = format_name(name)

            amount = 1
            if "value" in comp.attrs:
                price = format_price(comp.attrs["value"])
                with_amount = re.fullmatch(
                    r"(?P<amount>\d.?([xх×]|шт|pc)|([xх×]|шт|pc).?\d)(?P<name>.+$)",
                    name,
                    flags=re.I
                )
                if with_amount is not None:
                    amount = with_amount.group("amount")
                    name = with_amount.group("name").strip()
                    amount = sub_not_digits(amount)
                    price = int(price / amount)

                if quantity is not None and category_name == "Оперативная память":
                    ram_GB = search_from_pattern(Patterns.RAM.capacity, name)
                    if ram_GB is not None:
                        ram_GB = sub_not_digits(ram_GB)
                    amount = quantity // ram_GB

            else:
                price = 0

            new_comp = Component(
                category=category_name,
                name=name,
                price=price,
                new=new_or_ref(name),
                checked=selected,
                checked_amount=amount if selected else 0,
                resource=f"{server.name} | {server.config_url}"

            )
            if category_name.title() in ["Салазки", "Рельсы"]:
                new_comp.name = add_info_to_trays_and_rails(category_name, new_comp, server)

            selected = False
            result.append(new_comp)

        return result

    @staticmethod
    def get_config_components(servers: list[str]):
        processed_servers = list()
        all_components = list()
        for count, server_url in enumerate(servers):
            print(f"Осталось получить: {len(servers) - count} конфигураторов")
            time.sleep(2)
            print("Получение данных -", server_url)

            # Получение страницы
            try:
                Configurator.driver = selenium_try_to_get_max_5x(Configurator.driver, server_url, HEADERS)
                soup = BeautifulSoup(Configurator.driver.page_source, "lxml")

                config = soup.find(class_="wcCalculator")

                name = config.find("h1").text.strip()
                name = re.sub("Конфигуратор", "Сервер", name, flags=re.I)
                name = format_name(name)
                print("    Название:", name)

                price = soup.find(attrs={"ng-model": "cost"})
                if price is not None:
                    price = format_price(price.text)
                    print("    Цена:", price)
                else:
                    print("    ОШИБКА!!! Не найдена цена у сервера")
                    price = 0
            except Exception as e:
                print("!!!!!!!!!!!!ОШИБКА!!!!!!!!")
                print(e)
                continue

            server = Server(
                name=name,
                new=new_or_ref(name),
                card_price=price,
                config_price=price,
                config_url=server_url
            )
            server.get_specs_from_name()

            # Получение комплектующих конфигуратора
            components_block = config.find_all(class_="wcCalculator_items")[1]
            components_list = Configurator.get_config_components_categories_html(components_block)
            print(f"    Найдено категорий товаров: {len(components_list)}")

            components = list()
            for item in components_list:
                components.extend(Configurator.get_components_from_category(item, server))
            comp_count = dict()
            for comp in components:
                comp_count[comp.category] = comp_count.get(comp.category, 0) + 1
            for comp_count_cat, comp_count_num in comp_count.items():
                if comp_count_cat in [
                    "Процессоры",
                    "Оперативная память",
                    "Салазки",
                    "Сетевой адаптер",
                    "RAID контроллер",
                    "Рельсы"

                ]:
                    print(f"        {comp_count_cat}: {comp_count_num}")

            server.components = components
            all_components += components

            processed_servers.append(server)

            print()

        Configurator.driver.close()
        return processed_servers, all_components
