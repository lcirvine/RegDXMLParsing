import os
import sys
import logging
import configparser
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from urllib.request import urlopen
from datetime import datetime
from collections import defaultdict, OrderedDict


handler = logging.FileHandler(os.path.join(os.getcwd(), 'Logs', 'Reg D XML Parsing Logs.txt'), mode='a+',
                              encoding='UTF-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.info('-' * 100)


class RegDXML:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('reg_d_settings.ini')
        self.lb_source_file = config['Settings']['SourceFile']
        self.columns_list = []
        self.x_dict = defaultdict(list)
        self.sample_size = 250
        self.test_mode = True

    def read_lb_list(self):
        """Returns a data frame from the source file from list builder"""
        return pd.read_excel(self.lb_source_file)

    def path_of_elems(self, elem, elem_path=""):
        """Creates a string for the path of each element in the XML and appends it to the columns list
        e.g. offeringData/industryGroup/industryGroupType"""
        for child in elem:
            if len(child) == 0 and f'{elem_path}/{child.tag}' not in self.columns_list:
                self.columns_list.append(f'{elem_path}/{child.tag}')
            else:
                self.path_of_elems(child, f'{elem_path}/{child.tag}')

    def cols_from_paths(self):
        """Adds a column in the columns list for the path of each element in the XML.
        Only goes through the first X rows of LB source file based on sample size.
        Duplicates are removed from column list, but the order is kept from original list"""
        df = self.read_lb_list()
        for index, value in df.head(self.sample_size).iterrows():
            url = df.loc[index, 'EDG - URL - XML Filing']
            data_xml = ET.parse(urlopen(url))
            root = data_xml.getroot()
            self.path_of_elems(root, root.tag)
        self.columns_list = list(OrderedDict.fromkeys(self.columns_list))

    def elem_path_file(self, file_name):
        """Saves the columns list into a file.
        The root tag is taken out of the column name or else it won't be found
        All the EDGAR form D docs have the same root: edgarSubmission/ """
        with open(file_name, 'w') as f:
            for col in self.columns_list:
                col = col.replace('edgarSubmission/', '').strip()
                f.write(col + '\n')

    def parse_xml(self):
        """This function parses the XML data and saves it to a dictionary"""
        df = self.read_lb_list()
        if self.test_mode:
            df = df.head(self.sample_size)
        for index, value in df.iterrows():
            self.x_dict['dam_doc_id'].append(df.loc[index, 'Document Id'])
            self.x_dict['iconum'].append(df.loc[index, 'Iconum (Primary)'])
            url = df.loc[index, 'EDG - URL - XML Filing']
            data_xml = ET.parse(urlopen(url))
            root = data_xml.getroot()
            for col in self.columns_list:
                # the root tag (edgarSubmission/) must be taken out
                # otherwise, the item will not be found
                item = data_xml.findall(col.replace(root.tag + '/', '').strip())
                # some items have a many to one relationship
                # for those, the text is concatenated into one string
                if len(item) > 1:
                    item_str = ', \n'.join(map(str, [i.text for i in item]))
                    self.x_dict[col].append(item_str)
                elif len(item) == 1 and item[0].text is not None:
                    self.x_dict[col].append(item[0].text.strip())
                else:
                    self.x_dict[col].append(np.nan)

    def check_dict(self):
        """Before creating a data frame from the dictionary,
        check that the each item in the dictionary has the same number of values"""
        first_key = next(iter(self.x_dict))
        num_values = len(self.x_dict[first_key])
        for k in self.x_dict:
            if len(self.x_dict[k]) != num_values:
                print(f'{k} has {len(self.x_dict[k])} values, the first key has {num_values}')
                logger.info(f'{k} has {len(self.x_dict[k])} values, the first key has {num_values}')
                return False
        return True

    def create_data_frame(self, file_name):
        """This puts the parsed data into it's final format.
        The file is saved with the file name passed to the function.
        The data frame is returned by the function, mainly so that I can log the number of rows added"""
        if self.check_dict():
            df = pd.DataFrame(self.x_dict)
            drop_list = list(df.filter(regex='relatedPersonsList', axis=1))
            df.drop(columns=drop_list, inplace=True)
            df.columns = df.columns.str.replace('edgarSubmission/', '')
            df.to_csv(file_name, index=False, encoding='utf-8-sig')
            return df


if __name__ == '__main__':
    try:
        start_time = datetime.utcnow()
        reg_d = RegDXML()
        reg_d.test_mode = False
        logger.info(f'Sample size: {reg_d.sample_size}')
        logger.info(f'Test mode: {reg_d.test_mode}')
        reg_d.cols_from_paths()
        reg_d.elem_path_file('Reg D XML Paths.txt')
        reg_d.parse_xml()
        df_reg_d = reg_d.create_data_frame('Reg D Data.csv')
        logger.info(f'Number of docs parsed: {len(df_reg_d)}')
        logger.info(f'Time to complete: {str(datetime.utcnow() - start_time)}')
    except Exception as e:
        logger.info('ERROR')
        logger.info(e, exc_info=sys.exc_info())
        logger.info('-' * 100)
