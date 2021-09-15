import requests
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.generic import View, TemplateView
from django.shortcuts import render
from django.conf import settings
import snscrape.modules.twitter as sntwitter
import json
from json import dumps
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import os
import requests
from urllib.request import Request, urlopen


Names = []
TwitterHandles = []


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
                        twitterUsername
                        profileImage                        
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
    global Names
    Names = []
    global TwitterHandles
    TwitterHandles = []
    phUrls = []
    profilePics = []
    print("Running")
    for i in jsonInfo['data']['post']:
        if(i=='makers'):
            print("Makers")
            for y in jsonInfo['data']['post']['makers']:
                TwitterHandles.append(y['twitterUsername'])
                Names.append(y['name'])
                phUrls.append(y['username'])
                profilePics.append(y['profileImage'])
                print(y['twitterUsername'])
                print(str(y['twitterUsername']) + ": " + str(y['name']))
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

    """Paring Other Websites"""
    companyName = str(results.get('name'))

    socialMediaZip = zip(Names,TwitterHandles, phUrls, profilePics)

    product_name = slug.capitalize()

    print("Twitter Handle is " + str(TwitterHandles))
    print("Names are : " + str(Names))

    ####################
    #Get News
    newsHeadlines = []
    newsLink = []
    """
    url = "https://bing-news-search1.p.rapidapi.com/news/search"

    newsQuery = str(topics[0])
    querystring = {"q":newsQuery,"safeSearch":"Off","textFormat":"Raw","freshness":"Day"}

    headers = {
        'x-bingapis-sdk': "true",
        'x-rapidapi-host': "bing-news-search1.p.rapidapi.com",
        'x-rapidapi-key': "cc31406e1cmshee5b3ea7ab27afbp1895d6jsnc029cbf06f88"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    response.raise_for_status()
    response_data = response.json()
    newsCount = 0
    for i in response_data['value']:
        if newsCount<5:
            newsHeadlines.append(i['name'])
            newsLink.append(i['url'])
            newsCount+=1
"""
    newsZip = zip(newsLink,newsHeadlines)
    ####################
    searchStat = StatistaSearcher()
    if(topics[0] == "Productivity"):
        statRes = searchStat.searchStatista(topics[1])
    else:
        statRes = searchStat.searchStatista(topics[0])
    getLinks = searchStat.getLinks(statRes)
    print(getLinks)

    if(len(getLinks) == 0):
        statLabels = []
        chartLabel = ""
        chartData = []
    else:
        statGraph = StatistaGraph(getLinks[0])

        graphInfo = statGraph.getInfo()
        chartLabel = graphInfo[0]
        statLabels = graphInfo[1]
        statLabels.reverse()
        chartData = graphInfo[2]
        chartData.reverse()
    statData ={
        "labels":statLabels,
        "chartLabel":chartLabel,
        "chartData":chartData,
    }

    jsonData = dumps(statData)
    combi = YCombinatorInfo(companyName)
    combiData = {
        'founders':combi.getFounders(),
        'jobs':combi.getJobsHiring(),
        'overview':combi.getOverview(),
    }
    print("---- YCOMBINATOR ----")
    print(combiData)
    print("---- Capterra ----")
    cap = CapterraInfo(companyName)
    captData = cap.competitorComparison()
    print("---- Saasworth ----")
    saas = SaasworthyInfo(companyName)
    saasData = {
        'pricing':saas.getPricingInfo(),
        'score':saas.getSWScore(),
        'features':saas.getFeatures(),
        'tech_details':saas.getTechDetails(),
        'social_media':saas.getSocialMediaInfo()
    }


    context = {
        'data':jsonData,
        'results':results,
        'topics':topics,
        'logo':logo,
        'names':Names,
        'socialMediaZip':socialMediaZip,
        'newsZip':newsZip,
        'twitterHandles':TwitterHandles,
        'combiData':combiData,
        'captData':captData,
        'saasData':saasData
    }

    return render(request, 'productParser/product.html', {"context":context})

