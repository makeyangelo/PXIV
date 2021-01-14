"""https://pixiv-api.readthedocs.io/en/latest/"""
from pixivapi import Client, Size, Visibility
from pathlib import Path
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

def getBookmarks(tags, client):
    tags=tags.split(" ")
    tags.sort()
    allBM=[]
    allId=[]
    toRemove=[]
    for i in tags:
        if i.startswith('-'):
            bookmarks=client.fetch_user_bookmarks(client.account.id, visibility=Visibility.PRIVATE, tag=i[1:])
            if bookmarks['next'] is not None:
                while bookmarks['next'] is not None:
                    for img in bookmarks['illustrations']:
                        if img.id not in toRemove:
                            toRemove.append(img.id)
                    bookmarks=client.fetch_user_bookmarks(client.account.id, visibility=Visibility.PRIVATE, tag=i[1:], max_bookmark_id=bookmarks['next'])
                else:
                    for img in bookmarks['illustrations']: #Probar si esto rompe cuando no hay más
                        if img.id not in toRemove:
                            toRemove.append(img.id)
            else:
                for img in bookmarks['illustrations']: #Probar si esto rompe cuando no hay más
                    if img.id not in toRemove:
                        toRemove.append(img.id)

        else:
            tempList=[]
            bookmarks=client.fetch_user_bookmarks(client.account.id, visibility=Visibility.PRIVATE, tag=i)
            if bookmarks['next'] is not None:
                while bookmarks['next'] is not None:
                    for img in bookmarks["illustrations"]:
                        if img.id not in toRemove:
                            allBM.append(img)
                            tempList.append(img.id)
                    bookmarks=client.fetch_user_bookmarks(client.account.id, visibility=Visibility.PRIVATE, tag=i,max_bookmark_id=bookmarks['next'])
                else:
                    for img in bookmarks["illustrations"]:
                        if img.id not in toRemove:
                            allBM.append(img)
                            tempList.append(img.id)
            else:
                for img in bookmarks["illustrations"]:
                    if img.id not in toRemove:
                        allBM.append(img)
                        tempList.append(img.id)
            allId.append(tempList)

    if len(tags) >1:
        allId= filterTags(allId)
        alreadyIn=[]
        newBM=[]
        for i in allBM:
            if i.id in allId and (not i.id in alreadyIn):
                alreadyIn.append(i.id)
                newBM.append(i)
        return newBM

    else:
        return allBM

def pxLogin():
    client = Client()
    client.login(USERNAME,PASSWORD)
    return client

def refresh(client=None):
    try:
        client.authenticate(client.refresh_token)
        return client
    except:
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
    items=tags
    l=len(items)

    for link in items:
        ill=client.fetch_illustration(link)
        ill.download(
            directory=target,
            size=Size.ORIGINAL,
            )
    moveToTarget(target)

def getTags():
    allTags=[]
    client=pxLogin()
    tagsDict=client.fetch_user_bookmark_tags(client.account.id, visibility=Visibility.PRIVATE, offset=None)
    if tagsDict['next']:
        while tagsDict['next']:
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
