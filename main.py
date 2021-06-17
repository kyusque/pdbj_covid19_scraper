from enum import Enum
from time import sleep
import pandas as pd
from lxml import html

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

class Page(Enum):
    ALL = '/html/body/div[1]/div/main/div[2]/a[1]' # allのタブ
    REPR = '/html/body/div[1]/div/main/div[2]/a[2]' # 代表構造のタブ
    LATEST = '/html/body/div[1]/div/main/div[2]/a[3]' # 

class PdbjScraper:

    def move_page(self, driver, target: Page):
        element = driver.find_element_by_xpath(target.value)
        actions = ActionChains(driver)
        element.location_once_scrolled_into_view
        actions.move_to_element(element)
        actions.click()
        actions.perform()
        sleep(3)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/main/div[3]/div'))) # 下のメニューバー(ページ番号)

        # pdbid順
        element = driver.find_element_by_xpath('/html/body/div[1]/div/aside/div[2]/div[2]/label[1]') # 右のpdbid順の場所
        actions = ActionChains(driver)
        element.location_once_scrolled_into_view
        actions.move_to_element(element)
        actions.click()
        actions.perform()
        sleep(5)

    def read_page(self, driver, target, xpaths):
        data = []
        self.move_page(driver, target)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[1]/main/div[3]/div'))) # 下のメニューバー(ページ番号)
        while True:
            tree = html.fromstring((driver.page_source).encode('utf-8'))
            for i in  tree.xpath('/html/body/div[1]/div/div/div[3]/table/tbody/tr[*]'):
                data.append(["" if len(i.xpath(v)) == 0 else "".join(i.xpath(v)[0].itertext()) for k, v in xpaths.items()])
            try:
                driver.find_element_by_xpath('/html/body/div[1]/div/main/div[3]/div/a[text() = ">"]').click()  # 下のメニューバーの>ボタン
                sleep(3)
                #WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/img[ @class == ""]'))) # >を押したときに出る画像
            except:
                break
        return data


if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("-v", action="store_true")
    a = p.parse_args()
    opts = webdriver.ChromeOptions()
    if not a.v:
        opts.add_argument('--headless')
    with webdriver.Chrome(options=opts) as driver:
        url= "https://pdbj.org/featured/covid-19"
        driver.get(url)
        driver.set_window_size(2000,2000)
        sleep(5)
        scraper = PdbjScraper()
        xpaths = {
            "pdbid": "td[1]",
            "title": "td[2]/table/tbody/tr[1]",
            "mol": "td[2]/table/tbody/tr[contains(td[1],'Descriptor')]/td[2]",
            "author": "td[2]/table/tbody/tr[contains(td[1],'Authors')]/td[2]",
            "method": "td[2]/table/tbody/tr[contains(td[1],'Method')]/td[2]",
            "citation": "td[2]/table/tbody/tr[contains(td[1],'Cite')]/td[2]",
            "deposit": "td[2]/table/tbody/tr[contains(td[1],'Deposit')]/td[2]",
            "release": "td[2]/table/tbody/tr[contains(td[1],'Release')]/td[2]",
            "modified": "td[2]/table/tbody/tr[contains(td[1],'modified')]/td[2]"
        }
        data = scraper.read_page(driver, Page.ALL, xpaths)
        pdb = scraper.read_page(driver,  Page.REPR, {"pdbid": "td[1]"})

    a = pd.DataFrame(data, columns=xpaths.keys()).merge(pd.DataFrame(pdb, columns=["pdbid"]).assign(representative=True), how="left")
    a = a.assign(representative=~a["representative"].isna(), modified=a["modified"].where(a["modified"] != "", a["release"]))
    a.to_csv("test.csv")
