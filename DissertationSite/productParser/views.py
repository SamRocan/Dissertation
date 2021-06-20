from django.shortcuts import render
from django.http import HttpResponse

from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def index(request):
    return render(request, 'productParser/index.html')

def homepage(request):
    return render(request, 'productParser/home.html')

def send(request):

    #Fixes String for URL Finder
    def stringFixer(entry):
        entry = entry.translate({ord(c): " " for c in "@#$%^&[]{};:,/<>?\\'|`=+"})
        for x in entry:
            entry = entry.replace("  ", " ")
        entry = entry.replace(" ", "%20")
        if(len(entry) > 2 and (entry[len(entry)-3:len(entry)] == "%20")):
            entry =  entry[:len(entry)-3]
        return entry

    pages = int(request.GET['page-no'])/10
    search = stringFixer(request.GET['search-area'])
    siteLink = 'https://www.producthunt.com/search/posts?q='+search

    chromeOptions = Options()
    chromeOptions.headless = True

    driver = webdriver.Chrome(executable_path="./chromedriver", options=chromeOptions)

    driver.get(siteLink)

    try:
        SCROLL_PAUSE_TIME = 1
        driver.maximize_window()
        last_height = driver.execute_script("return document.body.scrollHeight")
        count=0
        while count<pages:
            print("I"*count)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            count += 1
    finally:

        soup = BeautifulSoup(driver.page_source, "html.parser")
        linkList = []
        titleList = []
        for c in soup("a"):
            z = str(c)
            if ("href=\"/posts/" and "data-test=\"post-name") in z:
                start = z.find("href")
                end = z.find(">") - 1
                print("http://producthunt.com"+(z[start+6:end]))
                linkList.append("http://producthunt.com"+(z[start+6:end]))
        #removes ad
        for c in soup("h3"):
            titleList.append(c.getText())
            print(c.getText())
        pass
        #maybe look at a more elegent way of removing advert links
        titleList.pop(3)

    zipList = zip(titleList, linkList)
    return render(request, 'productParser/results.html', {'zipList':zipList})