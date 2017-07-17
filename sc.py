import config
from scrapex import *
from scrapex import common
from scrapex.node import Node
from scrapex.excellib import *
from scrapex.http import Proxy
from proxy_list import random_proxy
import common_lib
import os
import argparse
import csv, random
import json
from time import sleep
from datetime import datetime
import sys  
from agent import random_agent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common import exceptions as EX
from selenium.common.exceptions import *
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

reload(sys)  
sys.setdefaultencoding('utf8')

lock = threading.Lock()

global_s = Scraper(
    use_cache=False, #enable cache globally
    retries=2,
    timeout=240,
    delay=0.5,
    #proxy_file = 'proxy.txt',
    #proxy_auth= 'silicons:1pRnQcg87F',
    use_cookie=True
    )

output_file = "output.csv"
total_cnt = 0

DRIVER_WAITING_SECONDS                  = 60
DRIVER_MEDIUM_WAITING_SECONDS           = 10
DRIVER_SHORT_WAITING_SECONDS            = 3

driver = None

start_url = "https://www.naukri.com/browse-jobs"

username = config.username
userpwd = config.userpwd

keywords = config.keywords

class AnyEc:
    """ Use with WebDriverWait to combine expected_conditions
        in an OR.
    """

    def __init__(self, *args):
        self.ecs = args

    def __call__(self, driver):
        for fn in self.ecs:
            try:
                if fn(driver): return True
            except:
                pass
def wait():
    sleep(random.randrange(DRIVER_SHORT_WAITING_SECONDS))

def wait_medium():
    offset_time = random.randrange(DRIVER_SHORT_WAITING_SECONDS +1 ,
        DRIVER_MEDIUM_WAITING_SECONDS)

    print("Sleep Time: {} ".format(offset_time))
    sleep(offset_time)

def show_exception_detail(e):
    print (e)
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print("{}, {}, {}".format(exc_type, fname, str(exc_tb.tb_lineno)))

