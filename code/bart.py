#!/usr/bin/env python
# coding: utf-8

# # Library def

# In[ ]:


import collections
import os
import re
import requests

from datetime import date, datetime, timedelta
from IPython.display import clear_output
from time import time as timer

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.support import wait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


# In[ ]:


# Throughout, "att" is short for "archiveTimes table", which contains archive 
# entry info for the date selected in the calendar


# In[ ]:


# Constants
_FEED_URL_STEM = 'https://www.broadcastify.com/listen/feed/'
ARCHIVE_FEED_STEM = 'https://m.broadcastify.com/archives/feed/'
ARCHIVE_DOWNLOAD_STEM = 'https://m.broadcastify.com/archives/id/'
LOGIN_URL = 'https://www.broadcastify.com/login/'
FIRST_URI_IN_ATT_XPATH = "//a[contains(@href,'/archives/download/')]"

MONTHS = ['','January', 'February', 'March',
      'April', 'May', 'June',
      'July', 'August', 'September',
      'October', 'November', 'December']

# Library-level variables
ArchiveEntry = collections.namedtuple('ArchiveEntry',
                                     'feed_id file_uri file_end_datetime mp3_url')
"""
    feed_id : str
        Unique ID for the Broadcastify feed. Taken from https://www.broadcastify
        .com/listen/feed/[feed_id]
    file_uri : str
        The unique ID for an individual archive file page, which corresponds to 
        a feed's transmissions over a ~30-minute period on a given date. Can be 
        used to find the mp3 file's individual download page
    file_end_date_time : str
        Date and end time of the individual archive file
    mp3_url : str
        The URL of the corresponding mp3 file
    """;

FILE_REQUEST_WAIT = 5 # seconds
PAGE_REQUEST_WAIT = 2 # seconds
# WEBDRIVER_PATH = '../assets/chromedriver' # for Chrome
WEBDRIVER_PATH = '../assets/phantomjs-2.1.1-macosx' # for Phantom JS
MP3_OUT_PATH = '../audio_data/audio_files/mp3_files/'


# In[ ]:


class RequestThrottle:
    def __init__(self):
        self.last_file_req = timer()
        self.last_page_req = timer()
        
    def throttle(self, type='page'):
        if type == 'page':
            while not timer() - self.last_page_req >= PAGE_REQUEST_WAIT:
                pass
            self.last_page_req = timer()
        else:
            while not timer() - self.last_file_req >= FILE_REQUEST_WAIT:
                pass
            self.last_file_req = timer()        


# In[ ]:


class NoActiveBrowser(Exception):
    pass


# In[ ]:


