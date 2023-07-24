# -*- coding: utf-8 -*-
"""
Define a class AEROSOL to handle aerosol data generated by PSI CATCOS.

@author: joerg.klausen@meteoswiss.ch
"""

import os
import time
import logging
import shutil
import zipfile
from mkndaq.utils.filesync import rsync

import colorama


class AEROSOL:
    """
    Virtual aerosol instrumentation.

    Aerosol data are generated from an aethalometer and a nephelometer. The data are pushed in
    a folder that is mounted as a network share.
    These data files are moved locally and staged for transfer.
    """

    _log = None
    _staging = None
    _datadir = None
    _data_storage_interval = None
    _days_to_sync = None
    _name = None
    _logger = None
    _source = None
    _netshare = None

    @classmethod
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
        print("# Initialize AEROSOL")

        try:
            # setup logging
            logdir = os.path.expanduser(config['logs'])
            os.makedirs(logdir, exist_ok=True)
            logfile = '%s.log' % time.strftime('%Y%m%d')
            logfile = os.path.join(logdir, logfile)
            self._logger = logging.getLogger(__name__)
            logging.basicConfig(level=logging.DEBUG,
                                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                datefmt='%y-%m-%d %H:%M:%S',
                                filename=str(logfile),
                                filemode='a')

            # read instrument control properties for later use
            self._name = name
            self._type = config[name]['type']

            # setup data directory
            datadir = os.path.expanduser(config['data'])
            self._datadir = os.path.join(datadir, name)
            os.makedirs(self._datadir, exist_ok=True)

            # source of data files
            dbs = r"\\"
            self._netshare = os.path.join(f"{dbs}{config[name]['socket']['host']}", config[name]['netshare'])

            # reporting/storage
            # self._reporting_interval = config[name]['reporting_interval']
            self._data_storage_interval = config[name]['data_storage_interval']
            if self._data_storage_interval == "None":
                self._data_storage_interval = None

            # days up to present for which files should be synched to data directory
            self._days_to_sync = config[name]['days_to_sync']

            # interval to fetch and stage data files
            self._staging_interval = config[name]['staging_interval']

            # staging area for files to be transfered
            self._staging = os.path.expanduser(config['staging']['path'])
            self._zip = config[name]['staging_zip']

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)

    # @classmethod
    # def store_and_stage_files(self):
    #     """
    #     Fetch data files from local source and move to datadir. Zip files and place in staging area.

    #     :return: None
    #     """
    #     try:
    #         print("%s .store_and_stage_files (name=%s)" % (time.strftime('%Y-%m-%d %H:%M:%S'), self._name))

    #         # get data file from local source
    #         files = os.listdir(self._source)

    #         if files:
    #             # staging location for transfer
    #             stage = os.path.join(self._staging, self._name)
    #             os.makedirs(stage, exist_ok=True)

    #             # store and stage data files
    #             for file in files:
    #                 # stage file
    #                 shutil.move(os.path.join(self._source, file), os.path.join(stage, file))

    #     except Exception as err:
    #         if self._log:
    #             self._logger.error(err)
    #         print(err)


    @classmethod
    def store_and_stage_new_files(self):
        """
        Fetch data files from local source and move to datadir. Zip files and place in staging area.
        New files on the PSI machine are not automatically organized in subfolders!

        :return: None
        """
        try:
            if self._data_storage_interval == 'hourly':
                ftime = "%Y/%m/%d"
            elif self._data_storage_interval == 'daily':
                ftime = "%Y/%m"
            elif self._data_storage_interval is None:
                ftime = None
            else:
                raise ValueError(f"Configuration 'data_storage_interval' of {self._name} must be <None|hourly|daily>.")

            try:
                if os.path.exists(self._netshare):
                    files_received = rsync(source=self._netshare, 
                                            target=self._datadir, 
                                            buckets=self._data_storage_interval, 
                                            days=self._days_to_sync)
                    for file in files_received:    
                        # stage data for transfer
                        stage = os.path.join(self._staging, self._name)
                        os.makedirs(stage, exist_ok=True)

                        if self._zip:
                            # create zip file
                            archive = os.path.join(stage, "".join([os.path.basename(file)[:-4], ".zip"]))
                            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as fh:
                                fh.write(file, os.path.basename(file))
                        else:
                            shutil.copyfile(file, os.path.join(stage, os.path.basename(file)))

                        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} .store_and_stage_new_files (name={self._name}, file={os.path.basename(file)})")
                else:
                    msg = f"{time.strftime('%Y-%m-%d %H:%M:%S')} (name={self._name}) Warning: {self._netshare} is not accessible!)"
                    if self._log:
                        self._logger.error(msg)
                    print(colorama.Fore.RED + msg)

            except:
                print(colorama.Fore.RED + f"{time.strftime('%Y-%m-%d %H:%M:%S')} (name={self._name}) Warning: {self._netshare} is not accessible!)")

                return

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)

    # try:
    #     print("%s .store_and_stage_files (name=%s)" % (time.strftime('%Y-%m-%d %H:%M:%S'), self._name))

    #     # get data file from local source
    #     files = os.listdir(self._source)

    #     if files:
    #         # staging location for transfer
    #         stage = os.path.join(self._staging, self._name)
    #         os.makedirs(stage, exist_ok=True)

    #         # store and stage data files
    #         for file in files:
    #             # stage file
    #             shutil.move(os.path.join(self._source, file), os.path.join(stage, file))

    # except Exception as err:
    #     if self._log:
    #         self._logger.error(err)
    #     print(err)


    @classmethod
    def print_aerosol(self) -> None:
        try:
            # files = os.listdir(self._source)
            # if files:
            #     file = max([x for x in files if "VMSW" in x])
            #
            #     data = self.extract_short_bulletin(os.path.join(self._source, file))
            print(colorama.Fore.GREEN + "%s [%s] near-real-time display not implemented." %
                  (time.strftime("%Y-%m-%d %H:%M:%S"), self._name))

        except Exception as err:
            if self._log:
                self._logger.error(err)
            print(err)
