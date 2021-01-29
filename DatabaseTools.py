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

def getAllDbTags(connection):
    c=connection.cursor()
    query="SELECT * FROM tags"
    tagList=c.execute(query)
    tagList=tagList.fetchall()
    if tagList:
        temp={}
        for t in tagList:
            temp[t[0]]=t[1]
        tagList=temp
    return tagList

def fillTagTable(client):
    connection=createConnection(DATABASE)
    c=connection.cursor()
    try:
        allTags=getTags(client)
        dbTags=getAllDbTags(connection)
        for tag in allTags:
            name=tag['name']
            count=tag['count']
            if not name in dbTags:
                print("Adding:",name)
                c.execute("INSERT INTO tags VALUES (?,?)", (name,count))
            elif count != dbTags[name]:
                print("Updating:",name)
                c.execute("UPDATE tags SET count=? WHERE name=?", (count,name))
        connection.commit()
        connection.close()
        print("The Tag table has been updated!")
    except (sqlite3.Error, PixivError) as e:
        print(e)
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
        #print(e)
        nextId=None
    finally:
        return nextId,client

def fillIllTableSlowly(client, nextId=None):
    connection=createConnection(DATABASE)
    count=0
    nextId,client=fillIllTable(connection,client=client)
    count+=30
    print(count,nextId)
    sleep(1)
    while nextId:
        nextId,client=fillIllTable(connection,nextId=nextId,client=client)
        sleep(1)
        count+=30
        print(count,nextId)
    print("The Illustrations table has been updated!")
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

#Gets every BM from every Tag to fill the table, better when table is empty
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

def fillBookmarksTableSlowly(connection,client, nextId=None):
    tagList=getAllTags(connection)
    count=0
    for tag in tagList:
        nextId=None
        count+=1
        print(count,"Out of",len(tagList),"Next id=",nextId,tag[0])
        nextId,client=fillBookmarksTable(connection,nextId=nextId,client=client, tag=tag[0])
        sleep(1)
        while nextId:
            print(count,nextId,tag[0])
            nextId,client=fillBookmarksTable(connection,nextId=nextId,client=client, tag=tag[0])
            sleep(1)
    connection.close()

def makeFilterQuery(tags,negTags):
    query="""SELECT u.id,u.page_count,GROUP_CONCAT(ut.name,'') as tags
    FROM illustrations u
    LEFT JOIN bookmarks as ut ON u.id = ut.id
    LEFT JOIN tags t ON t.name=ut.name AND t.name IN ()
    GROUP BY u.id
    HAVING COUNT(ut.id) >= COUNT(t.name) AND COUNT(t.name) ="""
    if tags[-1].startswith("-"):
        tags[-1]="%"+tags[-1].replace('-','')+"%"
        query+=str(len(tags)-negTags)+" "
        values='?,'*(len(tags)-negTags)
        query.replace('()','('+values[:-1]+')')
        query+="AND NOT tags like ? "*negTags
        return query.replace('()','('+values[:-1]+')')
    else:
        query+=str(len(tags))
        values='?,'*len(tags)
        return query.replace('()','('+values[:-1]+')')

def getDbTags(tags):
    connection=createConnection(DATABASE)
    negTags=tags.count('-')
    tagList=None
    try:
        tags=tags.split(' ')
    except:
        print("Tags have to be strings separated by a space")
        return tagList
    if len(tags)>1:
        tags.sort(reverse=True)
        query=makeFilterQuery(tags,negTags)
        try:
            for i,t in enumerate(tags):
                if t.startswith("-"):
                    tags[i]="%"+tags[i].replace('-','')+"%"
            c=connection.cursor()
            tagList=c.execute(query,tags)
            tagList=tagList.fetchall()
        except:
            print("Couldn't find any matches in DB!")
            return None
        connection.close()
        return [t[0] for t in tagList], sum([t[1] for t in tagList])
    else:
        if tags[0].startswith('-'):
            try:
                tags[0]="%"+tags[0].replace('-','')+"%"
                query="""SELECT f.id,f.page_count, f.tags FROM
                (SELECT u.id,u.page_count, GROUP_CONCAT(ut.name) as tags
                FROM illustrations as u
                LEFT JOIN bookmarks as ut ON u.id = ut.id
                GROUP BY u.id) f
                WHERE not f.tags like ? ORDER BY RANDOM() LIMIT 15"""
                c=connection.cursor()
                tagList=c.execute(query,tags)
                tagList=tagList.fetchall()
            except:
                print("Couldn't find any matches in DB!")
                return None
            connection.close()
            return [t[0] for t in tagList], sum([t[1] for t in tagList])
        else:
            try:
                query=makeFilterQuery(tags,[])
                c=connection.cursor()
                tagList=c.execute(query +" ORDER BY RANDOM() LIMIT 15",tags)
                tagList=tagList.fetchall()
            except:
                print("Couldn't find any matches in DB!")
                return None
            connection.close()
            return [t[0] for t in tagList], sum([t[1] for t in tagList])

def createDatabase():
    conn=createConnection(DATABASE)
    if conn:
        createTagTable(conn)
        createIllTable(conn)
        createBookmarksTable(conn)
        conn.close()

#Gets every illustration that doesnt have a bookmark entry already
#Better when you just want to add new BM to the DB
def updateBookmarksTable(client):
    connection=createConnection(DATABASE)
    c=connection.cursor()
    if c.execute("SELECT * FROM bookmarks limit 1").fetchall():
        print("")
        query="""SELECT u.id,GROUP_CONCAT(ut.name) as tags
                FROM illustrations u
                LEFT JOIN bookmarks as ut ON u.id = ut.id
                LEFT JOIN tags t ON t.name=ut.name
                GROUP BY u.id
                HAVING COUNT(ut.id) >= COUNT(t.name) AND tags is NULL"""
        ill=c.execute(query).fetchall()
        #ill=[i[0] for i in ill.fetchall()]
        total=len(ill)
        for c,i in enumerate(ill):
            print(c,"/",total)
            tags=client.fetch_bookmark(i[0])
            sleep(1)
            temp=[]
            for t in tags['tags']:
                if t['is_registered']:
                    temp.append(t['name'])
            for t in temp:
                print("Updating:",i[0],"with",t)
                c.execute("INSERT INTO bookmarks VALUES (?,?)", (i[0],t))
        connection.commit()
        print("Bookmarks Table has been updated!")
        connection.close()
    else:
        print("This might take a while depending on how many Bookmarks you have")
        fillBookmarksTableSlowly(connection,client)

def removeIllFromDb(id):
    connection=createConnection()
    c=connection.cursor()
    c.execute("DELETE FROM bookmarks WHERE id=?",id)
    c.execute("DELETE FROM illustrations WHERE id=?",id)
    connection.commit()
    connection.close()