class BroadcastifyArchive:
    def __init__(self, feed_id, username=None, password=None, verbose=1):
        self.feed_id = feed_id
        self.feed_url = _FEED_URL_STEM + feed_id
        self.archive_url = ARCHIVE_FEED_STEM + feed_id
        self.username = username
        self.password = password
        self.entries = sample_archive_entries #[] # list of ArchiveEntry objects
        self.earliest_date = None 
        self.latest_date = None
        
        self._an = None
        self._verbose = verbose
        
    @property
    def feed_id(self):
        """
        Unique ID for the Broadcastify feed. Taken from 
        https://www.broadcastify.com/listen/feed/[feed_id]
        """
        return self._feed_id
    @feed_id.setter
    def feed_id(self, value):
        self._feed_id = value
        self.entries = []
        self.earliest_date = None
        self.latest_date = None
        self.feed_url = _FEED_URL_STEM + value
        self.archive_url = ARCHIVE_FEED_STEM + value
        self._an = None

    @property
    def password(self):
        """
        Password for Broadcastify premium account. Getting the property
        will return a Boolean indicating whether the password has been set.
        """
        if self._password:
            return True
        else:
            return False
    @password.setter
    def password(self, value):
        self._password = value

    def build(self, days_back=0, rebuild=False): # 0 days back means the active day
        
        if self.entries and not rebuild:
            raise ValueError(f'Entries already exist for this BroadcastifyArchive. '
                             f'To rebuild, specify rebuild=True when calling .build()')
        
        all_att_entries = []
        counter = 1
        
        # Make sure days_back is an integer and non-negative
        try:
            days_back = int(days_back)
            if days_back < 0: days_back = 0
            days_back += 1
        except (TypeError):
            raise TypeError("The `days_back` parameter needs an integer between 0 and 180.")
        
        if self._verbose: print('Starting the ArchiveNavigator...')

        # Instantiate the ArchiveNavigator
        self.an = ArchiveNavigator(self.archive_url, self._verbose)
        
        # Add the current (zero-th) day's archiveTimes table (ATT) entries 
        # (file_uri & file_end_date_time)
        if self._verbose: print(f'Parsing day {counter} of {days_back}: {self.an.active_date}')
        all_att_entries = self.__parse_att(self.an.att_soup)
        self.latest_date = all_att_entries[0][1]
        self.earliest_date = all_att_entries[-1][1]

        # For each day requested...
        for day in range(1, days_back):
            # If clicking the prior day takes us past the beginning of the archive,
            # stop.
            if not self.an.click_prior_day(): break
            
            counter += 1
            if self._verbose: print(f'Parsing day {counter} of {days_back}: {self.an.active_date}')
            
            # Get the archiveTimes table entries (file_uri & file_end_date_time)
            all_att_entries.extend(self.__parse_att(self.an.att_soup))
            self.earliest_date = all_att_entries[-1][1]
            
        self.an.close_browser()
        
        # Iterate through att entries to
        ##  - Get the mp3 URL
        ##  - Build an ArchiveEntry, and append to the list
        ## Instantiate the DownloadNavigator
        dn = DownloadNavigator(login=True, _verbose=self._verbose)
        counter = 0
        
        ## Loop & build ArchiveEntry list
        for uri, end_time in all_att_entries:
            counter += 1
            if self._verbose: print(f'Building ArchiveEntry list: {counter} of {len(all_att_entries)}')
            clear_output(wait=True)
            self.entries.append(ArchiveEntry(self.feed_id,
                                             uri,
                                             end_time,
                                             self.__parse_mp3_path(
                                             dn.get_download_soup(uri))))

        if self._verbose:
            print(f'Archive build complete.')
            print(self)
            
    def download(self, start=None, end=None, filepath=MP3_OUT_PATH):
        entries = self.entries
        entries_to_pass = []
        dn = DownloadNavigator(login=False)
        
        if not start: start = datetime(1,1,1,0,0)
        if not end: end = datetime(9999,12,31,0,0)

        # Remove out-of-date-range entries from self.entries
        entries_to_pass = [entry for entry in entries if 
                           entry.file_end_datetime >= start and
                           entry.file_end_datetime <= end]
        
        # Pass them as a list to a DownloadNavigator.get_archive_mp3s
        dn.get_archive_mp3s(entries_to_pass, filepath)
    
    def __parse_att(self, att_soup):
        """
        Generates Broadcastify archive file information from the `archiveTimes`
        table ("ATT") on a feed's archive page. Returns a list of lists
        containing two elements:
            - The URI for the file, which can be used to find the file's
              individual download page
            - Date and end time of the transmission as a datetime object

        Parameters
        ----------
        att_soup : bs4.BeautifulSoup
            A BeautifulSoup object containing the ATT source code, obtained
            from ArchiveNavigator.att_soup


        """
        
        # Set up a blank list to return
        att_entries = []

        # Loop through all rows of the table
        for row in att_soup.find_all('tr'):    
            # Grab the end time, contained in the row's second <td> tag
            file_end_datetime = self.__get_entry_end_datetime(row.find_all('td')[1].text)
            
            # Grab the file ID
            file_uri = row.find('a')['href'].split('/')[-1]

            # Put the file date/time and URL leaf (as a list) into the list
            att_entries.append([file_uri, file_end_datetime])
        
        return att_entries
    
    def __get_entry_end_datetime(self, time):
        """Convert the archive entry end time to datetime"""
        clock = datetime.strptime(time, '%I:%M %p')
        return datetime.combine(self.an.active_date, datetime.time(clock))
        
    def __parse_mp3_path(self, download_page_soup):
        """Parse the mp3 filepath from a BeautifulSoup of the download page"""
        return download_page_soup.find('a', {'href': re.compile('.mp3')}).attrs['href']

    def __repr__(self):
        return(f'BroadcastifyArchive\n'
               f' ('
               f'{len(self.entries)} ArchiveEntries\n'
               f'  start date: {str(self.earliest_date)}\n'
               f'  end date:   {str(self.latest_date)}\n'
               f'  feed_id = {self.feed_id}\n'
               f'  username = "{self.username}", pwd = [{self.password}]\n'
               f'  feed_url = "{self.feed_url}"\n'
               f'  archive_url = "{self.archive_url}"\n'
               f'  verbose = {self._verbose}'
               f')')


# In[ ]:


class ArchiveNavigator:
    def __init__(self, url, verbose):
        self.url = url
        self.calendar_soup = None
        self.att_soup = None
        self.browser = None
        self.verbose = verbose

        self.active_date = None # currently displayed date
        self.month_max_date = None # latest day in displayed month with archive entries
        self.month_min_date = None # earliest day in displayed month with archive entries
        
        self.current_first_uri = None
       
        # Get initial page scrape & parse the calendar
        self.open_browser()
        self.__load_nav_page()
        self.__scrape_nav_page()
        self.__parse_calendar()
        
        self.archive_max_date = self.active_date
        
        # https://www.saltycrane.com/blog/2010/10/how-get-date-n-days-ago-python/
        self.archive_min_date = self.archive_max_date - timedelta(days=181)
        
    def click_prior_day(self):
        # calculate the prior day
        prior_day = self.active_date - timedelta(days=1)
        
        # would this take us past the archive? if so, stop.
        if prior_day < self.archive_min_date:
            return False
        
        # is the prior day in the previous month? set the xpath class appropriately
        if prior_day < self.month_min_date:
            xpath_class = 'old day'
        else:
            xpath_class = 'day'

        xpath_day = prior_day.day
        
        self.__check_browser()
        
        # click the day before the currently displayed day
        calendar_day = self.browser.find_element_by_xpath(
                        f"//td[@class='{xpath_class}' "
                        f"and contains(text(), '{xpath_day}')]")
            # https://stackoverflow.com/questions/2009268/how-to-write-an-xpath-query-to-match-two-attributes
        calendar_day.click()

        # refresh soup & re-parse calendar
        self.__scrape_nav_page()
        self.__parse_calendar()
        
        return self.active_date
    
    def __load_nav_page(self):
        if self.verbose: print('Loading navigation page...')
        self.__check_browser()

        # Browse to feed archive page
        self.browser.get(self.url)
        
        # Wait for page to render
        element = WebDriverWait(self.browser, 10).until(
                  EC.presence_of_element_located((By.CLASS_NAME, 
                                                  "cursor-link")))
        
        # Get current_first_uri, if none populated
        if not self.current_first_uri:
            self.current_first_uri = self.__get_current_first_uri()
    
    def __scrape_nav_page(self):
        if self.verbose: print('Scraping navigation page...')
        self.__check_browser()

        # Wait for page to render
        element = WebDriverWait(self.browser, 10).until_not(
                    EC.text_to_be_present_in_element((By.XPATH, FIRST_URI_IN_ATT_XPATH), 
                                                      self.current_first_uri))

        self.current_first_uri = self.__get_current_first_uri()
        
        # Scrape page content
        soup = BeautifulSoup(self.browser.page_source, 'lxml')

        # Isolate the calendar and the archiveTimes table
        self.calendar_soup = soup.find('table', 
                                       {'class': 'table-condensed'})
        self.att_soup = soup.find('table', 
                                  attrs={'id': 'archiveTimes'}
                                  ).find('tbody')
        
    def __parse_calendar(self):
        """
        Uses a bs4 ResultSet of the <td> tags representing days currently displayed
        on the calendar to set calendarattributes. Items have the format of 
        `<td class="[class]">[D]</td>` where 
         - [D] is the one- or two-digit day (as a string) and
         - [class] is one of
             "old day"          = a day with archives but in a prior month (clicking
                                  will refresh the calendar)
             "day"              = a past day in the current month
             "active day"       = the day currently displayed in the archiveTimes 
                                  table
             "disabled day"     = a day for which no archive is available in a month
                                  (past or future) that has other days with archives. 
                                  For example, if today is July 27, July 28-31 will 
                                  be disabled days, as will January 1-26 (since the 
                                  archive goes back only 180 days). December 31 would
                                  be an "old disabled day".
                                  past month for which archives are no longer available
             "new disabled day" = a day in a future month
             "old disabled day" = see explanation in "disabled day"
         
        """
        if self.verbose: print('Parsing calendar...')
        
        # Get the tags representing the days currently displayed on the calendar
        days_on_calendar = self.calendar_soup.find_all('td')
        
        # Get the month & year currently displayed
        month, year = self.calendar_soup.find('th', 
                                              {'class': 'datepicker-switch'}
                                              ).text.split(' ')
        
        displayed_month = MONTHS.index(month)
        displayed_year = int(year)
        
        # Parse the various calendar attributes
        active_day = int([day.text for day in days_on_calendar
                           if (day['class'][0] == 'active')][0])
        
        month_max_day = int([day.text for day in days_on_calendar
                              if (day['class'][0] == 'day') or
                                 (day['class'][0] == 'active')][::-1][0])
        
        month_min_day = int(self.__parse_month_min_day(days_on_calendar))
        
        # Set class attributes
        self.active_date = date(displayed_year, displayed_month, active_day)        
        self.month_min_date = date(displayed_year, displayed_month, month_min_day)
        self.month_max_date = date(displayed_year, displayed_month, month_max_day)
        
    def __parse_month_min_day(self, days_on_calendar):
        """Parse the lowest valid day in the displayed month"""
        disabled_found = False
        for day in days_on_calendar:
            if day['class'][0] == 'disabled':
                disabled_found = True
            elif day['class'][0] in 'day active'.split():
                return day.text
            elif day['class'][0] != 'old' and disabled_found:
                return day.text
        
        return None

    def __get_current_first_uri(self):
        return self.browser.find_element_by_xpath(
                    FIRST_URI_IN_ATT_XPATH
                    ).get_attribute('href').split('/')[-1]
        
    def open_browser(self):
        if self.verbose: print('Opening browser...')
        self.browser = webdriver.Chrome(WEBDRIVER_PATH)

    def close_browser(self):
        if self.verbose: print('Closing browser...')
        self.browser.quit()

    def __check_browser(self):
        if not self.browser:
            raise NoActiveBrowser("Please open a browser. And remember to close it when you're done.")
            
    def __repr__(self):
        return(f'ArchiveNavigator(URL: {self.url}, '
               f'Currently Displayed: {str(self.active_date)}, '
               f'Max Day: {str(self.archive_max_date)}, '
               f'Min Day: {str(self.archive_min_date)}, ')