def create_url():
    global driver, start_url, total_cnt
    
    # @todo Check to make sure that we have the information needed for this retailer in the DB
    try:
        # @TODO Timeout does not seem to be working here
        
        print('loading url... , {}'.format(start_url))

        driver.get(start_url)
        wait()

        print "Login with user"
        driver.find_element_by_xpath("//a[@id='login_Layer']").click()
        wait()
        
        driver.find_element_by_xpath("//input[@id='eLogin']").send_keys(username)
        wait()

        pwd_obj = driver.find_element_by_xpath("//input[@id='pLogin']")
        pwd_obj.send_keys(userpwd)
        wait()

        pwd_obj.send_keys(Keys.ENTER)
        wait_medium()
        
        driver.get(start_url)
        wait()

        search_div = driver.find_element_by_xpath("//div[@class='qsbfield']")

        #finance, mumbai, 5, 8
        skill_item = search_div.find_element_by_xpath("//div[@id='skill']//input")
        skill_item.click()
        skill_item.send_keys(keywords[0]["Skill"])
        wait()

        location_item = search_div.find_element_by_xpath("//div[@id='location']//input")
        location_item.click()
        location_item.send_keys(keywords[0]["Location"])
        wait()

        experience_item = search_div.find_element_by_xpath("//div[@id='exp_dd']//input")
        experience_item.click()

        li_divs = search_div.find_elements_by_xpath("//div[@id='exp_dd']/div[@class='sDrop']//ul/li")
        print "Experience Len=", len(li_divs)

        for li_div in li_divs:
            if li_div.text.strip() == str(keywords[0]["Experience"]):
                print "Select", li_div.text
                li_div.click()

        wait()

        salary_item = search_div.find_element_by_xpath(".//div[@id='salary_dd']//input")
        salary_item.click()
        li_divs = search_div.find_elements_by_xpath("//div[@id='salary_dd']/div[@class='sDrop']//ul/li")
        print "Experience Len=", len(li_divs)

        for li_div in li_divs:
            if li_div.text.strip() == str(keywords[0]["Salary"]):
                print "Select", li_div.text
                li_div.click()

        wait()
        
        print "Click submit to search"
        driver.find_element_by_xpath("//button[@id='qsbFormBtn']").click()
        wait_medium()

        print "Sory by date"        
        sort_div = driver.find_element_by_xpath("//div[@class='sortBy']")
        sort_div.click()
        wait()
        sort_div.find_element_by_xpath("//ul[@class='list']/li[contains(text(), 'Date')]").click()

        print "Loading job listing"
        job_listings = driver.find_elements_by_xpath("//div[contains(@class, 'srp_container fl')]//div[@type='tuple']")
        stop_find_job = False

        main_window_handle = driver.window_handles[0]
        
        print "Jobs = ", len(job_listings)
        for job_ind, job_listing in enumerate(job_listings):
            driver.switch_to.window(main_window_handle)
            post_date_str = job_listing.find_element_by_xpath("//div[@class='rec_details']/span").text

            print "Job Index=", job_ind, " Post Date =", post_date_str
            # if ("Today" in post_date_str) or ("day ago" in post_date_str):
            #     stop_find_job = True
            #     break

            job_listing.click()
            driver.switch_to.window(driver.window_handles[1])
            wait_medium()

            WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(
                AnyEc(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(text(), 'Apply')]")
                    ),
                    EC.presence_of_element_located(
                        (By.XPATH, "//a[contains(text(), 'Apply')]")
                    )
                )
            )

            print "Find Apply Button"
            apply_btn = None
            try:
                apply_btn = driver.find_element_by_xpath("//button[contains(text(), 'Apply')]")
            except Exception as e:
                #print e
                try:
                    apply_btn = driver.find_element_by_xpath("//a[contains(text(), 'Apply')]")
                except Exception as e:
                    #print e
                    pass
            
            #print apply_btn

            if apply_btn != None:
                actions = ActionChains(driver)
                actions.move_to_element(apply_btn)
                actions.click(apply_btn)
                actions.perform()
                #apply_btn.click()
                wait_medium()
                   
            else:
                print "Not found apply button"
                continue

            print "Find Skip Link Button"
            try:
                WebDriverWait(driver, DRIVER_WAITING_SECONDS).until(
                    AnyEc(
                        EC.presence_of_element_located(
                            (By.XPATH, "//a[@id='skip_qup']")
                        ),
                        EC.presence_of_element_located(
                            (By.XPATH, "//a[@id='qup_skip']")
                        )
                    )
                )
            except TimeoutException as t:
                #print t
                driver.close()
                continue
            
            skip_link = None

            try:
                skip_link = driver.find_element_by_xpath("//a[@id='skip_qup']")
            except Exception as e:
                #print e
                try:
                    skip_link = driver.find_element_by_xpath("//a[@id='qup_skip']")
                except Exception as e:
                    #print e
                    pass

            if skip_link != None:
                actions = ActionChains(driver)
                actions.move_to_element(skip_link)
                actions.click(skip_link)
                actions.perform()
                wait_medium()
               
            driver.close()
       
    except TimeoutException as ex:
        print('***********Exception1*************')
        show_exception_detail(ex)

    except Exception, e:
        print('***********Exception2*************')
        show_exception_detail(e)

if __name__ == '__main__':
    #create_url()
    parser = argparse.ArgumentParser(description="Do something.")
    parser.add_argument('-t', '--threads', type=int, required=False, default=10, help='Number of threads, defaults to 5')
    parser.add_argument('-p', '--proxy', type=int, required=False, default=0, help='Proxy type: 0(standard), 1(Micro leave), 2(Rotating)')
    
    args = parser.parse_args()

    threads_number = args.threads
    proxy_type = args.proxy

    driver = common_lib.create_chrome_driver(None)
    create_url() 
    common_lib.phantom_Quit(driver)