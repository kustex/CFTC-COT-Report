import urllib.request, shutil
import math
import yaml
import os
import pandas as pd
import requests
import subprocess
import time

from datetime import datetime
from dateutil.relativedelta import relativedelta
from zipfile import ZipFile


num_of_entries = 0
extract_zip_files = True

def get_asset_lists():
    """
	Get list of assets you want to analyze
    """
    with open("metrics.yaml", 'r') as yf:
        metrics = yaml.safe_load(yf)
    options = []
    for asset_class in metrics:
        for metric in metrics[asset_class]:
            options.append(metric)
    return options

def sortOnTime(val):
    return val[1]

def get_list_of_i_and_date_for_metric(expected_row_names, num_of_entries, date_list, name_list):
    the_list = []
    for expected_row_name in expected_row_names:
        for i in range(0, num_of_entries):
            row_name = name_list[i]
            if row_name == expected_row_name:
                the_list.append((i, date_list[i]))
    the_list.sort(key=sortOnTime)
    return the_list

def get_latest_i(list_of_i_and_date, end_date=datetime.now()):
    latest_i = list_of_i_and_date[-1][0]
    for i, date in reversed(list_of_i_and_date):
        if date < end_date:
            latest_i = i
            break
    return latest_i

def get_second_latest_i(list_of_i_and_date, latest_i):
    previous_i = 0
    second_latest_i = 0
    for i, date in list_of_i_and_date:
        if i == latest_i:
            second_latest_i = previous_i
        else:
            previous_i = i
    return second_latest_i

def get_x_year_min_max(list_of_i_and_date, begin_date, values):
    minimum = float('inf')
    maximum = float('-inf')
    for i, date in list_of_i_and_date:
        if date > begin_date:
            current = values[i]
            if current < minimum:
                minimum = current
            if current > maximum:
                maximum = current
    return minimum, maximum

def calculate_x_year_avg(list_of_i_and_date, begin_date, values, end_date=datetime.now()):
    x_year_avg = 0
    entry_count = 0
    for i, date in list_of_i_and_date:
        if date >= begin_date and date <= end_date:
            x_year_avg += values[i]
            entry_count += 1
    if entry_count != 0:
        x_year_avg /= entry_count
    return x_year_avg

def calculate_z_score(list_of_i_and_date, begin_date, values, end_date=datetime.now()):
    z_score = 0
    entry_count = 0
    latest_i = get_latest_i(list_of_i_and_date, end_date)
    latest = values[latest_i]

    x_year_avg = calculate_x_year_avg(list_of_i_and_date, begin_date, values, end_date)
    for i, date in list_of_i_and_date:
        if date >= begin_date and date <= end_date:
            z_score += pow((values[i] - x_year_avg), 2)
            entry_count += 1

    if entry_count != 0:
        z_score /= entry_count
        z_score = math.sqrt(z_score)
        if z_score != 0:
            z_score = (latest - x_year_avg) / z_score
    return z_score

def get_list_of_z_scores(list_of_i_and_date, year_count, values):
    the_list = []
    for i in range(0, 156):
        begin_date = datetime.now() - relativedelta(years=year_count, weeks=i)
        end_date = datetime.now() - relativedelta(weeks=i)
        the_list.append(calculate_z_score(list_of_i_and_date, begin_date, values, end_date))
    return the_list

def get_list_of_net_positioning(list_of_i_and_date, begin_date, values):
    the_list = []
    for i, date in list_of_i_and_date:
        if date > begin_date:
            current = values[i]
            the_list.append(current)
    return the_list

def get_cot_zip_file(url, file_name):
    with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

def get_cot_zip(url, file_name):
    response = requests.get(url, stream=True)
    with open(file_name, "wb") as f:
        for chunk in response.iter_content(chunk_size=512):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

