
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
from datetime import date
import re
import os
import glob


class getChronicle:

    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.base_url = ("https://mut-gegen-rechte-gewalt.de/"
                         "service/chronik-vorfaelle?&"
                         "&field_date_value[value][year]=")

    def read_page(self, page_nr, page_yr):

        url = f"{self.base_url}{page_yr}&page={page_nr}"
        try:
            html = urlopen(url).read().decode()
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            raise ValueError("Page does not exist")

        # get page data
        city_r = soup.find_all("div", attrs={"field-name-field-city"})
        state_r = soup.find_all("div", attrs={"field-name-field-bundesland"})
        date_r = soup.find_all("div", attrs={"field-name-field-date"})
        source_r = soup.find_all("div", attrs={"field-name-field-source"})
        cat_de_r = soup.find_all("div", attrs={"field-name-field-art"})
        des_r = soup.find_all("div", attrs="field-name-body")

        # if information is not of equal length, replace source
        if not (len(city_r) == len(state_r) == len(date_r)
                == len(source_r) == len(cat_de_r) == len(des_r)):
            print(f"Content on page {page_nr}-{page_yr} of unequal length")
            source_r = soup.find_all("div", attrs={"node-chronik-eintrag"})

            for i in range(len(source_r)):
                try:
                    source_r[i] = (source_r[i]
                                   .find("div",
                                         attrs={"field-name-field-source"}))
                except Exception:
                    source_r[i] = None

        # append to dataframe
        page_content = []

        for el in range(len(city_r)):
            page_content.append(
                {
                    "date": date_r[el].text,
                    "city": city_r[el].text,
                    "state": state_r[el].text,
                    "category_de": cat_de_r[el].text,
                    "description_de": des_r[el].text,
                    "source": source_r[el].text if hasattr(source_r[el],
                                                           'text') else '',
                    "page_nr": page_nr,
                    "year": page_yr
                }
            )

        df_page = pd.DataFrame(page_content)

        return df_page

    def read_year(self, year):

        year_current = date.today().year
        if year < 2017:
            raise ValueError("Data can only be retrieved from 2017 onwards.")
        if year > year_current:
            raise ValueError("Data cannot be retrieved from the future.")

        url_start = f"{self.base_url}{year}&page=0"
        print(url_start)
        html = urlopen(url_start).read().decode("utf-8")
        soup = BeautifulSoup(html, "html.parser")

        # get last page
        try:
            url_end = (soup
                       .find("li", attrs={"pager-last last"})
                       .find("a", href=True)["href"]
                       )
            last_page = [int(s) for s in re.findall(r"page=(\d*)", url_end)][0]
        except Exception:
            # last page does not exist
            last_page = 0

        # retrieve data for all pages
        print(f"Retrieving data for {year} from {last_page + 1} pages")

        df = pd.DataFrame()

        for page in range(0, last_page + 1):
            df_page = self.read_page(page, year)
            df = pd.concat([df, df_page])

        return df

    def read_all(self):

        df = pd.DataFrame()

        for year in range(self.start, self.end):
            df_year = self.read_year(year)
            df = pd.concat([df, df_year])

        return df

    def save_to_csv(self, file_path, start=None, end=None):

        if start is None:
            start = self.start
        if end is None:
            end = self.end

        print(start, end)

        for year in range(start, end+1):
            print(f"Checking whether attacks_{year} exists in "
                  f"'{file_path}'...")
            if os.path.isfile(f"{file_path}attacks_{year}.csv"):
                print(f"attacks_{year} already exists, moving to next year.")
            else:
                print(f"attacks_{year} does not exist. Downloading now...")

                # download and save
                attacks = self.read_year(year)
                attacks.to_csv(f"{file_path}attacks_{year}.csv", index=False)
        print(f"All files from {start} to {end} downloaded.")

    def load_all(self, file_path):

        # check if all files exist
        years_file = []
        for file in os.listdir(file_path):
            pattern = re.findall(r".*_(\d{4})", file)
            if len(pattern) == 0:
                continue
            years_file.append(int(pattern[0]))

        years_missing = [x for x in range(self.start, self.end + 1)
                         if x not in years_file]
        years_missing = sorted(years_missing)

        # if all files don't exist, ask if files should be downloaded
        while len(years_missing) != 0:
            year_left = years_missing[0]
            check = input(f"{year_left} is missing. "
                          "Should data be downloaded now? [Y/N]")
            if check in ["Yes", "YES", "yes", "Y", "y"]:
                print("Beginning download.")
                self.save_to_csv(file_path, year_left, year_left)
                years_missing.remove(year_left)
            else:
                raise ValueError(
                    f"All files need to be downloaded."
                    f"Download {sorted(years_missing)} before concatenating.")

        else:
            # append all files
            print("All files downloaded. Concatenating files.")
            all_files = glob.glob(os.path.join(file_path, "*20[0-9][0-9].csv"))
            all_files = sorted(all_files)
            df = pd.concat((pd.read_csv(f) for f in all_files),
                           ignore_index=True)
            return df
