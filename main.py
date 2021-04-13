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
    ALL = '/html/body/div[2]/div[1]/div/div[2]/span[1]'
    REPR = '/html/body/div[2]/div[1]/div/div[2]/span[2]'
    LATEST = '/html/body/div[2]/div[1]/div/div[2]/span[3]'

class PdbjScraper:

    def move_page(self, driver, target: Page):
        element = driver.find_element_by_xpath(target.value)
        actions = ActionChains(driver)
        element.location_once_scrolled_into_view
        actions.move_to_element(element)
        actions.click()
        actions.perform()
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[1]/div/div[3]/div/div')))

        # pdbid順
        element = driver.find_element_by_xpath('//*[@id="pageDIV"]/div[1]/aside/div[1]/div[2]/label[1]')
        actions = ActionChains(driver)
        element.location_once_scrolled_into_view
        actions.move_to_element(element)
        actions.click()
        actions.perform()
        sleep(1)
        element = driver.find_element_by_xpath('//*[@id="pageDIV"]/div[1]/aside/div[1]/div[2]/label[4]')
        actions = ActionChains(driver)
        element.location_once_scrolled_into_view
        actions.move_to_element(element)
        actions.click()
        actions.perform()
        sleep(1)

    def read_page(self, driver, target, xpaths):
        data = []
        self.move_page(driver, target)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[1]/div/div[3]/div/div')))
        while True:
            tree = html.fromstring((driver.page_source).encode('utf-8'))
            for i in  tree.xpath("/html/body/div[2]/div[1]/div/div[3]/table/tbody/tr[*]"):
                data.append(["" if len(i.xpath(v)) == 0 else "".join(i.xpath(v)[0].itertext()) for k, v in xpaths.items()])
            try:
                driver.find_element_by_xpath('/html/body/div[2]/div[1]/div/div[3]/div/div/a[text() = ">"]').click()
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[@class = "loadingImage" and @class != "visible"]')))
            except:
                break
        return data


if __name__ == "__main__":
    opts = webdriver.ChromeOptions()
    opts.add_argument('--headless')
    with webdriver.Chrome(options=opts) as driver:
        url= "https://pdbj.org/featured/covid-19"
        driver.get(url)
        sleep(5)
        scraper = PdbjScraper()
        xpaths = {
            "pdbid": "td[1]",
            "mol": "td[2]/table/tbody/tr[contains(td[1],'分子名称')]/td[2]",
            "author": "td[2]/table/tbody/tr[contains(td[1],'著者')]/td[2]",
            "method": "td[2]/table/tbody/tr[contains(td[1],'実験手法')]/td[2]",
            "reference": "td[2]/table/tbody/tr[contains(td[1],'引用文献')]/td[2]",
            "register": "td[2]/table/tbody/tr[contains(td[1],'登録日')]/td[2]",
            "publish": "td[2]/table/tbody/tr[contains(td[1],'公開日')]/td[2]",
            "update": "td[2]/table/tbody/tr[contains(td[1],'最終更新日')]/td[2]"
        }
        data = scraper.read_page(driver, Page.ALL, xpaths)
        pdb = scraper.read_page(driver,  Page.REPR, {"pdbid": "td[1]"})

    a = pd.DataFrame(data, columns=xpaths.keys()).merge(pd.DataFrame(pdb, columns=["pdbid"]).assign(representative=True), how="left")
    a = a.assign(representative=~a["representative"].isna(), update=a["update"].where(a["update"] != "", a["publish"]))
    a.to_csv("test.csv")