def getLists():
    NAME = "Market_and_Exchange_Names"
    DATE = "Report_Date_as_MM_DD_YYYY"
    INTEREST = "Open_Interest_All"
    NON_COMM_LONG = "NonComm_Positions_Long_All"
    NON_COMM_SHORT = "NonComm_Positions_Short_All"
    COMM_LONG = "Comm_Positions_Long_All"
    COMM_SHORT = "Comm_Positions_Short_All"

    name_list = []
    date_list = []
    interest_list = []
    non_comm_long_list = []
    non_comm_short_list = []
    comm_long_list = []
    comm_short_list = []

    working_dir = os.getcwd()
    DATA_DIR = "cftc_data"
    tmp = 'tmp'
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(tmp):
        os.makedirs(tmp)

    # years = [2021, 2022, 2023, 2024]
    # for y in years:
    #     if not f"{y}.xls" in os.listdir(f"{working_dir}/tmp/"):
    #         file = f'{DATA_DIR}/{y}.zip'
    #         zip_file = get_cot_zip(f'https://www.cftc.gov/files/dea/history/dea_com_xls_{y}.zip', file)
    #         with ZipFile(zip_file, 'r') as f:
    #             listOfFileNames = f.namelist()
    #             filename = listOfFileNames[0]
    #             file_path = f"{working_dir}/tmp/{filename}"
    #             try:
    #                 subprocess.run(["sudo", "chmod", "777", file_path], check=True)
    #                 print(f"Changed permissions for {file_path}")
    #             except subprocess.CalledProcessError as e:
    #                 print(f"Failed to change permissions: {e}")

    #             f.extractall(f"{working_dir}/tmp/")
    #             os.replace(f"{working_dir}/tmp/{listOfFileNames[0]}", f"{working_dir}/tmp/{listOfFileNames[0]}.xls")

    #     else:
    #         print(y)
    #         xl = pd.ExcelFile(f"{working_dir}/tmp/{y}.xls")
    #         df = pd.read_excel(xl, usecols=[NAME, DATE, INTEREST, NON_COMM_LONG, NON_COMM_SHORT, COMM_LONG, COMM_SHORT])
    #         name_list += list(df[NAME])
    #         date_list += list(df[DATE])
    #         interest_list += list(df[INTEREST])
    #         non_comm_long_list += list(df[NON_COMM_LONG])
    #         non_comm_short_list += list(df[NON_COMM_SHORT])
    #         comm_long_list += list(df[COMM_LONG])
    #         comm_short_list += list(df[COMM_SHORT])

    # return name_list, date_list, interest_list, non_comm_long_list, non_comm_short_list, comm_long_list, comm_short_list


    years = [2020, 2021, 2022, 2023, 2024]
    for year in years:
        if not f'{year}.zip' in os.listdir(DATA_DIR):
            print(f'{year}.zip')
            file = f'{DATA_DIR}/{year}.zip'
            get_cot_zip(f'https://www.cftc.gov/files/dea/history/dea_com_xls_{year}.zip', file)

    data_files = os.listdir(DATA_DIR)

    for data_file in data_files:
        if '.zip' in data_file:
            data_file_name = data_file[:-4]
            if extract_zip_files:
                with ZipFile(f"{DATA_DIR}/{data_file}", 'r') as f:
                    f.extractall(f"{working_dir}/tmp/")
                    listOfFileNames = f.namelist()
                    fileName = listOfFileNames[0]
                    print(fileName)
                    os.rename(f"{working_dir}/tmp/{fileName}", f"{working_dir}/tmp/{data_file_name}.xls")

            xl = pd.ExcelFile(f"{working_dir}/tmp/{data_file_name}.xls")
            df = pd.read_excel(xl, usecols=[NAME, DATE, INTEREST, NON_COMM_LONG, NON_COMM_SHORT, COMM_LONG, COMM_SHORT])
            name_list += list(df[NAME])
            date_list += list(df[DATE])
            interest_list += list(df[INTEREST])
            non_comm_long_list += list(df[NON_COMM_LONG])
            non_comm_short_list += list(df[NON_COMM_SHORT])
            comm_long_list += list(df[COMM_LONG])
            comm_short_list += list(df[COMM_SHORT])
    return name_list, date_list, interest_list, non_comm_long_list, non_comm_short_list, comm_long_list, comm_short_list

def get_values(list_of_i_and_date, list_long, three_years_ago, three_months_ago, six_months_ago, one_year_ago, list_short=None):
    latest_i = get_latest_i(list_of_i_and_date)
    second_latest_i = get_second_latest_i(list_of_i_and_date, latest_i)
    if list_short is not None:
        diff = [(a-b) for a,b in zip(list_long,list_short)]
    else:
        diff = list_long
    latest = diff[latest_i]
    second_latest = diff[second_latest_i]
    ww_change = latest - second_latest
    minimum, maximum = get_x_year_min_max(list_of_i_and_date, three_years_ago, diff)
    three_month_avg = calculate_x_year_avg(list_of_i_and_date, three_months_ago, diff)
    six_month_avg = calculate_x_year_avg(list_of_i_and_date, six_months_ago, diff)
    one_year_avg = calculate_x_year_avg(list_of_i_and_date, one_year_ago, diff)
    three_year_avg = calculate_x_year_avg(list_of_i_and_date, three_years_ago, diff)
    z_score_one_year = calculate_z_score(list_of_i_and_date, one_year_ago, diff)
    z_score_three_years = calculate_z_score(list_of_i_and_date, three_years_ago, diff)
    return latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, \
           z_score_three_years

def get_CFTC_Dataframe(name_list, date_list, long_list, short_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago):
    num_of_entries = len(name_list)
    with open("metrics.yaml", 'r') as yf:
        metrics = yaml.safe_load(yf)
    cftc_df = pd.DataFrame()
    for asset_class in metrics:
        for metric in metrics[asset_class]:
            list_of_i_and_date = get_list_of_i_and_date_for_metric(metrics[asset_class][metric], num_of_entries, date_list, name_list)
            latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, \
            z_score_three_years = get_values(list_of_i_and_date, long_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago, short_list)

            cftc_df[metric] = [metric, latest, ww_change, three_month_avg, six_month_avg, one_year_avg, three_year_avg,
                               maximum, minimum, z_score_one_year, z_score_three_years]
    cftc_df = cftc_df.T
    cftc_df.columns = ['metric', 'latest', 'w/w change', '3m ave', '6m ave', '1y ave','3y ave', '3y max', '3y min', '1y zscore', '3y zscore']
    for column in cftc_df.iloc[:, 1:]:
        cftc_df[column] = cftc_df[column].astype(float)
    return cftc_df.round(2), cftc_df.index, num_of_entries







