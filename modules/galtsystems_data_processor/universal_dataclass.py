from dataclasses import dataclass


@dataclass(order=True)
class ExcelItem:
    name: str
    key: tuple | None = None
    price: int | dict = -1
    new: bool = False
    no_sale_price: int = -1
    we_need: bool = False
    category: str = "Неизвестно"

    def __repr__(self):
        return f'{["______", "NEED"][self.we_need]}, {self.category}: {self.name} | {self.key} | {self.price}'