def analysis(request, userName, self=None):
    userName = userName
    if(userName == "None"):
        return render(request, 'productParser/noTwitter.html')
    module_dir = os.path.dirname('media/')
    all_users = os.path.join(module_dir, 'combined_users.xlsx')
    user_scores = os.path.join(module_dir, 'user_scores.xlsx')
    liwc_dic = os.path.join(module_dir, 'LIWC2007_Ammended.dic')
    start_time = time.time()

    data = LIWCAnalysis.getExcel(self, all_users)
    score_data = LIWCAnalysis.getExcel(self, user_scores)
    print(userName)
    print("Getting Tweets for " + str(userName))
    twitterContent = LIWCAnalysis.getTweets(self, userName)
    print("Getting Tweets took ", time.time() - start_time, " to run")


    print("Tokenizing Tweets")
    tokenizedTweets = LIWCAnalysis.tokenize(self, twitterContent)
    print(tokenizedTweets)
    print("Tokenizing Tweets took ", time.time() - start_time, " to run")

    print("turning to dictionary")
    dictionary = LIWCAnalysis.dic_to_dict(self, liwc_dic)
    print("Dictionary took ", time.time() - start_time, " to run")

    print("Categorizing tokens")
    values = LIWCAnalysis.match_regex_to_text(self, tokenizedTweets[0], dictionary)
    print("Categorizing tokens took ", time.time() - start_time, " to run")

    print("Getting Best Match")
    match = LIWCAnalysis.bestMatch(self, data, values)
    print("Best Match took ", time.time() - start_time, " to run")

    profile = list(match.keys())[0]
    print("Getting Scores")
    scores = LIWCAnalysis.getScore(self, score_data, profile)
    print("Scores took ", time.time() - start_time, " to run")

    scoresVar = scores[0]
    catVar = scores[1]
    fiveFactors = ["Extraversion", "Neuroticism", "Agreableness", "Concientiousness", "Openness"]

    print("My program took ", time.time() - start_time, " to run")
    extScore = scoresVar[0]
    neuScore = scoresVar[1]
    agrScore = scoresVar[2]
    conScore = scoresVar[3]
    opnScore = scoresVar[4]
    ext = "Extraversion (" + str(catVar[0]) + ")"
    neu = "Neuroticism (" + str(catVar[1]) + ")"
    agr = "Agreableness (" + str(catVar[2]) + ")"
    con = "Concientiousness (" + str(catVar[3]) + ")"
    opn = "Openness (" + str(catVar[4]) + ")"

    print("My program took ", time.time() - start_time, " to run")

    fiveFactorData = {
        'fiveFactors': fiveFactors,
        'scores': scoresVar,
        'cats': catVar,
        'founderName':userName
    }

    jsonData = dumps(fiveFactorData)

    context = {
        #'scoresVar':scoresVar,
        #'catVar':catVar,
        'data':jsonData,
        'extScore':extScore,
        'neuScore':neuScore,
        'agrScore':agrScore,
        'conScore':conScore,
        'opnScore':opnScore,
        'ext':ext,
        'neu':neu,
        'agr':agr,
        'con':con,
        'opn':opn,
        'founderName':userName
    }

    return render(request, 'productParser/analysis.html', context)


def noTwitter(request):
    return render(request, 'productParser/noTwitter.html')

# Classes

