import sqlite3
from time import sleep
from PixivAPITools import getTags, getBM
from pixivapi import PixivError

"""connection.execute('''CREATE TABLE illustrations
     (id integer, pages int, primary key (id))''')
connection.execute('''CREATE TABLE illustrationTags
     (illustrationId integer, tagId int, UNIQUE (illustrationId,tagId))''')"""

def createConnection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except:
        print("Something went wrong!")
    finally:
        return conn

def createTagTable(connection):
    try:
        c=connection.cursor()
        c.execute('''CREATE TABLE tags
             (name text, count integer, primary key (name))''')
        connection.commit()
    except:
        print("Something went wrong!")

def fillTagTable(connection):
    try:
        allTags=getTags()
        for tag in allTags:
            c.execute("INSERT INTO tags VALUES (?,?)", (tag['name'],tag['count']))
        connection.commit()
    except:
        print("Something went wrong!")
        #return c
def createIllTable(connection):
    try:
        c=connection.cursor()
        c.execute('''CREATE TABLE illustrations
             (id integer, page_count integer, primary key (id))''')
    except:
        print("Something went wrong!")
def fillIllTable(connection,nextId=None,client=None):
    try:
        c=connection.cursor()
        allBM,nextId,client=getBM(nextId=nextId,client=client)
        if allBM:
            for bm in allBM:
                c.execute("INSERT INTO illustrations VALUES (?,?)", (bm.id,bm.page_count))
            connection.commit()
    except (sqlite3.Error, PixivError) as e:
        print(e)
    finally:
        return nextId,client

def fillIllTableSlowly(connection,client=None, nextId=None):
    count=0
    nextId,client=fillIllTable(connection,client=client)
    count+=30
    print(count,nextId)
    sleep(10)
    while nextId:
        nextId,client=fillIllTable(connection,nextId=nextId,client=client)
        sleep(10)
        count+=30
        print(count,nextId)
    """else:
        nextId,client=fillIllTable(connection,nextId=-1,client=client)
        count+=30
        print(count,nextId)"""
    connection.close()


def createBookmarksTable(connection):
    try:
        c=connection.cursor()
        c.execute('''CREATE TABLE bookmarks
             (id integer, name text, UNIQUE (id,name), foreign key (id) references illustrations (id),
             foreign key (name) references tags (name))''')
        connection.commit()
    except (sqlite3.Error, PixivError) as e:
        print(e)

def fillBookmarksTable(connection,tag,nextId=None,client=None):
    try:
        c=connection.cursor()
        allBM,nextId,client=getBM(nextId=nextId,client=client,tag=tag)
        if allBM:
            for bm in allBM:
                c.execute("INSERT INTO bookmarks VALUES (?,?)", (bm.id,tag))
            connection.commit()
    except (sqlite3.IntegrityError, PixivError) as e:
        print(e,"If it's a database error try updating Illustrations and / or Tags")
    finally:
        return nextId,client

def getAllTags(connection):
    tags=None
    c=connection.cursor()
    try:
        tags=c.execute("SELECT name FROM tags")
        tags=tags.fetchall()
    except:
        print("Table is empty or doesn't exist")
    return tags

def fillBookmarksTableSlowly(connection,client=None, nextId=None):
    tagList=getAllTags(connection)
    count=0
    for tag in tagList:
        nextId=None
        count+=1
        print(count,nextId,tag[0])
        nextId,client=fillBookmarksTable(connection,nextId=nextId,client=client, tag=tag[0])
        sleep(10)
        while nextId:
            print(count,nextId,tag[0])
            nextId,client=fillBookmarksTable(connection,nextId=nextId,client=client, tag=tag[0])
            sleep(10)
    connection.close()

def makeFilterQuery(tags):
    tagQ=len(tags)
    query="SELECT b1.id  FROM (SELECT * FROM bookmarks WHERE %) b1 INNER JOIN "
    search="SELECT * FROM bookmarks WHERE "
    plusConditions=""
    bookmarks=""
    idCondition="ON "
    for i,t in enumerate(tags):
        if t.startswith('-'):
            plusConditions+="name!=? AND "
        else:
            plusConditions+="name=? AND "
        if i == 0:
            bookmarks+=""
            idCondition+="b"+str(i+1)+".id"+"="+"b"+str(i+2)+".id "
        else:
            bookmarks+="(SELECT * FROM bookmarks WHERE %) b"+str(i+1)+' ,'
            idCondition+="AND b"+str(i+1)+".id"+"="+"b"+str(i+2)+".id "

    plusConditions=plusConditions[:-4]
    bookmarks=bookmarks[:-1]
    idCondition=idCondition[:-16]
    query=query+bookmarks+idCondition
    return query.replace("%",plusConditions)

    query="SELECT b1.id FROM bookmarks b1 INNER JOIN "
    bookmarks=""
    idCondition="ON "
    tagCondition=""
    for i,j in enumerate(tags):
        equal='='
        if j.startswith('-'):
            equal='!='
        if i == tagQ-1:
            #bookmarks+="bookmarks "+"b"+str(i+1)+" "
            #idCondition+=" "
            bookmarks+="bookmarks "+"b"+str(i+1)+" "
            tagCondition+="AND "+"b"+str(i+1)+".name"+equal+"? "
        else:
            if i==0:
                idCondition+="b"+str(i+1)+".id"+"="+"b"+str(i+2)+".id "
            else:
                bookmarks+="bookmarks "+"b"+str(i+1)+", "
                idCondition+="AND b"+str(i+1)+".id"+"="+"b"+str(i+2)+".id "
            tagCondition+="AND b"+str(i+1)+".name"+equal+"? "
    return query+bookmarks+idCondition+tagCondition

def filterDbTags(connection, tags=None):
    tagList=None
    try:
        tags=tags.split(' ')
    except:
        print("Tags have to be strings separated by a space")
        return tagList
    query=makeFilterQuery(tags)
    try:
        tags=[t.replace("-","") for t in tags]
        c=connection.cursor()
        tagList=c.execute(query,tags*len(tags))
    except:
        print("Couldn't find any matches in DB!")
    return tagList.fetchall()
