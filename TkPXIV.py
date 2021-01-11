import tkinter as tk
from PIL import Image, ImageTk
import os, io, base64

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
OFFSET=0
IMAGE_GRID=[]

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
    for file in FILES:
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
                #print(count)
                ph=ImageTk.PhotoImage(Image.open(os.path.join(THUMBNAILS_FOLDER, FILES[count+last][:-3]+"png")))
                #IMAGE_GRID[r][c].configure(image=ph)
                IMAGE_GRID[r][c].configure(image=ph,text=r*6+c)
                IMAGE_GRID[r][c].text=(r,c)
                IMAGE_GRID[r][c].image=ph
                #IMAGE_GRID[r][c].bind("<<Button-"+str(r*6+c)+">>",
                # lambda e: NewWindow(IMAGE_GRID[r][c]))
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

class NewWindow(tk.Toplevel):
    id=0

    def __init__(self, master = None, id=0):

        super().__init__(master = master)
        self.id=id
        print(self.id)
        self.title(self.id)
        #self.geometry("200x200")
        #ph=ImageTk.PhotoImage(Image.open(os.path.join(BOOKMARKS_FOLDER, FILES[self.id[0]*6+self.id[1]])))
        ph=resizeTo(FILES[self.id],IMGSIZE)
        label = tk.Label(self, image =ph)
        label.image=ph
        label.pack()

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




window = tk.Tk()
window.title("TkPXIV")
window.geometry("1300x700")

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
        #frame.event_add('<<Algo-'+str(row*THUMBNAILS_PER_PAGE[0]+col)+'>>',"<Button-1>")
        #print(help(frame))
        button=tk.Button(master=frame, text=(row,col),command=lambda c=c:displayImage(c))
        #button.event_add('<<Algo-'+str(row*THUMBNAILS_PER_PAGE[0]+col)+'>>',"<Button-1>")
        """button.bind('<<Algo-'+str(row*THUMBNAILS_PER_PAGE[0]+col)+'>>',
         lambda e: NewWindow(frame,id=row*6+col))"""
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
searchIn=tk.Entry(master=controlsFrame, width=50)
searchIn.pack(side=tk.LEFT)
searchBttn=tk.Button(master=controlsFrame, height=BUTTON_SIZE[0], width=BUTTON_SIZE[1], text="Search")
searchBttn.pack(side=tk.LEFT)
idLabel=tk.Label(master=controlsFrame, text='idnumber')
idLabel.pack(side=tk.LEFT)
deleteBttn=tk.Button(master=controlsFrame, height=BUTTON_SIZE[0], width=BUTTON_SIZE[1], text="Delete")
deleteBttn.pack(side=tk.LEFT)


window.mainloop()
