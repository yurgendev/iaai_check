from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os
import shutil
from dotenv import load_dotenv
import pandas as pd

load_dotenv('.env')

s = Service(executable_path="/Users/yurgenoa/Documents/iaai cheker/chromedriver/chromedriver")
driver = webdriver.Chrome(service=s)

username_483 = os.getenv('USERNAME_483')
password_483 = os.getenv('PASSWORD_483')

username_581 = os.getenv('USERNAME_581')
password_581 = os.getenv('PASSWORD_581')

login_url = 'https://login.iaai.com/'
purchase_history_url = 'https://www.iaai.com/purchasehistory'
new_filename_483 = '483_new.csv'
new_filename_581 = '581_new.csv'

target_directory_483 = '/Users/yurgenoa/Documents/iaai cheker/483/'
target_directory_581 = '/Users/yurgenoa/Documents/iaai cheker/581/'


def download_file(username, password, target_directory):
    """
        Downloads a file from an internet resource using the provided user credentials.

        This function logs in to the specified website using the given username and password.
        It locates specific elements on the page and performs actions to initiate the file download.
        The downloaded file is then moved to the specified target directory.

        :param username: The username used for logging in to the website.
        :type username: str
        :param password: The password used for logging in to the website.
        :type password: str
        :param target_directory: The path to the target directory where the downloaded file will be saved.
        :type target_directory: str
        :return: None
        :raises ValueError: If the provided username does not match any of the predefined values.
        """
    try:

        driver.get(login_url)
        if username == username_483:
            time.sleep(20)
        if username == username_581:
            time.sleep(2)

        username_field = driver.find_element(By.ID, 'Email')
        password_field = driver.find_element(By.ID, 'Password')

        username_field.send_keys(username)
        password_field.send_keys(password)

        password_field.send_keys(Keys.ENTER)

        driver.get(purchase_history_url)

        # close popup
        if username == username_483:
            driver.find_element(By.ID, 'onetrust-close-btn-container').click()

        select_element = driver.find_element(By.ID, 'drpAuction')

        select_element.find_element(By.XPATH, '//option[@data-filtername="ThisMonth"]').click()

        download_button = driver.find_element(By.ID, 'btnExport')

        download_button.click()

        time.sleep(5)

        download_directory = '/Users/yurgenoa/Downloads'

        files = os.listdir(download_directory)

        # newest file in directory
        newest_file = max(files, key=lambda f: os.path.getctime(os.path.join(download_directory, f)))
        downloaded_file_path = os.path.join(download_directory, newest_file)

        # rename and moving file
        if username == username_483:
            new_file_path = os.path.join(download_directory, new_filename_483)
            os.rename(downloaded_file_path, new_file_path)

            target_file_path = os.path.join(target_directory, new_filename_483)
            shutil.move(new_file_path, target_file_path)

            driver.get('https://www.iaai.com/login/gbplogout')
            return None

        elif username == username_581:
            new_file_path = os.path.join(download_directory, new_filename_581)
            os.rename(downloaded_file_path, new_file_path)

            target_file_path = os.path.join(target_directory, new_filename_581)
            shutil.move(new_file_path, target_file_path)
        else:
            raise ValueError("Invalid username")

    except Exception as err:
        print(f"An error occurred: {err}")

    return None


def process_table_483():
    """
    Process data for table 483.

    Reads two CSV files (old and new) for table 483, compares them to find new VINs (paid cars) and
    updates for pick-up cars (difference between old and new tables). Prints the results and renames
    the new file as the old file.

    :return: None
    """
    path_483_old = '483/483_old.csv'
    path_483_new = '483/483_new.csv'

    df1 = pd.read_csv(path_483_old, sep=',', na_values='', usecols=['VIN', 'Date Paid', 'Date Picked Up'])
    df2 = pd.read_csv(path_483_new, sep=',', na_values='', usecols=['VIN', 'Date Paid', 'Date Picked Up'])

    result_483 = iaai_cheker(df1, df2)

    print('483 checking...\n', result_483, '\n', 50 * '*')

    # Remove old file
    os.remove(path_483_old)

    # Rename new file
    os.rename(path_483_new, path_483_new.replace('483_new.csv', '483_old.csv'))


def process_table_581():
    """
    Process data for table 581.

    Reads two CSV files (old and new) for table 581, compares them to find new VINs (paid cars) and
    updates for pick-up cars (difference between old and new tables). Prints the results and renames
    the new file as the old file.

    :return: None
    """
    path_581_old = '581/581_old.csv'
    path_581_new = '581/581_new.csv'

    df1 = pd.read_csv(path_581_old, sep=',', na_values='', usecols=['VIN', 'Date Paid', 'Date Picked Up'])
    df2 = pd.read_csv(path_581_new, sep=',', na_values='', usecols=['VIN', 'Date Paid', 'Date Picked Up'])

    result_581 = iaai_cheker(df1, df2)

    print('581 checking...\n', result_581)

    # Remove old file
    os.remove(path_581_old)

    # Rename new file
    os.rename(path_581_new, path_581_new.replace('581_new.csv', '581_old.csv'))


def iaai_cheker(df1, df2):
    """
    Combine and process data from two data frames.

    Takes two data frames (old and new) and merges them to find new VINs (paid cars) and updates for
    pick-up cars. The function prints the results and returns the merged data frame.

    :param df1: The data frame containing old table data.
    :type df1: pandas.DataFrame
    :param df2: The data frame containing new table data (just downloaded with updates).
    :type df2: pandas.DataFrame
    :return: The merged data frame with processed data.
    :rtype: pandas.DataFrame
    """

    # Merge DataFrame filling in missing values from df1
    merged_df = df2.combine_first(df1)
    merged_df = merged_df.fillna('').astype(str)
    # UPDATE for PickUp
    merged_df = merged_df.mask(df2.notnull() & df1.isnull(), 'UPDATED->' + merged_df)
    # new VIN-paid
    merged_df['VIN'] = merged_df.apply(
        lambda row: 'NEW->' + row['VIN'] if row['VIN'] not in df1['VIN'].values else row['VIN'], axis=1)

    # set max lines
    pd.set_option('display.max_rows', None)

    return merged_df


if __name__ == "__main__":
    try:
        download_file(username_483, password_483, target_directory_483)
        download_file(username_581, password_581, target_directory_581)

        process_table_483()
        process_table_581()
        print('\n', time.strftime("%H:%M:%S"))
    finally:
        driver.quit()
