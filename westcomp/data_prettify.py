from modules.parser import *


def prettify_components(components):
    pretty_components = standard_prettify_components(components)

    return pretty_components


def prettify_components_cfg(components: list[Component], nord_server=False):
    pretty_components = standard_prettify_components_cfg(components, nord_server=nord_server)

    return pretty_components


def prettify_servers(servers):
    all_components = list()
    for server in servers:
        standard_prettify_server(server)
        server.components = prettify_components(server.components)
        all_components += server.components

    return servers, prettify_components_cfg(all_components)
