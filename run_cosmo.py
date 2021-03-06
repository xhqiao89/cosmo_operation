import datetime

from cosmo_helper import OperationHelperForCOSMO

lsm_source_path = "/mnt_lsm"
input_folder_path = "/mnt_cosmo_project/template"
workspace_path = "/mnt_cosmo_project/run"


if __name__ == "__main__":

    cosmo_helper = OperationHelperForCOSMO(lsm_source_path, input_folder_path, workspace_path, lsm_symlink=True)

    # current_utc_dt_str = sys.argv[1]
    # print (current_utc_dt_str)
    # current_utc_dt = datetime.datetime.strptime(current_utc_dt_str, "%Y%m%d%H%M")
    end_utc_dt = None

    #start_utc_dt = datetime.datetime.utcnow()
    #end_utc_dt = None


    #dates with missing files:
    #2018082600
    #2018082612
    #2018090912
    #2018091012  -- 2018092112


    start_utc_dt = datetime.datetime(year=2018, month=9, day=22, hour=0)
    end_utc_dt = datetime.datetime(year=2018, month=10, day=1, hour=12)


    cosmo_helper.start_run(start_utc_dt, end_utc_dt, init_first_run=True)
    pass

