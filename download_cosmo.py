# -*- coding: utf-8 -*-

## Zhiyu/Drew Li & Xiaohui/Sherry Qiao
## Brigham Young University, 2018

## Adapted from Alan D. Snow and Michael Souffront's spt_compute\ftp_ecmwf_download.py
## https://github.com/BYU-Hydroinformatics/spt_compute

from glob import glob
import os
from shutil import rmtree

""""
This section adapted from https://github.com/keepitsimple/pyFTPclient
"""
import threading
import ftplib
import socket
import time

from multiprocessing import Pool, Process
import numpy as np
import datetime
import glob


ftp_host = "XXXXX"
ftp_user = "XXXX"
ftp_password = "XXXXXX"
ftp_dir = "XXXXXXXX"
use_multiple_processing = True
remove_expired_files_from_ftp = False
file_life_span_hrs_on_ftp = 24*2
process_num = 4
local_dir = "XXXXXXXXXX"


def setInterval(interval, times=-1):
    # This will be the actual decorator,
    # with fixed interval and times parameter
    def outer_wrap(function):
        # This will be the function to be
        # called
        def wrap(*args, **kwargs):
            stop = threading.Event()

            # This is another function to be executed
            # in a different thread to simulate setInterval
            def inner_wrap():
                i = 0
                while i != times and not stop.isSet():
                    stop.wait(interval)
                    function(*args, **kwargs)
                    i += 1

            t = threading.Timer(0, inner_wrap)
            t.daemon = True
            t.start()
            return stop

        return wrap

    return outer_wrap


class PyFTPclient:
    def __init__(self, host, login, passwd, directory="", monitor_interval=30):
        self.host = host
        self.login = login
        self.passwd = passwd
        self.directory = directory
        self.monitor_interval = monitor_interval
        self.ptr = None
        self.max_attempts = 15
        self.waiting = True
        self.ftp = ftplib.FTP(self.host)

    def connect(self):
        """
        Connect to ftp site
        """
        self.ftp = ftplib.FTP(self.host)
        self.ftp.set_debuglevel(0)
        self.ftp.set_pasv(True)
        self.ftp.login(self.login, self.passwd)
        if self.directory:
            self.ftp.cwd(self.directory)
        # optimize socket params for download task
        self.ftp.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if os.name != 'nt':
            self.ftp.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 75)
            self.ftp.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)

    def download_file(self, dst_filename, local_filename=None):
        res = ''
        if local_filename is None:
            local_filename = dst_filename

        with open(local_filename, 'w+b') as f:
            self.ptr = f.tell()

            @setInterval(self.monitor_interval)
            def monitor():
                if not self.waiting:
                    if f and not f.closed:
                        i = f.tell()
                        if self.ptr < i:
                            print("DEBUG: %s %d  -  %0.1f Kb/s" % (f.name, i, (i - self.ptr) / (1024 * self.monitor_interval)))
                            self.ptr = i
                        else:
                            self.ftp.close()

            self.connect()
            self.ftp.voidcmd('TYPE I')
            dst_filesize = self.ftp.size(dst_filename)

            mon = monitor()
            while dst_filesize > f.tell():
                try:
                    self.connect()
                    self.waiting = False
                    # retrieve file from position where we were disconnected
                    res = self.ftp.retrbinary('RETR %s' % dst_filename, f.write) if f.tell() == 0 else \
                        self.ftp.retrbinary('RETR %s' % dst_filename, f.write, rest=f.tell())

                except:
                    self.max_attempts -= 1
                    if self.max_attempts == 0:
                        mon.set()
                        raise
                    self.waiting = True
                    print('INFO: waiting 30 sec...')
                    time.sleep(30)
                    print('INFO: reconnect')

            mon.set()  # stop monitor
            self.ftp.close()

            if not res.startswith('226'):  # file successfully transferred
                print('ERROR: Downloaded file {0} is not full.'.format(dst_filename))
                print(res)
                return False
            return True


"""
end pyFTPclient adapation section
"""


def get_ftp_forecast_list(file_match, ftp_host, ftp_login,
                          ftp_passwd, ftp_directory):
    """
    Retrieves list of forecast on ftp server
    """
    ftp_client = PyFTPclient(host=ftp_host,
                             login=ftp_login,
                             passwd=ftp_passwd,
                             directory=ftp_directory)
    ftp_client.connect()
    file_list = ftp_client.ftp.nlst(file_match)
    ftp_client.ftp.quit()
    return file_list


