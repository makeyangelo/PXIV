import sqlite3
from time import sleep
from PixivAPITools import getTags, getBM
from pixivapi import PixivError

DATABASE="BMDB.db"

def createConnection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
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
    query="""SELECT u.id,GROUP_CONCAT(ut.name) as tags
    FROM illustrations u
    LEFT JOIN bookmarks as ut ON u.id = ut.id
    LEFT JOIN tags t ON t.name=ut.name AND t.name IN ()
    GROUP BY u.id
    HAVING COUNT(ut.id) >= COUNT(t.name) AND COUNT(t.name) ="""
    if tags[-1].startswith("-"):
        tags[-1]="%"+tags[-1].replace('-','')+"%"
        query+=str(len(tags)-1)+" "
        values='?,'*(len(tags)-1)
        query.replace('()','('+values[:-1]+')')
        query+="AND NOT tags like ?"
        return query.replace('()','('+values[:-1]+')')
    else:
        query+=str(len(tags))
        values='?,'*len(tags)
        return query.replace('()','('+values[:-1]+')')

def getDbTags(tags):
    connection=createConnection(DATABASE)
    if tags.count('-')>1:
        print ("Only one - tag is supported")
        return None
    tagList=None
    try:
        tags=tags.split(' ')
    except:
        print("Tags have to be strings separated by a space")
        return tagList
    if len(tags)>1:
        tags.sort(reverse=True)
        query=makeFilterQuery(tags)
        try:
            tags=[t.replace("-","") for t in tags]
            c=connection.cursor()
            tagList=c.execute(query,tags)
        except:
            print("Couldn't find any matches in DB!")
            return None
        return [t[0] for t in tagList.fetchall()]
    else:
        if tags[0].startswith('-'):
            try:
                tags[0]="%"+tags[0].replace('-','')+"%"
                query="""SELECT f.id, f.tags FROM
                (SELECT u.id, GROUP_CONCAT(ut.name) as tags
                FROM illustrations as u
                LEFT JOIN bookmarks as ut ON u.id = ut.id
                GROUP BY u.id) f
                WHERE not f.tags like ? ORDER BY RANDOM() LIMIT 15"""
                c=connection.cursor()
                tagList=c.execute(query,tags)
            except:
                print("Couldn't find any matches in DB!")
                return None
            return [t[0] for t in tagList.fetchall()]
        else:
            try:
                c=connection.cursor()
                tagList=c.execute("SELECT id FROM bookmarks WHERE name=? ORDER BY RANDOM() LIMIT 15",tags)
            except:
                print("Couldn't find any matches in DB!")
                return None
            return [t[0] for t in tagList.fetchall()]
