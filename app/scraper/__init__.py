import time
from os import getcwd
from random import choice
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SlipPicker:
    
    def __init__(self):
        self.driver = None
        self.url = 'https://www.betway.com.gh/'
        self.__initializeDriver()
    
    def __initializeDriver(self):
        options = webdriver.FirefoxOptions()
        options.set_preference("permissions.default.image", 2)
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        options.add_argument('--headless')
        self.driver = webdriver.Firefox(service=Service(executable_path=f"{getcwd()}/app/scraper/geckodriver", log_path=f"{getcwd()}/app/scraper/logs/geckodriver.log"), options=options)
        self.driver.get(self.url)
    
    
    def getSlipData(self, code):
        try:
            WebDriverWait(self.driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#helphero-dom > iframe")))
            self.driver.execute_script("document.querySelector('#helphero-dom > iframe').style.display = 'none';")
        except Exception as e:
            print(e)
        
        try:
            slipAreaOpener = self.driver.find_element(By.CSS_SELECTOR, "#headerBtnBetslip")
            if slipAreaOpener.is_displayed():
                slipAreaOpener.click()
        except Exception as e:
            print(e)
        
        try:
            WebDriverWait(self.driver, 40).until(EC.presence_of_element_located((By.ID, 'mtSearch')))
            searchInput = self.driver.find_element(By.ID, "mtSearch")
            searchInput.send_keys(code)
            searchBtn = self.driver.find_element(By.ID, "searchIconBetslip")
            searchBtn.click()
            WebDriverWait(self.driver, 40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#betslip-list > li")))
        except Exception as e:
            print(e)
        
        slipSoup = BeautifulSoup(self.driver.page_source, "lxml")
        self.driver.quit()
        
        matchSoup = slipSoup.find_all("li", attrs={"class": "SelectedOutcomeForBetslip ms-divider"})
        
        gamesData = []
        totalOdds = 1
        if len(matchSoup) > 0:
            for item in matchSoup:
                newGame = {'home': item.find('label', {'class': 'outcomeRow-Info'}).text.split(' v ')[0].strip(), 'away': item.find('label', {'class': 'outcomeRow-Info'}).text.split(' v ')[1].strip(), 'odds': item.find('div', {'class': 'betslipPriceDecimal'}).text, 'betType': item.find('label', {'class': 'outcomeRow-title'})['data-translate-market'], 'matchType': item.find('label', {'class': 'outcomeRow-title'})['data-translate-set'], 'outcome': item.find('label', {'class': 'outcomeRow-title'}).text}
                if item.find('div', {'class': 'betslipPriceDecimal'}).text.strip().isdigit():
                    totalOdds *= int(item.find('div', {'class': 'betslipPriceDecimal'}).text.strip())
                gamesData.append(newGame)
        
        return { 'code': code, 'games': gamesData, 'odds': totalOdds }