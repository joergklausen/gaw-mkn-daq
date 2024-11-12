# -*- coding: utf-8 -*-
"""
Define a class METEO to handle meteo data generated by MeteoSwiss.

@author: joerg.klausen@meteoswiss.ch
"""

import os
import time
import logging
import shutil
import zipfile

import colorama


class METEO:
    """
    Virtual meteo instrumentation.

    Meteo data are generated from a number of instruments and pushed via ftp to local directory.
    These data files are moved locally and staged for transfer.
    """
    def __init__(self, name: str, config: dict) -> None:
        """
        Constructor

        Parameters
        ----------
        name : str
            name of instrument as defined in config file
        config : dict
            dictionary of attributes defining the instrument and port
        """
        colorama.init(autoreset=True)

        try:
            self.name = name

            # configure logging
            _logger = f"{os.path.basename(config['logging']['file'])}".split('.')[0]
            self.logger = logging.getLogger(f"{_logger}.{__name__}")
            self.logger.info(f"[{self.name}] Initializing")

            # read instrument control properties for later use
            # self.type = config[name]['type']

            # setup data directory
            root = os.path.expanduser(config['root'])
            self.data_path = os.path.join(root, config['data'], config[name]['data_path'])
            self.staging_path = os.path.join(root, config['staging'], config[name]['staging_path'])
            # datadir = os.path.expanduser(config['data'])
            # self._datadir = os.path.join(datadir, name)
            os.makedirs(self.data_path, exist_ok=True)

            # source of data files
            self.source = config[name]['source']
            self.pattern = config[name]['pattern']

            # interval to fetch and stage data files
            # self.staging_interval = config[name]['staging_interval']

            # reporting/storage
            self.reporting_interval = config[name]['reporting_interval']
            if not (self.reporting_interval==10 or (self.reporting_interval % 60)==0) and self.reporting_interval<=1440:
                raise ValueError(f"[{self.name}] reporting_interval must be 10 or a multiple of 60 and less or equal to 1440 minutes.")

            # staging area for files to be transfered
            self.staging = os.path.join(root, os.path.expanduser(config['staging']), self.name)
            os.makedirs(self.staging, exist_ok=True)
            self._zip = config[name]['staging_zip']

            # configure remote transfer
            self.remote_path = config[name]['remote_path']

        except Exception as err:
            self.logger.error(f"[{self.name}] {err}")


    def store_and_stage_files(self):
        """
        Fetch data files from local source and move to datadir. Zip files and place in staging area.

        :return: None
        """
        try:
            # print("%s .store_and_stage_files (name=%s)" % (time.strftime('%Y-%m-%d %H:%M:%S'), self.name))

            # get data file from local source
            files = os.listdir(self.source)

            if files:
                # staging location for transfer
                # stage = os.path.join(self.staging, self.name)
                # os.makedirs(stage, exist_ok=True)

                # store and stage data files
                for file in files:
                    # stage file
                    if self._zip:
                        # create zip file
                        archive = os.path.join(self.staging, "".join([file[:-4], ".zip"]))
                        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as fh:
                            fh.write(os.path.join(self.source, file), file)
                    else:
                        shutil.copyfile(os.path.join(self.source, file), os.path.join(self.staging, file))

                    # move to data storage location
                    target = os.path.join(self.data_path, time.strftime("%Y"), time.strftime("%m"), time.strftime("%d"))
                    os.makedirs(target, exist_ok=True)
                    shutil.move(os.path.join(self.source, file), os.path.join(target, file))

        except Exception as err:
            self.logger.error(err)


    def print_meteo(self) -> None:
        try:
            files = os.listdir(self.source)
            if len(files)>0:
                # self.logger.debug(colorama.Fore.GREEN + f"[{self.name}] {files}")
                file = max([x for x in files if self.pattern in x])

                data = self.extract_bulletin(os.path.join(self.source, file))
                # self.logger.info(colorama.Fore.GREEN + f"[{self.name}] zzzztttt: {data['zzzztttt']} tre200s0: {data['tre200s0']} uor200s0: {data['uor200s0']}")
                self.logger.debug(colorama.Fore.GREEN + f"[{self.name}] {[f'{key}: {value},' for key, value in data.items()]}")
            else:
                self.logger.warning(colorama.Fore.RED + "no recent data to display")
        except Exception as err:
            self.logger.error(colorama.Fore.RED + f"print_meteo: {err}; data: {data}")


    def extract_bulletin(self, file) -> dict:
        """
        Read file and extract meteo data.

        :param file:
        :return:
        """
        try:
            if "VRXA00" in file:
                with open(file, "r", encoding='utf8') as fh:
                    for i in range(3):
                        fh.readline()
                    header = fh.readline().split()
                    data = fh.readline().split()
                data = dict(zip(header, data))
            else:
                data = dict()

            return data

        except Exception as err:
            self.logger.error(err)
            return dict()
