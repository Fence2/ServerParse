import re

from modules.parser_tools import *
from modules.parser_dataclasses import *


def prettify_components_cfg(components: list[Component]):
    pretty_components = dict()
    for comp in components:
        if comp.category.lower() == "оперативная память":
            prettify_ram(comp)

        unique_name = f"{comp.name}|{int(comp.new)}|{comp.price}|{comp.no_sale_price}"
        if unique_name in pretty_components:
            pretty_components[unique_name].resource.append(comp.resource)
            continue

        comp.resource = [comp.resource]

        pretty_components[unique_name] = comp

    pretty_components = list(pretty_components.values())
    pretty_components.sort(key=lambda x: (x.category, x.name, x.price))

    return pretty_components


def prettify_servers(servers):
    for server in servers:
        if "12 LFF" in server.name:
            server.name = re.sub("12 LFF", "12LFF", server.name, flags=re.I)

        server.config_price = server.card_price

        if not len(server.components):
            continue

        for comp in server.components:
            if comp.checked and comp.price != 0:
                server.config_price -= comp.price * comp.checked_amount
                comp.checked = False

    return servers