class LIWCAnalysis:

    def getExcel(self, filename):
        # 0 means sheet zero
        exFile = pd.read_excel(filename,0)
        return exFile

    def getUserData(self, xlx, colName):
        user = []
        for i in range(0,64):
            user.append(xlx[colName][i])

        return user

    def getCategoryData(self, xlx, catNo):
        col = xlx.loc[catNo,:]
        category = []
        plus = 0
        for g in range(1, 241):
            if g not in col:
                pass
            else:
                category.append(col[g])
        return category

    def printUserData(self, xlx, colName):
        print(colName)
        print("------")
        total = 0
        for i in range(0, 64):
            print(str(xlx['CAT'][i]) + ": " + str(xlx[5][i]))
            total+= xlx[5][i]
        print("Total is: " + str(total))
        avg = total / 64
        print("Average is: " + str(avg))

    def printCategoryData(self, xlx, catNo):
        col = xlx.loc[catNo,:]
        head = xlx.columns.values
        print("---")
        total = 0
        plus = 0
        for g in range(1, 241):
            if g not in col:
                print("No " + str(g) + " col")
                plus+=1
            else:
                total += float(col[g])
                print("User " + str(head[g-plus]) + " " + str(col[g]))

        print("Average is: " + str(total/238))

    def printEverything(self, xlx):
        #Print everything
        for i in range(0, 64):
            print(i)
            self.printCategoryData(xlx, i)

    def bestMatch(self, xlx, user):
        mainUserData = user
        users = {}
        # 1) Create dict of all users initialize to 0
        for i in range(1, 241):
            if(i == 17 or i == 66):
                pass
            else:
                users[i] = 0

        # 2) For each category
        for i in range(64):
            # 3) Get all the scores from a category
            scoresForCategory = LIWCAnalysis.getCategoryData(self, xlx, i)
            mainUserData[i]
            scoreDict = {}
            count = 1
            for j in range(238):
                # 4) Calulate the difference between users and each test score
                scoreDict[count] = abs(mainUserData[i]-scoresForCategory[j])
                count+=1
                if(count == 17 or count == 66):
                    count+=1
            scoreDict = dict(sorted(scoreDict.items(), key=lambda item: item[1]))
            count = 0
            for x,y in scoreDict.items():
                users[x] += count
                count += 1

        users = dict(sorted(users.items(), key=lambda item: item[1]))
        return users

    def dic_to_dict(self, filename):
        exportDict = dict()
        with open(filename) as file:
            lines = file.readlines()
            for line in lines:
                num = ""
                numList = []
                count = 0
                word = ""
                while(line[count].islower() or line[count] == '+'):
                    word += line[count]
                    #print(str(word))
                    count+=1
                    if(count == len(line)-1):
                        break
                for i in line:
                    if i.isdecimal():
                        num+= i
                    if num != "" and i.isdecimal() == False:
                        numList.append(int(num))
                        num = ""
                    #print(str(line) + " " + str(count))
                exportDict[word] = numList
        return exportDict

    def simpTokenize(self, text):
        retList = []
        word = ""
        for i in text:
            if i == ' ':
                retList.append(word)
                word = ""
            else:
                word+= i
        retList.append(word)
        return retList

    def match_regex_to_text(self, tokens, dictionary):
        values = []
        for word in tokens:
            wordMatch = []
            valMatch = []

            matchedWords = []
            for reg,value in dictionary.items():
                if(re.match(reg, word)):
                    matchedWords.append(reg)
            sorted_matches = sorted(matchedWords, key=len)
            length = len(sorted_matches)
            if(length>=1):
                wordMatch.append(word)
                valMatch.append(dictionary[sorted_matches[length-1]])

            #Uncomment this to see words as they get added
            #for i in range(0, len(wordMatch)):
            #print(str(wordMatch[i]) + ":")
            #print(valMatch[i])
            for i in valMatch:
                for z in i:
                    values.append(z)

        print("------------")
        return values

    def removeSpecialCharacters(self, str):
        retStr = re.sub('[^a-zA-Z0-9]+', '', str)
        return retStr

    def getTweets(self, username):
        tweets_list = []
        twitterContent = ""
        #Puts tweets into list
        for i,tweet in enumerate(sntwitter.TwitterSearchScraper('from:'+username).get_items()): #declare a username
            if i>10: #number of tweets you want to scrape
                break
            tweets_list.append([tweet.date, tweet.id, tweet.content]) #declare the attributes to be returned

        for i in tweets_list:
            twitterContent += str(i[2])

        return twitterContent

    def tokenize(self, tweets):
        splitwords = tweets.split(" ")
        mentions = []
        links = []
        words = []
        prices = []
        for i in splitwords:
            print(i)
            if(len(i)>0):
                if(i[0]=='@'):
                    mentions.append(i)
                if(i[0]=='$' or i[0]=='£'):
                    prices.append(i)
            if(len(i)>7):
                if(i[0:6]=='https:'):
                    links.append(i)
            else:
                word = str.lower(LIWCAnalysis.removeSpecialCharacters(self, i))
                if(len(word)>0):
                    words.append(word)
        retList = []
        retList.append(words)
        retList.append(mentions)
        retList.append(links)
        retList.append(prices)
        return retList

    def getScore(self, xlx, userNo):
        retList = []
        scores = []
        categories = []
        sub = 2
        if(userNo<=16):
            sub = 1
        if(userNo >=67):
            sub = 3
        user = xlx.loc[userNo-sub,:]
        for i in range(1,11):
            if(i<6):
                scores.append(user[i])
            else:
                categories.append(str(user[i]))

        retList.append(scores)
        retList.append(categories)
        return retList

    LIWC = {
        1:0,
        2:0,
        3:0,
        4:0,
        5:0,
        6:0,
        7:0,
        8:0,
        9:0,
        10:0,
        11:0,
        12:0,
        13:0,
        14:0,
        15:0,
        16:0,
        17:0,
        18:0,
        19:0,
        20:0,
        21:0,
        22:0,
        121:0,
        122:0,
        123:0,
        124:0,
        125:0,
        126:0,
        127:0,
        128:0,
        129:0,
        130:0,
        131:0,
        132:0,
        133:0,
        134:0,
        135:0,
        136:0,
        137:0,
        138:0,
        139:0,
        140:0,
        141:0,
        142:0,
        143:0,
        146:0,
        147:0,
        148:0,
        149:0,
        150:0,
        250:0,
        251:0,
        252:0,
        253:0,
        354:0,
        355:0,
        356:0,
        357:0,
        358:0,
        359:0,
        360:0,
        462:0,
        463:0,
        464:0,
    }

