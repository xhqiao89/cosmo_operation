import datetime
import os
import shutil
from RAPIDpy.inflow import run_lsm_rapid_process

# Linux command for utc YYYYMMDDHHmm: date -u +%Y%m%d%H%m

class OperationHelperForCOSMO(object):

    datetime_format_str = "%Y%m%d%H"
    forecast_timestep_size_tdelta = datetime.timedelta(hours=1)
    model_run_output_timespan_tdelta = datetime.timedelta(days=7, hours=6)
    model_run_interval_tdelta = datetime.timedelta(hours=12)
    rapid_executable_path = "/root/rapid/run/rapid"
    lsm_source_path = "/mnt_lsm"
    template_path = "/mnt_cosmo_project/template"
    target_path = "/mnt_cosmo_project/run"

    def __init__(self, lsm_source_path, input_path, workspace_path, **kwargs):
        self.lsm_source_path = lsm_source_path
        self.template_path = input_path
        self.target_path = workspace_path
        for k,v in kwargs:
            setattr(self, k, v)


    def _create_folder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        else:
            print("Folder already exists at {}".format(path))


    def _copy_lsm(self, lsm_source_path, target_path, model_dt, symlink=False):
        print("Copying LSM....")
        fn_format = "PLATANC_{model_dt}_{forecast_dt}.nc"

        end_frst_dt = model_dt + self.model_run_output_timespan_tdelta - self.forecast_timestep_size_tdelta
        current_frst_dt = model_dt - self.forecast_timestep_size_tdelta
        while current_frst_dt <= end_frst_dt:
            current_frst_dt += self.forecast_timestep_size_tdelta
            current_frst_fn = fn_format.format(model_dt=model_dt.strftime(self.datetime_format_str), forecast_dt=current_frst_dt.strftime(self.datetime_format_str))

            source_file_path = os.path.join(lsm_source_path, current_frst_fn)
            target_file_path = os.path.join(target_path, current_frst_fn)

            # if symlink:
            #     if not (os.path.islink(target_file_path) and os.path.getsize(source_file_path) == os.path.getsize(target_file_path)):
            #         os.symlink(source_file_path, target_file_path)
            # else:
            if not(os.path.isfile(target_file_path) and os.path.getsize(source_file_path) == os.path.getsize(target_file_path)):
                shutil.copyfile(source_file_path, target_file_path)
                #print("Copying to {}".format(target_file_path))
            else:
                #print("File already exists at {}".format(target_file_path))
                pass
        print("********LSM ready for {}".format(model_dt))


    def _find_closest_model_run_dt(self, dt, search_future=False):
        input_dt = dt
        utc00 = datetime.datetime(year=input_dt.year, month=input_dt.month, day=input_dt.day, hour=0)
        utc12 = datetime.datetime(year=input_dt.year, month=input_dt.month, day=input_dt.day, hour=12)
        if search_future:
            if input_dt > utc12:
                return utc12 + self.model_run_interval_tdelta
            elif input_dt > utc00:
                return utc12
            else:
                return utc00
        else:
            if input_dt >= utc12:
                return utc12
            else:
                return utc00


    def _build_dt_list(self, model_run_first_dt, model_run_last_dt):
        model_run_dt_list = [model_run_first_dt]
        while model_run_dt_list[-1] < model_run_last_dt:
            model_run_dt_list.append(model_run_dt_list[-1]+self.model_run_interval_tdelta)
        model_run_dt_list.sort()
        return model_run_dt_list


    def prepare_model_run(self, model_run_start_dt, model_run_end_dt=None):

        model_run_dt_list = []
        if model_run_end_dt:
            model_run_first_dt = self._find_closest_model_run_dt(model_run_start_dt, search_future=True)
            model_run_last_dt = self._find_closest_model_run_dt(model_run_end_dt)
            model_run_dt_list = self._build_dt_list(model_run_first_dt, model_run_last_dt)
        else:
            model_run_dt_list=[self._find_closest_model_run_dt(model_run_start_dt)]

        print("*****************************Preparing {} runs: {}".format(len(model_run_dt_list), model_run_dt_list))

        for i in range(len(model_run_dt_list)):
            model_run_dt = model_run_dt_list[i]
            print("*********************************Preparing Run No{}: {}".format(i, model_run_dt))

            # create a parent folder for this run YYYYMMDDHH
            run_folder_name = model_run_dt.strftime(self.datetime_format_str)
            run_folder_path = os.path.join(self.target_path, run_folder_name)
            self._create_folder(run_folder_path)
            # create "data" folder
            data_folder_path = os.path.join(run_folder_path, "data")
            self._create_folder(data_folder_path)
            # create lsm folder
            lsm_folder_name = run_folder_name
            lsm_folder_path = os.path.join(data_folder_path, lsm_folder_name)
            self._create_folder(lsm_folder_path)
            # copy lsm
            self._copy_lsm(self.lsm_source_path, lsm_folder_path, model_run_dt)

            # copy input folder
            input_source_path = os.path.join(self.template_path, "input")
            input_folder_path = os.path.join(run_folder_path, "input")
            if os.path.isdir(input_folder_path):
                import uuid
                os.rename(input_folder_path, input_folder_path + "_" + str(uuid.uuid4())[:6])
            shutil.copytree(input_source_path, input_folder_path)

        return model_run_dt_list

    def start_run(self, start_utc_dt, end_utc_dt, init_first_run=False):
        model_run_dt_list = self.prepare_model_run(start_utc_dt, end_utc_dt)

        for i in range(len(model_run_dt_list)):
            model_run_dt = model_run_dt_list[i]
            print("****************************************Run RAPID {}".format(model_run_dt))
            model_run_dt_str = model_run_dt.strftime("%Y%m%d%H")
            model_run_root = os.path.join(self.target_path, model_run_dt_str)
            previous_model_run_dt = model_run_dt - self.model_run_interval_tdelta

            previous_model_run_dt_str = previous_model_run_dt.strftime("%Y%m%d%H")
            previous_model_run_root = os.path.join(self.target_path, previous_model_run_dt_str)

            # Run Cosmo
            run_lsm_rapid_process(
                rapid_executable_location=self.rapid_executable_path,
                rapid_io_files_location=model_run_root,
                lsm_data_location=os.path.join(model_run_root, "data", model_run_dt_str),
                use_all_processors=False,  # defaults to use all processors available
                num_processors=1,  # you can change this number if use_all_processors=False
                generate_initialization_file=True,
                timedelta_between_simulations=datetime.timedelta(hours=12),
                initial_flows_file=os.path.join(previous_model_run_root, "qinit.csv") if i > 0 or init_first_run else None

            )
            print("*************************Done {}".format(model_run_dt))

        pass
        print("****************************All Done")
