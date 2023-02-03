from modules.parser import *


def prettify_components_cfg(components: list[Component]):
    pretty_components = standard_prettify_components_cfg(components)

    return pretty_components


def prettify_servers(servers):
    for server in servers:
        standard_prettify_server(server)

    return servers