class StatistaGraph:
    def __init__(self, url):
        self.link = "https://www.statista.com" + url
        self.soup = BeautifulSoup(requests.get(self.link).content, 'html.parser')

        self.thd = self.soup.select('#statTableHTML th')
        self.tds = self.soup.select('#statTableHTML td')
        self.heading = self.soup.find("h2", {"class":"sectionHeadline"})
        self.title = self.heading.text.strip()
        #print(self.thd)
        #print(self.tds)
        self.cols = []
        self.data = []
        self.intData = []

        for i in self.tds:
            i = str(i.text).replace(",","")
            test = i.replace('.', '',1)
            if(i.isdigit()==False and test.isdigit()==False and i!="-"):
                self.cols.append(i)
            elif(i!="-"):
                self.data.append(i)

        for nums in range(len(self.data)):
            retNum = ""
            for i in self.data[nums]:
                if(i.isdigit() or i=="."):
                    retNum +=i
            if(retNum!="-" and retNum!="."):
                self.intData.append(float(retNum))

        if(len(self.cols)== 0):
            hold = []
            for i in range(1900,2100):
                if(float(i) in self.intData):
                    hold.append(i)
            if(len(hold)>2):
                for i in hold:
                    self.cols.append(i)
                    self.intData.remove(i)

    def getInfo(self):
        retList = []
        retList.append(self.title)
        retList.append(self.cols)
        retList.append(self.intData)
        return retList

class StatistaSearcher:

    def searchStatista(self, query):
        #query = str(input("Enter query: "))
        url = 'https://www.statista.com/search/?q='+query+'&Search=&qKat=search'
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        linkList = soup.find_all("li")
        return linkList

    def soupToLink(self, resultSetList):
        links = []
        for i in resultSetList:
            loc1 = str(i).find("href")
            loc2 = str(i).find("title")
            links.append(str(i)[loc1+6:loc2-2])
        return links

    def getLinks(self, linkList):
        premiumStatisticLinks = []
        basicStatisticLinks = []
        topicLinks = []

        for i in range(len(linkList)):
            if("searchContentTypeStatistic" in str(linkList[i])):
                if("iconSprite--statisticPremium" in str(linkList[i])):
                    element = linkList[i].find_all('a', href=True)
                    premiumStatisticLinks.append(element)
                if("iconSprite--statisticBasis" in str(linkList[i])):
                    element = linkList[i].find_all('a', href=True)
                    basicStatisticLinks.append(element)
            if("searchContentTypeTopic" in str(linkList[i])):
                if("iconSprite--topic" in str(linkList[i])):
                    element = linkList[i].find_all('a', href=True)
                    topicLinks.append(element)

        basicStatPage = self.soupToLink(basicStatisticLinks)
        premiumStatPage = self.soupToLink(premiumStatisticLinks)
        topicPage = self.soupToLink(topicLinks)

        return(basicStatPage)

