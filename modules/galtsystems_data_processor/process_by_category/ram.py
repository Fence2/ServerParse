import re
from pathlib import Path
from dataclasses import dataclass
from modules.parser.tools import Patterns, search_from_pattern, sub_not_digits, get_options, get_unique_name


@dataclass(slots=True, kw_only=True)
class RAM:
    ddr: str = ""
    ecc: str = ""
    dimm: str = ""
    capacity: str = ""
    freqHZ: str = ""
    freqPC: str = ""
    new: str = ""

    @staticmethod
    def get_attrs():
        return (
            "ddr",
            "ecc",
            "dimm",
            "capacity",
            "new",
        )


specs = (
    Patterns.RAM.ddr,  # 0
    Patterns.RAM.capacity,  # 1
    Patterns.RAM.freqHZ,  # 2
    Patterns.RAM.freqPC,  # 3
    Patterns.RAM.dimm,  # 4
    Patterns.RAM.not_ecc,  # 5
    Patterns.NEW,  # 6
)


def get_ram_specs_keys(all_ram):
    for ram in all_ram:
        ram_specs: list = [search_from_pattern(spec, ram.name) for spec in specs]
        ram.key = RAM(
            ddr=str(sub_not_digits(ram_specs[0])) if ram_specs[0] is not None else '',
            ecc='Y' if ram_specs[4] is None else 'N',
            dimm=ram_specs[4] if ram_specs[4] is not None else 'RDIMM',
            capacity=str(sub_not_digits(ram_specs[1])) if ram_specs[1] is not None else '',
            freqHZ=str(sub_not_digits(ram_specs[2])) if ram_specs[2] is not None else '',
            freqPC=re.findall(r"\d+", ram_specs[3])[-1] if ram_specs[3] is not None else '',
            new='Y' if ram_specs[6] is not None else ''
        )
    return all_ram


def get_ram_name(ram_item: RAM, gs_ram_final: dict):
    ram_name = list()
    if len(ram_item.ddr):
        ram_name.append(f"DDR{ram_item.ddr}")
    if len(ram_item.capacity):
        ram_name.append(f"{ram_item.capacity}GB")
    if len(ram_item.dimm):
        ram_name.append(f"{ram_item.dimm}")
    if len(ram_item.freqHZ):
        ram_name.append(f"{ram_item.freqHZ}MHz")
    if len(ram_item.freqPC):
        ram_name.append(f"PC{ram_item.ddr}-{ram_item.freqPC}")
    if len(ram_item.ecc) and ram_item.ecc == "Y":
        ram_name.append(f"ECC")
    if len(ram_item.new):
        ram_name.append("NEW")

    ram_name = " ".join([i for i in ram_name if len(i.strip())])

    return get_unique_name(ram_name, gs_ram_final)


def get_gs_ram_item(gs_ram):
    return RAM(
        ddr=gs_ram.get('DDR (2-5)', ''),
        ecc=gs_ram.get('ECC (Y/N)', '') if gs_ram.get('ECC (Y/N)', '') == 'Y' else '',
        dimm=gs_ram.get('DIMM (RDIMM or others)', ''),
        capacity=gs_ram.get('Capacity (GB)', ''),
        freqHZ=gs_ram.get('Frequency (MHZ)', ''),
        freqPC=gs_ram.get('Frequency (PC3/4)', ''),
        new=gs_ram.get('New (Y/N)' if gs_ram.get('New (Y/N)', '') == 'Y' else '', ''),
    )


def ram_process(all_ram):
    gs_ram_final = dict()
    ram_options = get_options(Path.cwd() / "Options.xlsx",
                              sheet_name="RAM")
    if ram_options is None:
        return {}, all_ram

    if not len(all_ram):
        for gs_ram in ram_options:
            gs_ram_item = get_gs_ram_item(gs_ram)
            ram_name = get_ram_name(gs_ram_item, gs_ram_final)
            gs_ram_final[ram_name] = 0
        return gs_ram_final, all_ram

    all_ram = get_ram_specs_keys(all_ram)

    for gs_ram in ram_options:
        gs_ram_item = get_gs_ram_item(gs_ram)
        ram_from_parser = None
        for ram in all_ram:
            good = list()
            for attr in RAM.get_attrs():
                good.append(getattr(ram.key, attr).upper() == getattr(gs_ram_item, attr).upper())
            if len(ram.key.freqHZ):
                if isinstance(gs_ram_item.freqHZ, str):
                    good.append(ram.key.freqHZ == gs_ram_item.freqHZ)
                else:
                    good.append(ram.key.freqHZ in gs_ram_item.freqHZ)
            elif len(ram.key.freqPC):
                if isinstance(gs_ram_item.freqPC, str):
                    good.append(ram.key.freqPC == gs_ram_item.freqPC)
                else:
                    good.append(ram.key.freqPC in gs_ram_item.freqPC)

            good = all(good)
            if good:
                ram.we_need = True
                ram_from_parser = ram
                break

        price = ram_from_parser.price if ram_from_parser is not None else 0

        ram_name = get_ram_name(gs_ram_item, gs_ram_final)

        gs_ram_final[ram_name] = price

    return gs_ram_final, all_ram


__all__ = ["ram_process"]
