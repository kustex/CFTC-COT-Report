import urllib.request, shutil
import math
import yaml
import os
import pandas as pd
import requests
import stat
import subprocess
import sqlite3
import time

from datetime import datetime
from dateutil.relativedelta import relativedelta
from zipfile import ZipFile

class CFTCDataAnalyzer:
    def __init__(self):
        self.num_of_entries = 0
        self.extract_zip_files = True
        self.metrics = self.load_metrics()

    def load_metrics(self):
        with open("metrics.yaml", 'r') as yf:
            return yaml.safe_load(yf)

    def get_asset_lists(self):
        options = []
        for asset_class in self.metrics:
            for metric in self.metrics[asset_class]:
                options.append(metric)
        return options

    @staticmethod
    def sort_on_time(val):
        return val[1]

    def get_list_of_i_and_date_for_metric(self, expected_row_names, date_list, name_list):
        the_list = []
        for expected_row_name in expected_row_names:
            for i in range(self.num_of_entries):
                row_name = name_list[i]
                if row_name == expected_row_name:
                    the_list.append((i, date_list[i]))
        the_list.sort(key=self.sort_on_time)
        return the_list

    @staticmethod
    def get_latest_i(list_of_i_and_date, end_date=datetime.now()):
        latest_i = list_of_i_and_date[-1][0]
        for i, date in reversed(list_of_i_and_date):
            if date < end_date:
                latest_i = i
                break
        return latest_i

    @staticmethod
    def get_second_latest_i(list_of_i_and_date, latest_i):
        previous_i = 0
        second_latest_i = 0
        for i, date in list_of_i_and_date:
            if i == latest_i:
                second_latest_i = previous_i
            else:
                previous_i = i
        return second_latest_i

    @staticmethod
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

    @staticmethod
    def calculate_x_year_avg(list_of_i_and_date, begin_date, values, end_date=datetime.now()):
        x_year_avg = 0
        entry_count = 0
        for i, date in list_of_i_and_date:
            if begin_date <= date <= end_date:
                x_year_avg += values[i]
                entry_count += 1
        if entry_count != 0:
            x_year_avg /= entry_count
        return x_year_avg

    @staticmethod
    def calculate_z_score(list_of_i_and_date, begin_date, values, end_date=datetime.now()):
        z_score = 0
        entry_count = 0
        latest_i = CFTCDataAnalyzer.get_latest_i(list_of_i_and_date, end_date)
        latest = values[latest_i]

        x_year_avg = CFTCDataAnalyzer.calculate_x_year_avg(list_of_i_and_date, begin_date, values, end_date)
        for i, date in list_of_i_and_date:
            if begin_date <= date <= end_date:
                z_score += pow((values[i] - x_year_avg), 2)
                entry_count += 1

        if entry_count != 0:
            z_score /= entry_count
            z_score = math.sqrt(z_score)
            if z_score != 0:
                z_score = (latest - x_year_avg) / z_score
        return z_score

    @staticmethod
    def get_list_of_z_scores(list_of_i_and_date, year_count, values):
        the_list = []
        for i in range(156):
            begin_date = datetime.now() - relativedelta(years=year_count, weeks=i)
            end_date = datetime.now() - relativedelta(weeks=i)
            the_list.append(CFTCDataAnalyzer.calculate_z_score(list_of_i_and_date, begin_date, values, end_date))
        return the_list

    @staticmethod
    def get_list_of_net_positioning(list_of_i_and_date, begin_date, values):
        the_list = []
        for i, date in list_of_i_and_date:
            if date > begin_date:
                current = values[i]
                the_list.append(current)
        return the_list

    @staticmethod
    def get_cot_zip_file(url, file_name):
        with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    @staticmethod
    def get_cot_zip(url, file_name):
        response = requests.get(url, stream=True)
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=512):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)

    def getLists(self):
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
        xls_data = 'xls_data'

        years = [2020, 2021, 2022, 2023, 2024]
        for year in years:
            data_file_name = f'{year}.xls'
            xl_path = os.path.join(working_dir, xls_data, data_file_name)

            # Load Excel file into pandas
            xl = pd.ExcelFile(xl_path)
            df = pd.read_excel(xl, usecols=[NAME, DATE, INTEREST, NON_COMM_LONG, NON_COMM_SHORT, COMM_LONG, COMM_SHORT])

            # Append data to respective lists
            name_list += list(df[NAME])
            date_list += list(df[DATE])
            interest_list += list(df[INTEREST])
            non_comm_long_list += list(df[NON_COMM_LONG])
            non_comm_short_list += list(df[NON_COMM_SHORT])
            comm_long_list += list(df[COMM_LONG])
            comm_short_list += list(df[COMM_SHORT])

        self.num_of_entries = len(name_list)  # Update num_of_entries
        return name_list, date_list, interest_list, non_comm_long_list, non_comm_short_list, comm_long_list, comm_short_list

    def get_values(self, list_of_i_and_date, list_long, three_years_ago, three_months_ago, six_months_ago, one_year_ago, list_short=None):
        latest_i = self.get_latest_i(list_of_i_and_date)
        second_latest_i = self.get_second_latest_i(list_of_i_and_date, latest_i)
        if list_short is not None:
            diff = [(a - b) for a, b in zip(list_long, list_short)]
        else:
            diff = list_long
        latest = diff[latest_i]
        second_latest = diff[second_latest_i]
        ww_change = latest - second_latest
        minimum, maximum = self.get_x_year_min_max(list_of_i_and_date, three_years_ago, diff)
        three_month_avg = self.calculate_x_year_avg(list_of_i_and_date, three_months_ago, diff)
        six_month_avg = self.calculate_x_year_avg(list_of_i_and_date, six_months_ago, diff)
        one_year_avg = self.calculate_x_year_avg(list_of_i_and_date, one_year_ago, diff)
        three_year_avg = self.calculate_x_year_avg(list_of_i_and_date, three_years_ago, diff)
        z_score_one_year = self.calculate_z_score(list_of_i_and_date, one_year_ago, diff)
        z_score_three_years = self.calculate_z_score(list_of_i_and_date, three_years_ago, diff)
        return (latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum,
                three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year,
                z_score_three_years)

    def get_cftc_dataframe(self, name_list, date_list, long_list, short_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago):
        num_of_entries = len(name_list)
        cftc_df = pd.DataFrame()
        
        for asset_class in self.metrics:
            for metric in self.metrics[asset_class]:
                list_of_i_and_date = self.get_list_of_i_and_date_for_metric(self.metrics[asset_class][metric], date_list, name_list)
                
                # Unpack the values as before
                latest_i, second_latest_i, latest, second_latest, ww_change, minimum, maximum, three_month_avg, six_month_avg, one_year_avg, three_year_avg, z_score_one_year, z_score_three_years = self.get_values(list_of_i_and_date, long_list, three_years_ago, three_months_ago, six_months_ago, one_year_ago, short_list)

                # Populate the DataFrame with the metrics
                cftc_df[metric] = [metric, latest, ww_change, three_month_avg, six_month_avg, one_year_avg, three_year_avg,
                                   maximum, minimum, z_score_one_year, z_score_three_years]

        cftc_df = cftc_df.T
        cftc_df.columns = ['metric', 'latest', 'w/w change', '3m ave', '6m ave', '1y ave', '3y ave', '3y max', '3y min', '1y zscore', '3y zscore']
        
        # Convert columns to float
        for column in cftc_df.iloc[:, 1:]:
            cftc_df[column] = cftc_df[column].astype(float)
        
        return cftc_df.round(2), cftc_df.index, num_of_entries

    def check_tables(self):
        conn = sqlite3.connect('cftc_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()

    def get_last_modified_date(self):
        conn = sqlite3.connect('cftc_data.db')  
        
        self.check_tables()

        cursor = conn.cursor()
        
        # Query to get the last modified date for this year
        current_year = datetime.now().year
        cursor.execute("SELECT last_modified FROM zip_files WHERE year = ?", (current_year,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return result[0]  # Assuming last_modified is the first column
        return None





