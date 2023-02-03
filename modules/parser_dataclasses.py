import dataclasses
import re
from dataclasses import dataclass, field

from modules.parser_tools import *


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
        if self.brand == "SUPERMICRO":
            self.model = search_from_pattern(Patterns.SERVER.supermicro_model, self.name)
        else:
            self.model = search_from_pattern(Patterns.SERVER.model, self.name)
            if self.model is not None and self.brand == "HP":
                self.model = re.sub(r"[pр]", "", self.model, flags=re.I)
                self.name = re.sub(search_from_pattern(Patterns.SERVER.model, self.name), self.model, self.name, flags=re.I)

        # GENERATION
        self.generation = search_from_pattern(Patterns.SERVER.gen, self.name)

        # UNITS
        self.units = search_from_pattern(Patterns.SERVER.units, self.name)

        # CATEGORY
        self.category = get_server_category(self)

    def to_dict(self):
        return dataclasses.asdict(self)