class CapterraInfo:
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}

    def __init__(self, query):
        self.newQ = '+'.join(query.split())
        newQ = '+'.join(query.split())
        capterraQ = '-'.join(query.split())
        capterraQ = capterraQ.lower()
        q = "capterra+"+newQ
        url = 'https://www.google.com/search?q=' + q + '&ie=utf-8&oe=utf-8'
        request = Request(url,headers=self.headers)
        try:
            page = urlopen(request)
            soup = BeautifulSoup(page, features="lxml")
            links = soup.findAll('a')
            retStr = None
            done = False
            for i in links:
                if("/url?q" in str(i) and "google" not in str(i) ):
                    if(("capterra" in str(i)) and (capterraQ in str(i)) and done==False):
                        retStr = ""
                        for z in str(i["href"])[7:]:
                            if(z=='&'):
                                done=True
                            if(done==False):
                                retStr+=z

            if(retStr == None):
                self.soup = None
            else:
                page = requests.get(retStr)
                self.soup = BeautifulSoup(page.content, 'html.parser')
        except:
            self.soup = None
    def competitorComparison(self):
        if(self.soup == None):
            return []
        section = self.soup.findAll(class_="row flex-nowrap flex-row-4 flex-row-xl-5")
        if(section != None):
            companyComparison = {}
            headers = []
            for i in range(len(section)):
                category = []
                headCount = 0
                for q in section[i]:
                    for p in q:
                        if("N/A" in str(p)):
                            category.append(p.strip())
                        if('Tag' in str(type(p))) and ( len(p.text) != 0):
                            if(i!=0):
                                category.append(p.text.strip())
                            elif(headCount%4 ==0):
                                headers.append(p.text.strip())
                            headCount+=1
                if(len(category)>0):
                    finalList = []
                    for x in range(len(category)):
                        if(x!=0 and (category[x] != category[0])):
                            finalList.append(category[x])
                    companyComparison[category[0]] = finalList
            companyComparison["Name"] = headers
            return companyComparison
        else:
            return None

class SaasworthyInfo:
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}

    def __init__(self, q):
        newQ = '+'.join(q.split())
        saasQ = '-'.join(q.split())
        saasQ = saasQ.lower()
        newQ = "saasworthy+"+newQ
        url = 'https://www.google.com/search?q=' + newQ + '&ie=utf-8&oe=utf-8'
        request = Request(url,headers=self.headers)
        try:
            page = urlopen(request)
            soup = BeautifulSoup(page, features="lxml")
            links = soup.findAll('a')
            retStr = None
            done=False
            for i in links:
                if("/url?q" in str(i) and "google" not in str(i) ):
                    if(("saasworthy" in str(i)) and (saasQ in str(i)) and done==False):
                        retStr = ""
                        for z in str(i["href"])[7:]:
                            if(z=='&'):
                                done=True
                            if(done==False):
                                retStr+=z
            if(retStr == None):
                self.soup = None
            else:
                page = requests.get(retStr)
                self.soup = BeautifulSoup(page.content, 'html.parser')
        except:
            self.soup = None

    def getPricingInfo(self):
        if(self.soup == None):
            return []
        prices = self.soup.findAll('span', {'class': 'pln-price'})
        titles = self.soup.findAll('span', {'class': 'plan-title'})

        altPrices = []
        titlesList =  []
        mainPrices = {}
        for i in titles:
            if ("Free" in i.text):
                altPrices.append(str(i.text.strip()))
            else:
                titlesList.append(str(i.text.strip()))

        for i in range(len(prices)):
            #print(titlesList[i] + ": " + str(prices[i].text.strip()))
            mainPrices[titlesList[i]] = str(prices[i].text.strip())
        for i in range(len(prices), len(titles)-len(altPrices)):
            altPrices.append(titlesList[i])
            mainPrices[titlesList[i]] = titlesList[i]

        #print("\n")

        #print("Other Options")
        #for i in altPrices:
        #print(i)
        return mainPrices

    def getFeatures(self):
        if(self.soup == None):
            return []
        features = self.soup.find(class_="feture_list")
        if(features != None):
            items = features.findAll('li')
            retFeatures = []
            for i in items:
                if('fa-check' in str(i)):
                    retFeatures.append(i.text)
            return retFeatures
        return []

    def getSWScore(self):
        if(self.soup == None):
            return []
        score = self.soup.find(class_="pop_score_d")
        if(score != None):
            return score.text.strip()[0:3]
        else:
            return []

    def getSocialMediaInfo(self):
        if(self.soup == None):
            return []
        social_media_followers = self.soup.findAll(class_="flwrs-row")

        socialMediaFollowers = {}
        for i in social_media_followers:
            if("twitter" in str(i)):
                print("Twitter Followers: " + str(i.text.strip()))
                socialMediaFollowers['Twitter'] = str(i.text.strip())
            if("linkedin" in str(i)):
                print("LinkedIn Followers: " + str(i.text.strip()))
                socialMediaFollowers['LinkedIn'] = str(i.text.strip())
            if("facebook" in str(i)):
                print("Facebook Followers: " + str(i.text.strip()))
                socialMediaFollowers['Facebook'] = str(i.text.strip())
            if("instagram" in str(i)):
                print("Instagram Followers: " + str(i.text.strip()))
                socialMediaFollowers['Instagram'] = str(i.text.strip())
            if("youtube" in str(i)):
                print("Youtube Followers: " + str(i.text.strip()))
                socialMediaFollowers['Youtube'] = str(i.text.strip())
        return socialMediaFollowers

    #https://stackoverflow.com/questions/23377533/python-beautifulsoup-parsing-table
    #Re do this method to amend the API array, the you're done.
    def getTechDetails(self):
        if(self.soup == None):
            return []
        data = []
        table = self.soup.find('table', attrs={'class':'tech-det-table'})
        if(table!= None):
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele])

            dataTidy = []
            for i in data:
                count=0
                tabInfo = []
                for z in range(len(i)):
                    text = i[z].replace("\n", ", ")
                    count+=1
                    tabInfo.append(text)#(i[z])
                    if(count%2==0):
                        dataTidy.append(tabInfo)
                        tabInfo = []
            return dataTidy
        return []

