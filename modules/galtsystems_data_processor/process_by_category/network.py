from modules.parser.tools import Patterns, search_from_pattern, sub_not_digits

GS_NETWORK = [
    'X540-T2',
    'X520-DA2',
    'i350-T4 V2',
    'i350-T2 V2',
    'Intel E1G42ET',
    'Intel i350/X540-T2',
    'X710-DA2',
    'X550-T2',
]

GS_NETWORK_DICT = {
    ('X540', 'T2'): 'X540-T2',
    ('X520', 'DA2'): 'X520-DA2',
    ('V2', 'i350', 'T4'): 'i350-T4 V2',
    ('V2', 'i350', 'T2'): 'i350-T2 V2',
    ('E1G42ET',): 'Intel E1G42ET',
    ('i350',): 'Intel i350',
    ('X540', 'T2'): 'Intel X540-T2',
    ('X710', 'DA2'): 'X710-DA2',
    ('X550', 'T2'): 'X550-T2',
}


def network_process(raw_network_data):
    gs_network_final = dict.fromkeys(GS_NETWORK_DICT.values(), "")
    for network in raw_network_data:
        if search_from_pattern(Patterns.NEW, network.name) is not None:
            continue

        for gs_network_key, gs_network_name in GS_NETWORK_DICT.items():
            for spec in gs_network_key:
                if spec.upper() not in network.name.upper():
                    break
            else:
                gs_network_final[gs_network_name] = network.price
                network.we_need = True

    return gs_network_final, raw_network_data


__all__ = ["network_process"]