def download_files_from_ftp(files, ftp_host, ftp_login,
                            ftp_passwd, ftp_directory,
                            local_dir=None):
    """
    Download a list of files from ftp server
    """
    ftp_client = PyFTPclient(host=ftp_host,
                             login=ftp_login,
                             passwd=ftp_passwd,
                             directory=ftp_directory)
    ftp_client.connect()

    if type(files) is not list:
        files = [files]

    for file_to_download in files:
        local_filename = None
        if local_dir is not None:
            local_filename = os.path.join(local_dir, file_to_download)
        ftp_client.download_file(file_to_download, local_filename)

    try:
        ftp_client.ftp.quit()
    except Exception:
        pass
    return files


def remove_old_ftp_downloads(folder):
    """
    Remove all previous ECMWF downloads
    """
    all_paths = glob(os.path.join(folder, 'Runoff*netcdf*'))
    for path in all_paths:
        if os.path.isdir(path):
            rmtree(path)
        else:
            os.remove(path)


def remove_files_from_ftp(files, ftp_host, ftp_login,
                            ftp_passwd, ftp_directory):
    """
        Download a list of files from ftp server
        """
    ftp_client = PyFTPclient(host=ftp_host,
                             login=ftp_login,
                             passwd=ftp_passwd,
                             directory=ftp_directory)
    ftp_client.connect()

    if type(files) is not list:
        files = [files]

    for file in files:
        try:
            ftp_client.ftp.delete(file)
        except Exception as ex:
            print("Failed to remove a file from FTP server: {fn}".format(fn=file))

    try:
        ftp_client.ftp.quit()
    except Exception:
        pass
    return files

    pass


def find_downloaded_files(host,
                          login,
                          passwd,
                          directory,
                          local_dir,
                          search_pattern="*"):

    ftp_client = PyFTPclient(host=host,
                             login=login,
                             passwd=passwd,
                             directory=directory)
    ftp_client.connect()
    file_list_ftp = ftp_client.ftp.nlst(search_pattern)
    file_list_local = glob.glob(os.path.join(local_dir, search_pattern))
    file_list_local = [os.path.basename(fn) for fn in file_list_local]

    matched_file_list = []
    wrong_size_list = []
    for file_ftp in file_list_ftp:
        # check filename
        if file_ftp in file_list_local:
            # check file size
            size_ftp = ftp_client.ftp.size(file_ftp)  # in bytes
            size_local = os.path.getsize(os.path.join(local_dir, file_ftp))  # in bytes
            if size_ftp == size_local:
                matched_file_list.append(file_ftp)
            else:
                wrong_size_list.append(file_ftp)

    ftp_client.ftp.quit()
    return {"files_ftp": file_list_ftp,
            "files_local": file_list_local,
            "downloaded": matched_file_list,
            "wrong_size": wrong_size_list,
            }


def is_expired_filename(in_fn, life_span_hrs=file_life_span_hrs_on_ftp):
    model_run_datetime_str = in_fn.split("_")[1]
    model_run_datetime = datetime.datetime.strptime(model_run_datetime_str, "%Y%m%d%H")
    time_delta = datetime.timedelta(hours=life_span_hrs)
    if model_run_datetime + time_delta < datetime.datetime.utcnow():
        return True
    return False


if __name__ == "__main__":

    #fn_list = get_ftp_forecast_list("PLATANC_2018080612_*.nc", ftp_host, ftp_user, ftp_password, ftp_dir)
    print("Check downloaded files")
    download_info = find_downloaded_files(ftp_host, ftp_user, ftp_password, ftp_dir, local_dir, search_pattern="*")

    downloaded_list = download_info['downloaded']
    not_downloaded_list = list(set(download_info['files_ftp']).difference(set(downloaded_list)))
    fn_list = not_downloaded_list
    fn_list.sort()
    print("Downloading the following files: ")
    print(fn_list)

    if use_multiple_processing and len(fn_list) > 1:
        if len(fn_list) < process_num:
            process_num = len(fn_list)
        chunk_list = np.array_split(fn_list, process_num)
        processes = []
        for chunk in chunk_list:
            p = Process(target=download_files_from_ftp,
                        args=(chunk.tolist(), ftp_host, ftp_user, ftp_password, ftp_dir, local_dir))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()
    else:
        download_files_from_ftp(fn_list, ftp_host, ftp_user, ftp_password, ftp_dir, local_dir)

    print ("Check downloaded files again")
    download_info = find_downloaded_files(ftp_host, ftp_user, ftp_password, ftp_dir, local_dir, search_pattern="*")
    downloaded_list = download_info['downloaded']
    expired_downloaded_filelist = list(filter(lambda x: is_expired_filename(x), downloaded_list))

    # expired_downloaded_filelist = ['PLATANC_2018080100_2018080600.nc', 'PLATANC_2018080200_2018080600.nc']
    if remove_expired_files_from_ftp:
        print("Remove the following expired downloaded files form server")
        print(expired_downloaded_filelist.sort())
        remove_files_from_ftp(expired_downloaded_filelist, ftp_host, ftp_user, ftp_password, ftp_dir)
    print("Done")
    exit(0)