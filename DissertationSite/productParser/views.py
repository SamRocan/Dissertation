import requests
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import View, TemplateView
from django.shortcuts import render
from django.conf import settings
import snscrape.modules.twitter as sntwitter
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os



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
        slugList = []
        titleList = []
        for c in soup("a"):
            z = str(c)
            if ("href=\"/posts/" and "data-test=\"post-name") in z:
                start = z.find("href")
                end = z.find(">") - 1
                print("http://producthunt.com"+(z[start+6:end]))
                slugList.append((z[start+13:end]))
        #removes ad
        for c in soup("h3"):
            titleList.append(c.getText())
            print(c.getText())
        pass
        #maybe look at a more elegent way of removing advert links
        titleList.pop(3)

    zipList = zip(titleList, slugList)
    return render(request, 'productParser/results.html', {'zipList':zipList})

def product(request, productName):
    API_URL = "https://api.producthunt.com/v2/api/graphql"

    # Specify your API token
    MY_API_TOKEN = "PbEz8mWhaMzYy1J8WwS-X2-YXi92xhRffQS3YDi3xl4"
    slug = productName

    # Specify your query

    query = {"query":
                 """
                 query FindBySlug {
                 post(slug:"""+ "\""+ slug +"\"" + """){
                    commentsCount
                    comments(first:5){
                        edges{
                            node{
                                body
                            }
                        }
                    }
                    createdAt
                    description
                    featuredAt
                    id
                    isCollected
                    isVoted
                    makers{
                        name
                        username
                    }
                    media{
                        url
                    }
                    name
                    productLinks{
                        url
                    }
                    reviewsRating
                    slug
                    tagline
                    thumbnail{
                        url
                    }
                    topics(first:5){
                        edges{
                            node{
                                name
                            }
                        }
                    }
                    votesCount
                    website
                }
            }
        """}

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + MY_API_TOKEN,
        'Host': 'api.producthunt.com'
    }
    posts = requests.post(API_URL,
                          headers=headers,
                          data=json.dumps(query))

    jsonInfo = posts.json()
    results = {}
    topics =[]
    print("Running")
    for i in jsonInfo['data']['post']:
        if(i=='makers'):
            print("Makers")
            for y in jsonInfo['data']['post']['makers']:
                print(str(y['username']) + ": " + str(y['name']))
        if(i=='media'):
            print("Media")
            for y in jsonInfo['data']['post']['media']:
                print(y['url'])
        if(i=='productLinks'):
            print("Product Links")
            for y in jsonInfo['data']['post']['productLinks']:
                print(y['url'])
        if(i=='thumbnail'):
            print("Thumbnail")
            logo = str(jsonInfo['data']['post'][i]['url'])
        if(i=='topics'):
            print("Topics")
            for y in jsonInfo['data']['post']['topics']['edges']:
                topics.append(y['node']['name'])
        results[i] = str(jsonInfo['data']['post'][i])
    print(results.get('tagline'))



    product_name = slug.capitalize()

    context = {
        'results':results,
        'topics':topics,
        'logo':logo
    }
    return render(request, 'productParser/product.html', {"context":context})
    #return HttpResponse("LOADED PAGE %s" % product)