class YCombinatorInfo:
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit537.36 (KHTML, like Gecko) Chrome","Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}

    def __init__(self, q):
        newQ = '+'.join(q.split())
        yCombq = '-'.join(q.split())
        yCombq = yCombq.lower()
        q = "ycombinator-"+newQ
        url = 'https://www.google.com/search?q=' + q + '&ie=utf-8&oe=utf-8'
        request = Request(url,headers=self.headers)
        try:
            page = urlopen(request)
            soup = BeautifulSoup(page, features="lxml")
            links = soup.findAll('a')
            done=False
            retStr = None
            for i in links:
                if("/url?q" in str(i) and "google" not in str(i) and "jobs" not in str(i)):
                    if(("ycombinator" in str(i)) and (yCombq in str(i))  and done==False):
                        retStr = ""
                        for z in str(i["href"])[7:]:
                            if(z=='&'):
                                done=True
                            if(done==False):
                                retStr+=z
            if(retStr == None):
                self.soup = None
            else:
                page = requests.get(retStr)
                self.soup = BeautifulSoup(page.content, 'html.parser')
        except:
            self.soup = None

    def getOverview(self):
        if(self.soup == None):
            return []
        res = self.soup.find(class_="facts")
        if(res!= None):
            divs = res.findAll("div")

            retOverview = []
            for i in divs:
                retOverview.append(i.text.strip())
            return retOverview
        else:
            return []

    def getFounders(self):
        if(self.soup == None):
            return []
        res = self.soup.findAll(class_="founder-card")
        if(res!= None):
            names = []
            for i in res:
                name = i.find(class_="font-bold")
                name = name.text
                names.append(name)

            return names
        else:
            return []

    def getJobsHiring(self):
        if(self.soup == None):
            return []
        jobs = []
        res = self.soup.findAll(class_="job-heading")
        if(res != None):
            for i in res:
                job = {}
                title = i.find(class_="job-title")
                job['position'] = title.text
                dets = i.findAll(class_="job-detail")
                for z in range(len(dets)):
                    if(z == 0):
                        job['location'] = dets[z].text
                    if('year' in dets[z].text):
                        job['experience'] = dets[z].text
                    if(('£' or '$' or '€') in dets[z].text):
                        job['salary'] = dets[z].text
                    if('%' in dets[z].text):
                        job['equity'] = dets[z].text
                jobs.append(job)
            return jobs
        else:
            return []
