import tkinter as tk
from PIL import Image, ImageTk
import os, io, base64
import DatabaseTools as dbtools
import PixivAPITools as apitools

THUMBNAIL_SIZE=(200,200)
IMGSIZE=(800,800)
THUMBNAIL_PAD=(2,2)
THUMBNAILS_PER_PAGE=(3,6)
BUTTON_SIZE=(3,15)
BUTTON_PAD=5
BOOKMARKS_FOLDER=os.path.join(os.getcwd(),"Bookmarks")
THUMBNAILS_FOLDER=os.path.join(os.getcwd(),"Thumbnails")
FILES=os.listdir(BOOKMARKS_FOLDER)
CURRENT_FILES=len(FILES)
THUMBNAILS=os.listdir(THUMBNAILS_FOLDER)
CURRENT_THUMBNAILS=len(THUMBNAILS)
OFFSET=0
IMAGE_GRID=[]
client=None

def updateFileList():
    global FILES, CURRENT_FILES, THUMBNAILS, CURRENT_THUMBNAILS
    FILES=os.listdir(BOOKMARKS_FOLDER)
    CURRENT_FILES=len(FILES)
    THUMBNAILS=os.listdir(THUMBNAILS_FOLDER)
    CURRENT_THUMBNAILS=len(THUMBNAILS)

def round18(num):
    flag=0
    while (num>flag):
        flag+=18
    return flag-18

def getId(clickedImage):
    try:
        fileId=clickedImage.split(r'\''[:-1])[-1].split('.')
    except:
        return 0
    try:
        fileId=int(fileId[0])
    except:
        fileId=int(fileId[0].split("_")[0])
    return fileId

def makeThumbnails():
    updateFileList()
    if FILES:
        for file in FILES:
            if not file in THUMBNAILS:
                image=resizeTo(file,THUMBNAIL_SIZE)
                ImageTk.getimage(image).save(os.path.join(THUMBNAILS_FOLDER,file[:-3]+"png"))

def assignImage():
    count=0
    last=0
    if OFFSET>CURRENT_FILES:
        last=CURRENT_FILES-round18(CURRENT_FILES)
    last=OFFSET
    for r in range(THUMBNAILS_PER_PAGE[0]):
        for c in range(THUMBNAILS_PER_PAGE[1]):
            try:
                ph=ImageTk.PhotoImage(Image.open(os.path.join(THUMBNAILS_FOLDER, FILES[count+last][:-3]+"png")))
                IMAGE_GRID[r][c].configure(image=ph,text=r*6+c)
                IMAGE_GRID[r][c].text=(r,c)
                IMAGE_GRID[r][c].image=ph

            except:
                ph=ImageTk.PhotoImage(Image.open("imgthmb.png"))
                IMAGE_GRID[r][c].configure(image=ph)
                IMAGE_GRID[r][c].image=ph
                continue
            count+=1



def resizeTo(file,size):
    if file == "img.png":
        im=Image.open(file)
    else:
        im=Image.open(os.path.join(BOOKMARKS_FOLDER,file))
    cur_width, cur_height = im.size
    new_width, new_height = size
    scale = min(new_height / cur_height, new_width / cur_width)
    im = im.resize((int(cur_width * scale), int(cur_height * scale)),  Image.ANTIALIAS)
    return ImageTk.PhotoImage(im)

def nextPage():
    global OFFSET
    offset=OFFSET
    offset+=18
    if not offset > CURRENT_FILES:
        OFFSET=offset
        assignImage()

def prevPage():
    global OFFSET
    offset=OFFSET
    offset-=18
    if offset >= 0 and offset<OFFSET:
        OFFSET=offset
        assignImage()

def reset():
    global OFFSET
    for dir in FILES:
        try:
            os.remove(os.path.join(BOOKMARKS_FOLDER, dir))
            os.remove(os.path.join(THUMBNAILS_FOLDER, dir[:-3]+'png'))
        except:
            print("Reset failed!")
    OFFSET=0
    assignImage()

def displayImage(id):
    display=tk.Toplevel(window)
    display.title(id)
    try:
        ph=resizeTo(FILES[id+OFFSET],IMGSIZE)
    except:
        ph=ImageTk.PhotoImage(Image.open("img.png"))
    label=tk.Label(display,image=ph)
    label.image=ph
    label.pack()
    updateFileList()
    if CURRENT_FILES > id+OFFSET:
        id=getId(FILES[id+OFFSET])
        display.title(id)
        imageId.set(id)
    else:
        imageId.set("X")


