import nord_server
from modules.parser.classes import MainParser


class Parser(MainParser):
    def __init__(self, work_folder, webdriver_path=None, catalog_selenium=False, config_selenium=False):
        super().__init__(
            module=nord_server,
            work_folder=work_folder,
            webdriver_path=webdriver_path,
            catalog_selenium=catalog_selenium,
            config_selenium=config_selenium
        )
