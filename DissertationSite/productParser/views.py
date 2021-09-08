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

    socialMediaZip = zip(Names,TwitterHandles, phUrls, profilePics)

    product_name = slug.capitalize()

    print("Twitter Handle is " + str(TwitterHandles))
    print("Names are : " + str(Names))
    context = {
        'results':results,
        'topics':topics,
        'logo':logo,
        'names':Names,
        'socialMediaZip':socialMediaZip,
        'twitterHandles':TwitterHandles,
    }
    return render(request, 'productParser/product.html', {"context":context})
    #return HttpResponse("LOADED PAGE %s" % product)

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
                    print(str(line) + " " + str(count))
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
            if i>1000: #number of tweets you want to scrape
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
                scores.append(str(user[i]))
            else:
                categories.append(str(user[i]))

        retList.append(scores)
        retList.append(categories)
        return retList

    # Running with handle @bigmommaprods:   1281s
    # Running with handle @_visionex:       1074s
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

class JSView(View):
    global Names
    global TwitterHandles
    def get(self, *args, **kwargs):
        #media_url = settings.MEDIA_URL
        #users = media_url + "combined_users.xlsx"
        module_dir = os.path.dirname('media/')
        all_users = os.path.join(module_dir, 'combined_users.xlsx')
        user_scores = os.path.join(module_dir, 'user_scores.xlsx')
        liwc_dic = os.path.join(module_dir, 'LIWC2007_Ammended.dic')
        start_time = time.time()

        data = LIWCAnalysis.getExcel(self, all_users)
        score_data = LIWCAnalysis.getExcel(self, user_scores)
        print(Names)
        print(TwitterHandles)
        print("Getting Tweets for " + str(TwitterHandles[0]))
        twitterContent = LIWCAnalysis.getTweets(self, TwitterHandles[0])
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


        print("My program took ", time.time() - start_time, " to run")
        extScore = "Extraversion: " + str(scoresVar[0])
        neuScore = "Neuroticism: " + str(scoresVar[1])
        agrScore = "Agreableness: " + str(scoresVar[2])
        conScore = "Concientiousness: " + str(scoresVar[3])
        opnScore = "Openness: " + str(scoresVar[4])
        ext = str(catVar[0])
        neu = str(catVar[1])
        agr = str(catVar[2])
        con = str(catVar[3])
        opn = str(catVar[4])

        print("My program took ", time.time() - start_time, " to run")


        context = {
            #'scoresVar':scoresVar,
            #'catVar':catVar,
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
            'founderName':Names[0]
        }

        return JsonResponse({'context':context}, safe=False)