def searchAndDownload():
    global client
    client=apitools.refresh(client)
    tags=searchTags.get()
    bm,total=dbtools.getDbTags(tags)
    r=input(str(len(bm))+" Illustrations with\n"+str(total)+" Images\nProceed? Y/n ")
    if r.lower() == "y":
        r=True
    else:
        r=False
    if not r:
        print("Download canceled!")
    elif not bm:
        print("No illustrations with those tags found!")
    else:
        apitools.downloadImages(client,bm)
        updateFileList()
        makeThumbnails()
        assignImage()

def resetIllustration():
    global client
    client=apitools.refresh(client)
    try:
        apitools.resetIllustration(client,imageId)
        dbtools.removeIllFromDb(imageId)
        print("Bookmark has been reset!")
    except:
        print("Something went wrong :(")

class Example(tk.Frame):
    """
    Base code by Jan Bodnar
    on www.zetcode.com"""
    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):

        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        fileMenu = tk.Menu(menubar)
        fileMenu.add_command(label="Make Thumbnails", command=self.onMakeThumbnails)
        databaseMenu = tk.Menu(menubar)
        databaseMenu.add_command(label="Create Database", command=self.onCreateDB)
        databaseMenu.add_command(label="Update Tags Table", command=self.onUpdateTagTable)
        databaseMenu.add_command(label="Update Illustrations Table", command=self.onUpdateIllTable)
        databaseMenu.add_command(label="Update Bookmarks Table", command=self.onUpdateBookmarkTable)
        menubar.add_cascade(label="File", menu=fileMenu)
        menubar.add_cascade(label="Database", menu=databaseMenu)


    def onMakeThumbnails(self):
        makeThumbnails()
        assignImage()
    def onCreateDB(self):
        if not os.path.exists("BMDB.db"):
            dbtools.createDatabase()
            print("Database created!")
        else:
            print("Database already exists!")
    def onUpdateIllTable(self):
        global client
        client=apitools.refresh(client)
        dbtools.fillIllTableSlowly(client)
    def onUpdateTagTable(self):
        global client
        client=apitools.refresh(client)
        dbtools.fillTagTable(client)
    def onUpdateBookmarkTable(self):
        global client
        client=apitools.refresh(client)
        dbtools.updateBookmarksTable(client)


window = tk.Tk()
window.title("TkPXIV")
window.geometry("1300x700")

menuBar=Example()

imageId=tk.IntVar()
imageId.set(0)
searchTags=tk.StringVar()
searchTags.set("")

#Create frames
imgFrame=tk.Frame()
imgFrame.pack()
controlsFrame=tk.Frame()
controlsFrame.pack()

#Create image buttons
c=0
for row in range(THUMBNAILS_PER_PAGE[0]):
    tempList=[]
    for col in range(THUMBNAILS_PER_PAGE[1]):
        frame = tk.Frame(master=imgFrame, borderwidth=1)
        frame.grid(row=row, column=col, padx=THUMBNAIL_PAD[0], pady=THUMBNAIL_PAD[1])
        button=tk.Button(master=frame, text=(row,col),command=lambda c=c:displayImage(c))
        button.pack()
        tempList.append(button)
        c+=1
    IMAGE_GRID.append(tempList)
assignImage()
#Create control buttons
prevBttn=tk.Button(master=controlsFrame, height=BUTTON_SIZE[0], width=BUTTON_SIZE[1], text="Prev", command=prevPage)
prevBttn.pack(side=tk.LEFT)
nextBttn=tk.Button(master=controlsFrame, height=BUTTON_SIZE[0], width=BUTTON_SIZE[1], text="Next",command=nextPage)
nextBttn.pack(side=tk.LEFT)
resetBttn=tk.Button(master=controlsFrame, height=BUTTON_SIZE[0], width=BUTTON_SIZE[1], text="Reset",command=reset)
resetBttn.pack(side=tk.LEFT)
searchIn=tk.Entry(master=controlsFrame, width=50,textvariable=searchTags)
searchIn.pack(side=tk.LEFT)
searchBttn=tk.Button(master=controlsFrame, height=BUTTON_SIZE[0], width=BUTTON_SIZE[1], text="Search", command=searchAndDownload)
searchBttn.pack(side=tk.LEFT)
idLabel=tk.Label(master=controlsFrame, textvariable=imageId)
idLabel.pack(side=tk.LEFT)
deleteBttn=tk.Button(master=controlsFrame, height=BUTTON_SIZE[0], width=BUTTON_SIZE[1], text="DeleteTags", command=resetIllustration)
deleteBttn.pack(side=tk.LEFT)



window.mainloop()
