# -*- coding: utf-8 -*-
"""
Define a class METEO to handle meteo data generated by MeteoSwiss.

@author: joerg.klausen@meteoswiss.ch
"""

# %%
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

    _log = None
    _zip = None
    _staging = None
    _datadir = None
    _name = None
    _logger = None
    _source = None

    @classmethod
    def __init__(cls, name: str, config: dict) -> None:
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
        print("# Initialize METEO")

        try:
            # setup logging
            logdir = os.path.expanduser(config['logs'])
            os.makedirs(logdir, exist_ok=True)
            logfile = '%s.log' % time.strftime('%Y%m%d')
            logfile = os.path.join(logdir, logfile)
            cls._logger = logging.getLogger(__name__)
            logging.basicConfig(level=logging.DEBUG,
                                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                datefmt='%y-%m-%d %H:%M:%S',
                                filename=str(logfile),
                                filemode='a')

            # read instrument control properties for later use
            cls._name = name
            cls._type = config[name]['type']

            # setup data directory
            datadir = os.path.expanduser(config['data'])
            cls._datadir = os.path.join(datadir, name)
            os.makedirs(cls._datadir, exist_ok=True)

            # source of data files
            cls._source = config[name]['source']

            # interval to fetch and stage data files
            cls._staging_interval = config[name]['staging_interval']

            # staging area for files to be transfered
            cls._staging = os.path.expanduser(config['staging']['path'])
            cls._zip = config[name]['staging_zip']

        except Exception as err:
            if cls._log:
                cls._logger.error(err)
            print(err)

    @classmethod
    def store_and_stage_files(cls):
        """
        Fetch data files from local source and move to datadir. Zip files and place in staging area.

        :return: None
        """
        try:
            print("%s .store_and_stage_files (name=%s)" % (time.strftime('%Y-%m-%d %H:%M:%S'), cls._name))

            # get data file from local source
            files = os.listdir(cls._source)

            if files:
                # staging location for transfer
                stage = os.path.join(cls._staging, cls._name)
                os.makedirs(stage, exist_ok=True)

                # store and stage data files
                for file in files:
                    # stage file
                    if cls._zip:
                        # create zip file
                        archive = os.path.join(stage, "".join([file[:-4], ".zip"]))
                        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as fh:
                            fh.write(os.path.join(cls._source, file), file)
                    else:
                        shutil.copyfile(os.path.join(cls._source, file), os.path.join(stage, file))

                    # move to data storage location
                    shutil.move(os.path.join(cls._source, file), os.path.join(cls._datadir, file))

        except Exception as err:
            if cls._log:
                cls._logger.error(err)
            print(err)

    @classmethod
    def print_meteo(cls) -> None:
        try:
            files = os.listdir(cls._source)
            if files:
                file = max([x for x in files if "VMSW" in x])

                data = cls.extract_short_bulletin(os.path.join(cls._source, file))
                print(colorama.Fore.GREEN + "%s [%s] zzzztttt: %s tre200s0: %s uor200s0: %s" % \
                      (time.strftime("%Y-%m-%d %H:%M:%S"), cls._name,
                       data['zzzztttt'], data['tre200s0'], data['uor200s0']))

        except Exception as err:
            if cls._log:
                cls._logger.error(err)
            print(err)

    @classmethod
    def extract_short_bulletin(cls, file) -> dict:
        """
        Read file and extract meteo data.

        :param file:
        :return:
        """
        try:
            if "VMSW" in file:
                with open(file, "r", encoding='utf8') as fh:
                    for i in range(3):
                        fh.readline()
                    header = fh.readline().split()
                    data = fh.readline().split()
                data = dict(zip(header, data))
            else:
                data = None

            return data

        except Exception as err:
            if cls._log:
                cls._logger.error(err)
            print(err)

# %%
