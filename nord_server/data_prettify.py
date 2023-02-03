from modules.parser import *


def prettify_components(components):
    for comp in components:
        # Корректировка RAM
        if comp.category.lower() == "оперативная память":
            prettify_ram(comp, nord_server=True)

    return components


def prettify_components_cfg(components: list[Component]):
    pretty_components = dict()
    for comp in components:
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
    all_components = list()
    for server in servers:
        if server.config_price == 0:
            server.config_price = server.card_price
        if re.search(r"\+\s?\d+[SL]FF", server.name, re.I) is not None:
            if server.category < 4:
                server.category += 3
        if not len(server.components):
            continue
        server_ddr = None
        for comp in server.components:
            if comp.category.lower() == "оперативная память":
                prettify_ram(comp, nord_server=True)
            if comp.category.lower() == 'оперативная память':
                ddr = search_from_pattern(Patterns.RAM.ddr, comp.name)
                if ddr is None:
                    if server_ddr is not None:
                        comp.name += " " + server_ddr
                    else:
                        ddr_num = re.search(r"\bPC\d\D", comp.name, re.I)
                        if ddr_num is not None:
                            ddr_num = str(sub_not_digits(ddr_num.group()))
                            ddr = f"DDR{ddr_num}"
                            comp.name += " " + ddr
                            server_ddr = ddr
                else:
                    server_ddr = ddr
        all_components += server.components

    return servers, prettify_components_cfg(all_components)