# In[ ]:


class DownloadNavigator():
    def __init__(self, login=False, verbose=False):
        self.download_page_soup = None
        self.current_archive_id = None
        self.verbose = verbose
        self.throttle = t = RequestThrottle()
        self.session = s = requests.Session()
        self.login = l = login
        
        # Set post parameters
        login_data = {
            'username': USERNAME,
            'password': PASSWORD,
            'action': 'auth',
            'redirect': '/'
        }

        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) ' +
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/' +
                          '75.0.3770.142 Safari/537.36'
        }
        
        if l:
            t.throttle()
            r = s.post(LOGIN_URL, data=login_data, headers=headers)

            if r.status_code != 200:
                raise ConnectionError(f'Problem connecting: {r.status_code}')
        
    def get_download_soup(self, archive_id):
        self.current_archive_id = archive_id
        s = self.session
        t = self.throttle
        
        t.throttle()
        r = s.get('https://m.broadcastify.com/archives/id/' + archive_id)
        if r.status_code != 200:
            raise ConnectionError(f'Problem connecting: {r.status_code}')
                                  
        self.download_page_soup = BeautifulSoup(r.text, 'lxml')       

        return self.download_page_soup        

    def get_archive_mp3s(self, archive_entries, filepath):
        start = timer()
   
        for file in archive_entries:
            feed_id =  file.feed_id
            archive_uri = file.file_uri
            file_date = self.__format_entry_date(file.file_end_datetime)
            file_url = file.mp3_url
   
            # Build the path for saving the downloaded .mp3
            out_file_name = filepath + '-'.join([feed_id, file_date]) + '.mp3'

            print(f'Downloading {archive_entries.index(file) + 1} of {len(archive_entries)}')
            if self.verbose:
                print(f'\tfrom {file_url}')
                print(f'\tto {out_file_name}')
            clear_output(wait=True)

            self.throttle.throttle('file')
            self.__fetch_mp3([out_file_name, file_url])

        duration = timer() - start

        print('Downloads complete.')
        if self.verbose:
            print(f'Retrieved {len(out_file_name)} files in {duration} seconds.')
    
    def __fetch_mp3(self, entry):
        # h/t https://markhneedham.com/blog/2018/07/15/python-parallel-download-files-requests/
        path, uri = entry

        if not os.path.exists(path):
            r = requests.get(uri, stream=True)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r:
                        f.write(chunk)
        return path

    def __format_entry_date(self, date):
        # Format the ArchiveEntry end time as YYYYMMDD-HHMM
        year = date.year
        month = date.month
        day = date.day
        hour = date.hour
        minute = date.minute
        
        return '-'.join([str(year) + str(month).zfill(2) + str(day).zfill(2), 
                         str(hour).zfill(2) + str(minute).zfill(2)])
    
    def __repr__(self):
        return(f'DownloadNavigator(Current Archive: {self.current_archive_id})')

