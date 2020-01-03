import xml.etree.ElementTree as ET
from urllib.request import urlopen
from collections import OrderedDict


class XMLColumns:
    def __init__(self):
        self.columns_list = []
        self.test_url = 'http://news-http-doc-internal.prod.factset.com/getstory?id=/home/docs/edgar/2019/20190102/0001387845-18-000001-1.xml&e=false&fsp=false&of=raw'
        self.data_url = ET.parse(urlopen(self.test_url))
        self.root_url = self.data_url.getroot()
        self.test_file = 'C:\\Users\\lirvine\\Documents\\Temp\\loans_wf_files\\tnc_loans_parser_ided_documents_00006B3A_20191219_142115_0eece5bf-6a22-ea11-810e-8cdcd4af21e4.xml'
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
