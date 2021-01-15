"""https://pixiv-api.readthedocs.io/en/latest/"""
from pixivapi import Client, Size, Visibility, PixivError
from pathlib import Path
from time import sleep
import shutil
import os
import collections

USERNAME=""
PASSWORD=""

def filterTags(tagList):
    while len(tagList)>1:
        allId=tagList[0]+tagList[1]
        allId= [item for item, count in collections.Counter(allId).items() if count > 1]
        tagList.append(allId)
        del tagList[0],tagList[0]
    return tagList[0]


def moveToTarget(target):
    dirList=os.listdir(target)
    for dir in dirList:
        if dir[-1].isdigit():
            source=os.path.join(target, dir)
            fileList=os.listdir(source)
            for file in fileList:
                shutil.move(os.path.join(source, file), os.path.join(target, file))
            os.rmdir(source)

def pxLogin():
    client = Client()
    client.login(USERNAME,PASSWORD)
    return client

def refresh(client=None):
    if client:
        client.authenticate(client.refresh_token)
        return client
    else:
        return pxLogin()

def removeBookmark(client,id):
    client=refresh(client)
    message=""
    try:
        client.delete_bookmark(id)
        message="Removed!"
    except:
        message="Something went wrong!"
    return message

def downloadImages(client,tags):
    client=refresh(client)
    target=Path.cwd() / 'Bookmarks'
    for id in tags:
        try:
            ill=client.fetch_illustration(id)
            ill.download(
                directory=target,
                size=Size.ORIGINAL,
                )
        except PixivError as e:
            print("Can't access ID:",id,"Reason:",e)
            print("Removing from database...")
            removeIllFromDb(id)
            pass
    moveToTarget(target)

def getTags(client):
    allTags=[]
    tagsDict=client.fetch_user_bookmark_tags(client.account.id, visibility=Visibility.PRIVATE, offset=None)
    if tagsDict['next']:
        while tagsDict['next']:
            sleep(1)
            allTags+=tagsDict['bookmark_tags']
            tagsDict=client.fetch_user_bookmark_tags(client.account.id, visibility=Visibility.PRIVATE, offset=tagsDict['next'])
        else:
            allTags+=tagsDict['bookmark_tags']
    else:
        allTags+=tagsDict['bookmark_tags']
    return allTags

def getAllIds():
    allIds=[]
    client=pxLogin()
    allTags=getTags()
    for tag in allTags:
        temp={}
        tempId=[]
        tagBM=getBookmarks(tag['name'],client)
        for bm in tagBM:
            tempId.append(bm.id)
        temp['name']=tag['name']
        temp['id']=tempId
        temp['count']=tag['count']
        allIds.append(temp)
    return allIds

def getBM(nextId=None,client=None,tag=None):
        client=refresh(client)
        bookmarks=client.fetch_user_bookmarks(client.account.id, visibility=Visibility.PRIVATE, max_bookmark_id=nextId,tag=tag)
        return bookmarks['illustrations'],bookmarks['next'],client
