import configparser
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from collections import OrderedDict


class XMLColumns:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('reg_d_settings.ini')
        self.test_url = config['Settings']['TestURL']
        self.test_file = config['Settings']['TestFile']
        self.columns_list = []
        self.data_url = ET.parse(urlopen(self.test_url))
        self.root_url = self.data_url.getroot()
        self.data_file = ET.parse(self.test_file)
        self.root_file = self.data_file.getroot()

    def path_of_elems(self, elem, elem_path=""):
        for child in elem:
            if len(child) == 0:
                self.columns_list.append(f'\n{elem_path}/{child.tag}')
            else:
                self.path_of_elems(child, f'{elem_path}/{child.tag}')

    def remove_dupes_from_dict(self):
        self.columns_list = list(OrderedDict.fromkeys(self.columns_list))

    def elem_path_file(self, file_name):
        with open(file_name, 'w') as f:
            for col in self.columns_list:
                col = col.replace('edgarSubmission/', '').strip()
                f.write(col + '\n')


test = XMLColumns()
test.path_of_elems(test.root_url, test.root_url.tag)
test.remove_dupes_from_dict()
test.elem_path_file('test_xml_col_list.txt')
