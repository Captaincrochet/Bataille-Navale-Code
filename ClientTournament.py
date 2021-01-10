import sys
from time import sleep
from sys import stdin, exit
from math import *

from PodSixNet.Connection import connection, ConnectionListener
from tkinter import *
from PIL import Image,ImageTk

chemin='/Users/quentinblanchet/Documents/Etudes/CPBx2/Semestre 4/Informatique/Bataille Navale/'     #chemin d'accès aux images et PodSixNet

ListPoints=[]
def MakeListPoints():
    global X
    x=-X/10
    for i in range(5):
        x+=X/5
        y=-X/10
        for j in range(5):
            y+=X/5
            ListPoints.append((x,y))
    return ListPoints

nickname=""                     #nom joueur
Hote=""                         #nom hote
ListPlayers=[]                  #Liste joueurs contenant le nom, et le score de chacun
LiveDisplayClassement="yes"     #affichage du classement en direct ou non (fin de tournoi)
InvitSended=[]                  #Liste invitations envoyées
InvitReceived=[]                #Liste invitation reçues
MessagesReceived=[]             #Liste messages pour tchat en live
LiveGame=[]                     #Liste de toutes les parties, avec scores, gagnants, perdants, numéro d'ID, état...
ID=-1                           #Définition ID partie
LenMsgRcd=0                     #Longueur liste messages reçus
PhaseAttenteJoueurs=1           #1 => Attente connexion de tous les joueurs, 0 => Jouez
ETAT=-1                         #Etat du jeu : ETAT=0: Phase placement ou phase jeu; 
T=0                             #Variable d'état sur la main du jeu, 0=Pas moi; 1=Moi
Playing=0                       #Variable d'état de jeu

INITIAL=0
ACTIVE=1
DEAD=-1

#IMAGES
imgFG=Image.open(chemin+'oceanG.gif')
imgFD=Image.open(chemin+'oceanD.gif')
img=Image.open(chemin+'bateau.png')
img3=Image.open(chemin+'explosion.png')
imgC1=Image.open(chemin+'cloud1.png')
imgC2=Image.open(chemin+'cloud2.png')


class Client(ConnectionListener):
    
    def __init__(self, host, port):     #Initialisation, fenêtre d'entrée et demande de pseudo
        global nickname,MessagesReceived
        def clear_entry(event, entry):
            entry.delete(0, END)
        def sendPseudo(self):
            global nickname
            nickname=pseudo.get()
            if nickname!='' and nickname!='Inserez votre pseudo et appuyer sur Entrer':
                self.nickname=nickname
                MessagesReceived.append({"msg":("Bonjour",nickname,"et","bienvenue","sur","Titanic","The","Game"),"fg":"black"})
                connection.Send({"action":"nickname", "nickname": nickname})
                Accueil.destroy()
        self.Connect((host, port))
        self.state=INITIAL
        Accueil=Tk()
        Accueil.title('Titanic The Game')
        X=int(Accueil.winfo_screenwidth()*0.75)
        Y=X//2
        positionRight = int(Accueil.winfo_screenwidth()/2-X/2)  #Positioner la fenetre au milieu de l'écran
        positionDown = int(Accueil.winfo_screenheight()/2-Y/2)
        Accueil.geometry("+{}+{}".format(positionRight, positionDown))
        Wallpaper=Canvas(Accueil,width=X,height=Y,bd=0,highlightthickness=0)
        Wallpaper.pack()
        imgW=Image.open(chemin+'wallpaper.png')
        imgW=imgW.resize((X,Y))
        wallpaper=ImageTk.PhotoImage(imgW)
        Wallpaper.create_image(Y,Y//2,image=wallpaper)

        F=Frame(Accueil,highlightbackground="firebrick",highlightthickness=3)
        F.place(relx=0.5,rely=0.5,anchor=CENTER)
        pseudo=Entry(F,width=40)
        pseudo.pack(side=LEFT)
        pseudo.insert(0, 'Inserez votre pseudo')
        B=Button(F,text="Entrer")
        B.pack(side=RIGHT)
        
        pseudo.bind("<Button-1>", lambda event: clear_entry(event, pseudo))
        pseudo.bind("<Return>",sendPseudo)
        B.bind("<Button-1>",sendPseudo)
        Accueil.mainloop()
        self.Loop()
        
    def Network_connected(self, data):
        print("You are now connected to the server")
    
    def Loop(self):
        connection.Pump()
        self.Pump()

    def quit(self):
        Console.destroy()
        self.state=DEAD

    def close(self):
        global Playing,ID
        Plateau.destroy()
        Playing=0
        ID=-1

    def Network_quit(self,data):
        Console.destroy()
        self.state=DEAD
   
    def Network_start(self,data):
        global Plateau
        self.state=ACTIVE
        n=-1
        while self.state!=DEAD:   
            Console.update()
            PlateauStart.update()
            if Playing==1:
                Plateau.update()
            self.Loop()
            if n==-1:
                PlateauStart.destroy()
            if n==100:
                n=0
                self.Send({"action":"ListPlayers"})
            n+=1      
            sleep(0.001)
        exit()

    def Network_ListPlayers(self,data):
        global INFOS,ETAT,TextAttente,FATTENTE,FVALIDER,Valider,TextValider,nickname,nicknameAdversaire,NbPartiesGagnees
        global ListPlayers,LiveGame,InvitReceived,InvitSended,Playing,ID,frm,LenMsgRcd,LenListP
        ListPlayers=data["ListPlayers"]
        LiveGame=data["LiveGame"]
        RefreshTab()
        for a in InvitReceived:        #creation d'une partie si deux joueurs se sont invoyé une invitation mutuellement
            for b in InvitSended:
                if a==b:
                    c.Send({"action":"CreateGame","Adv":a})
                    InvitReceived.remove(a)
                    InvitSended.remove(a)
                    Plateau2Jeu()
                    Playing=1
                    SuppButtonsInvit()

        for i in range(len(LiveGame)):  #suppression de toutes les invitations d'un joueur en train de jouer
            if LiveGame[i]["etat"]=="EnCours":
                if LiveGame[i]["J1"]==nickname or LiveGame[i]["J2"]==nickname:
                    ID=i
                    InvitSended=[]
                    InvitReceived=[]
                else:
                    for a in InvitSended:
                        if a==LiveGame[i]["J1"]:
                            InvitSended.remove(LiveGame[i]["J1"])
                        if a==LiveGame[i]["J2"]:
                            InvitSended.remove(LiveGame[i]["J2"])
                    for a in InvitReceived:
                        if a==LiveGame[i]["J1"]:
                            InvitReceived.remove(LiveGame[i]["J1"])
                        if a==LiveGame[i]["J2"]:
                            InvitReceived.remove(LiveGame[i]["J2"])

        if Playing==1 and ID>-1:    #en jeu
            LPlayersGame=LiveGame[ID]["L"]
            for i in LPlayersGame:
                if i!=nickname:
                    nicknameAdversaire=i
                    NbPartiesGagnees.set("Manche(s) gagnée(s) : {}".format(GameWin)+"/"+format(GameWin+GameLose)+" contre "+format(nicknameAdversaire))
            if len(LPlayersGame)==2 and LPlayersGame[0]!="" and LPlayersGame[1]!="" and ETAT<0:#2joueurs, on place les bateaux
                ETAT=0
                animationNuages()
                
                FVALIDER=Frame(INFOS,bg="gold")
                TextValider=Label(FVALIDER,text="Placez vos bateaux, puis valider",bg="gold",fg="white")
                TextValider.pack()
                Valider=Button(FVALIDER,text='Valider',command=valider) #Valider les positions des bateaux et passer à la phase de jeu
                Valider.pack()
                FVALIDER.pack(side=TOP,fill='both', expand=True)

                Quitter.destroy()
                FQUITTER.destroy()
                    
                Bateaux.bind("<Button-1>",prendrebateau)    
                Bateaux.bind("<B1-Motion>",deplacerbateau)
                Bateaux.bind("<ButtonRelease-1>",corrigerpositions)
                Bateaux.bind('<Double-Button-1>',tournerbateau)

    def Network_GoInTournament(self,data):      #lancement du tournoi lorsque l'hôte le décide
        global PhaseAttenteJoueurs,MessagesReceived
        PhaseAttenteJoueurs=0
        MessagesReceived.append({"msg":("Le","tournoi","vient","de","commencer"),"fg":"red3"})

    def Network_StopTournament(self,data):      #fin du tournoi lorsque l'hôte le décide
        global PhaseAttenteJoueurs,MessagesReceived,LenMsgRcd,LiveDisplayClassement,FinalRanking
        PhaseAttenteJoueurs=-1
        SuppButtonsInvit()
        LiveDisplayClassement="no"
        FinalRanking=ListPlayers
        LenMsgRcd+=1
        if nickname==Hote and Playing!=1:
            MessagesReceived.append({"msg":("Vous","avez","décidé","de","mettre","fin","au","tounoi"),"fg":"black"})
        else:
            MessagesReceived.append({"msg":(Hote,"a","décidé","de","mettre","fin","au","tounoi"),"fg":"black"})
        MessagesReceived.append({"msg":("total","de",ListPlayers[0][1],"points","!"),"fg":"red3"})
        MessagesReceived.append({"msg":("Bravo","à",ListPlayers[0][0],",","notre","vainqueur","avec","un"),"fg":"red3"})   

    def Network_Messages(self,data):            #reception messages du serveur
        MessagesReceived.append({"msg":(data["msg"]),"fg":data["fg"]})

    def Network_InvitReceived(self,data):       #invitation reçues des adversaires
        n=0
        InvitReceived.append(data["From"])
        for i in InvitSended:
            if i==data["From"]:
                n+=1
        if n==0:
            MessagesReceived.append({"msg":(data["From"],"vous","a","envoyé","une","invitation"),"fg":"gold","display":"yes"})       

    def Network_InvitRefused(self,data):        #invitation refusées des adversaires
        InvitSended.remove(data["From"])
        MessagesReceived.append({"msg":(data["From"],"a","refusé","votre","invitation"),"fg":"orange"})     
                         
    def Network_ReadyToPlay(self,data):         #début d'une partie lorsque les deux joueurs sont connectés
        if Playing==1:
            global ETAT,FVALIDER
            global Score
            ETAT+=1
            if ETAT==2:
                Bombes.bind("<Button-1>",poserBombe)
                FVALIDER.destroy()
                Wait.destroy()
                Bateauxrestants.set("Bateaux adverses restants : {}".format(score))
                Score=Label(INFOS,textvariable=Bateauxrestants,fg="white")
                Score.pack(fill='both', expand=True)      

    def Network_PlayerNumberOne(self,data):     #joueur commençant choisi aléatoirement
        if Playing==1:
            global T,FLIGHT,Light
            if LiveGame[data["ID"]]["L"][data["P1"]-1]==nickname:
                T=1            
            FLIGHT=Frame(INFOS)#Voyant vert ou rouge en fonction de la main sur le jeu
            Light=Label(FLIGHT,text="",bg="firebrick")
            Light.pack(side=BOTTOM,fill='both', expand=True)
            FLIGHT.pack(side=BOTTOM,fill='both', expand=True)
            lightTour()   

    def Network_PlayerNumberOneBis(self,data):  #joueur perdant de la première partie commence
        if Playing==1:
            global FLIGHT,Light
            FLIGHT=Frame(INFOS)#Voyant vert ou rouge en fonction de la main sur le jeu
            Light=Label(FLIGHT,text="",bg="firebrick")
            Light.pack(side=BOTTOM,fill='both', expand=True)
            FLIGHT.pack(side=BOTTOM,fill='both', expand=True)
            lightTour()
                    
    def Network_BombDropped(self, data):
        if Playing==1:
            global GameWin,GameLose,BR,Score,T,Light,FRETRY,End,nicknameAdversaire
            n=0
            for i in PosBateaux:
                for j in PosBateaux[i]:
                    bomb=[k*(X//data["screensize"]) for k in data["bomb"]]
                    if j==bomb:
                        PosBateaux[i].remove(j)
                        PosBateauxTouchés[i].append(j)
                        Bateaux.create_image(data["bomb"],image=explosion)
                        n=1
                        if len(PosBateaux[i])==0:
                            c.Send({"action":"Touched","touched":"Coulé","bomb":data["bomb"],"B":i,"ID":ID})
                            del BateauxTireur[i]
                            BR-=1
                            if BR==0:
                                GameLose+=1
                                Score.destroy()
                                Light.destroy()
                                FLIGHT.destroy()
                                if (GameLose==2 and GameWin==0) or (GameLose==2 and GameWin==1):
                                    ScoreGameWin.destroy()
                                    End=Label(INFOS,text=("Vous","avez","perdu","le","match","contre",nicknameAdversaire),bg="firebrick",fg="white")
                                    End.pack(side=BOTTOM,fill='both', expand=True)
                                    
                                    FRETRY=Frame(FBOTTOM)
                                    Continu=Button(FRETRY,text='Quitter la partie',command=c.close)
                                    Continu.pack()
                                    FRETRY.pack(anchor="n")
                                else:
                                    #NbPartiesGagnees.set("Manche(s) gagnée(s) : {}".format(GameWin)+"/"+format(GameWin+GameLose)+" contre "+format(nicknameAdversaire))
                                    if GameLose==1 and GameWin==1:
                                        End=Label(INFOS,text="Vous avez perdu la manche. Une dernière manche vous départagera !",bg="firebrick",fg="white")
                                    else:
                                        End=Label(INFOS,text="Vous avez perdu la manche",bg="firebrick",fg="white")
                                    End.pack(side=BOTTOM,fill='both', expand=True)
                                    
                                    FRETRY=Frame(FBOTTOM)
                                    Continu=Button(FRETRY,text='Continuer la partie',command=retryY)
                                    Continu.pack()
                                    FRETRY.pack(anchor="n")
                                centrerFenetre(Plateau,1)
                        else:
                            c.Send({"action":"Touched","touched":"Touché","bomb":data["bomb"],"B":i,"ID":ID})
            (x,y)=data['bomb']
            if n==0 and verifierExplosion(x,y)==False:
                c.Send({"action":"Touched","touched":"Raté","bomb":data["bomb"],"B":"0","ID":ID})
                Bateaux.create_line(x-X/10,y-X/10,x+X/10,y+X/10,fill='firebrick')
                Bateaux.create_line(x-X/10,y+X/10,x+X/10,y-X/10,fill='firebrick')
                T=1
                lightTour()
            
    def Network_Touched(self, data):
        if Playing==1:
            global score,GameWin,GameLose,BateauxCoulés,T,Light,FRETRY,End,nicknameAdversaire
            (x,y)=data["bomb"]
            i=data["B"]
            if data["touched"]=="Coulé":
                T=1
                BateauxCoulés[i].append((x,y))
                afficherBateauCoulé(i)
                score-=1
                Bateauxrestants.set("Bateaux adverses restants : {}".format(score))
                if score==0:
                    T=0
                    GameWin+=1
                    Score.destroy()
                    Light.destroy()
                    FLIGHT.destroy()
                    if (GameLose==0 and GameWin==2) or (GameLose==1 and GameWin==2):
                        ScoreGameWin.destroy()
                        End=Label(INFOS,text=("Vous","avez","gagné","le","match","contre",nicknameAdversaire),bg="green",fg="white")
                        End.pack(side=BOTTOM,fill='both', expand=True)
                                    
                        FRETRY=Frame(FBOTTOM)
                        Continu=Button(FRETRY,text='Quitter la partie',command=c.close)
                        Continu.pack()
                        FRETRY.pack(anchor="n")
                        c.Send({"action":"GameWinner","Winner":nickname,"Loser":nicknameAdversaire,"ID":ID})
                    else:
                        #NbPartiesGagnees.set("Manche(s) gagnée(s) : {}".format(GameWin)+"/"+format(GameWin+GameLose)+" contre "+format(nicknameAdversaire))
                        if GameLose==1 and GameWin==1:
                            End=Label(INFOS,text="Vous avez gagné la manche. Une dernière manche vous départagera !",bg="green",fg="white")
                        else:
                            End=Label(INFOS,text="Vous avez gagné la manche",bg="green",fg="white")
                        End.pack(side=BOTTOM,fill='both', expand=True)
                                    
                        FRETRY=Frame(FBOTTOM)
                        Continu=Button(FRETRY,text='Continuer la partie',command=retryY)
                        Continu.pack()
                        FRETRY.pack(anchor="n")
                    centrerFenetre(Plateau,1)          
            if data['touched']=='Raté':
                Bombes.create_line(x-X/10,y-X/10,x+X/10,y+X/10,fill='firebrick')
                Bombes.create_line(x-X/10,y+X/10,x+X/10,y-X/10,fill='firebrick')
                lightTour()
            if data['touched']=='Touché':
                T=1
                Bombes.create_image(x,y,image=explosion)
                BateauxCoulés[i].append((x,y))

    def Network_retry(self,data):
        if Playing==1:
            global repM,repA
            repA=data["rep"]
            retry(repM,repA)        
        
    def Network_error(self, data):
        print('error:', data['error'][1])
        connection.Close()
    
    def Network_disconnected(self, data):
        print('Server disconnected')
        exit()
    
#########################################################

if len(sys.argv) != 2:
    print("Please use: python3", sys.argv[0], "host:port")
    print("E.g., python3", sys.argv[0], "localhost:31425")
    exit()

host, port = sys.argv[1].split(":")
c = Client(host, int(port))

#FONCTIONS

def lightTour():
    global T,Light,Score
    if T==1:
        Light.destroy()
        Light=Label(FLIGHT,text="C'est votre tour",bg="green",fg="white")
        Light.pack(side=BOTTOM,fill='both', expand=True)
        Score.config(bg="green")
    if T==0:
        Light.destroy()
        Light=Label(FLIGHT,text="Attendez votre tour",bg="firebrick",fg="white")
        Light.pack(side=BOTTOM,fill='both', expand=True)
        Score.config(bg="firebrick")

def plateau(Canvas):
    global X
    x=0
    for i in range(4):
        x+=X/5
        Canvas.create_line(x,0,x,X,fill='black')
        Canvas.create_line(0,x,X,x,fill='black')

def verifierExplosion(x,y):
    for i in PosBateauxTouchés:
            for j in PosBateauxTouchés[i]:
                if j==(x,y):
                    return True
    return False

def afficherBateauCoulé(i):
    global BateauxCoulés
    X=(BateauxCoulés[i][0][0]+BateauxCoulés[i][1][0])//2
    Y=(BateauxCoulés[i][0][1]+BateauxCoulés[i][1][1])//2
    if X==BateauxCoulés[i][0][0] and X==BateauxCoulés[i][1][0]: #Bateau Coulé est Vertical
        Bombes.create_image(X,Y,image=bateauv)
        Bombes.create_image(BateauxCoulés[i][0][0],BateauxCoulés[i][0][1],image=explosion)
        Bombes.create_image(BateauxCoulés[i][1][0],BateauxCoulés[i][1][1],image=explosion)
    if Y==BateauxCoulés[i][0][1] and Y==BateauxCoulés[i][1][1]: #Bateau Coulé est Horizontal
        Bombes.create_image(X,Y,image=bateauh)
        Bombes.create_image(BateauxCoulés[i][0][0],BateauxCoulés[i][0][1],image=explosion)
        Bombes.create_image(BateauxCoulés[i][1][0],BateauxCoulés[i][1][1],image=explosion)

def poserBombe(evt):
    global T,ListPoints
    n=0
    x=evt.x//(X/5)*X/5+X/10
    y=evt.y//(X/5)*X/5+X/10
    for i in ListPoints:
        if i==(x,y):
            n=1
    if T==1 and n==1:
        T=0
        animationMissile(x,y)
        ListPoints.remove((x,y))

def prendrebateau(evt):
    global CoordsInit,nB
    CoordsInit={'B1':Bateaux.coords(B1),'B2':Bateaux.coords(B2),'B3':Bateaux.coords(B3)}
    (x1,y1)=Bateaux.coords(B1)
    (x2,y2)=Bateaux.coords(B2)
    (x3,y3)=Bateaux.coords(B3)
    if evt.x>x1-X/10 and evt.x<x1+X/10 and evt.y>y1-X/5 and evt.y<y1+X/5:
        nB=B1
    elif evt.x>x2-X/10 and evt.x<x2+X/10 and evt.y>y2-X/5 and evt.y<y2+X/5:
        nB=B2
    elif evt.x>x3-X/10 and evt.x<x3+X/10 and evt.y>y3-X/5 and evt.y<y3+X/5:
        nB=B3

def deplacerbateau(evt):
    Bateaux.coords(nB,(evt.x,evt.y))

def corrigerpositions(evt): #Replace le bateau sur les cases
    global nB
    nB=0
    (x1,y1)=Bateaux.coords(B1)
    (x2,y2)=Bateaux.coords(B2)
    (x3,y3)=Bateaux.coords(B3)
    if SensBateaux['B1']=='vertical':
        (X1,Y1)=(round(x1//(X/5))*X/5+X/10,round(y1//(X/5))*(X/5))
    elif SensBateaux['B1']=='horizontal':
        (X1,Y1)=(round(x1//(X/5))*X/5,round(y1//(X/5))*X/5+X/10)
    if SensBateaux['B2']=='vertical':
        (X2,Y2)=(round(x2//(X/5))*X/5+X/10,round(y2//(X/5))*(X/5))
    elif SensBateaux['B2']=='horizontal':
        (X2,Y2)=(round(x2//(X/5))*X/5,round(y2//(X/5))*X/5+X/10)
    if SensBateaux['B3']=='vertical':
        (X3,Y3)=(round(x3//(X/5))*X/5+X/10,round(y3//(X/5))*X/5)
    elif SensBateaux['B3']=='horizontal':
        (X3,Y3)=(round(x3//(X/5))*X/5,round(y3//(X/5))*X/5+X/10)
    PosB['B1']=(X1,Y1)
    PosB['B2']=(X2,Y2)
    PosB['B3']=(X3,Y3)
    (X1,Y1)=corrigerpositions2(X1,Y1,'B1')
    (X2,Y2)=corrigerpositions2(X2,Y2,'B2')
    (X3,Y3)=corrigerpositions2(X3,Y3,'B3')
    Bateaux.coords(B1,(X1,Y1))
    Bateaux.coords(B2,(X2,Y2))
    Bateaux.coords(B3,(X3,Y3))
   
   
def corrigerpositions2(x,y,B): #Regarde si le bateau ne dépasse pas du cadre
    if SensBateaux[B]=='vertical':
        if x<=0:
            x=X/10
        if x>=X:
            x=X-X/10
        if y<=0:
            y=X/5
        if y>=X:
            y=X-X/5
    else:
        if x<=0:
            x=X/5
        if x>=X:
            x=X-X/5
        if y<=0:
            y=X/10
        if y>=X:
            y=X-X/10
    if superposition(B)==True:
        return(CoordsInit[B])
    else:
        return(x,y)

def superposition(B):
    if SensBateaux[B]=='vertical':
        (b1,b2)=((PosB[B][0],PosB[B][1]-X//10),(PosB[B][0],PosB[B][1]+X/10))
    else:
        (b1,b2)=((PosB[B][0]-X//10,PosB[B][1]),(PosB[B][0]+X//10,PosB[B][1]))
    for i in tuple(x for x in ('B1','B2','B3') if x != B):
        if SensBateaux[i]=='vertical':
            (i1,i2)=((PosB[i][0],PosB[i][1]-X//10),(PosB[i][0],PosB[i][1]+X/10))
        else:
            (i1,i2)=((PosB[i][0]-X//10,PosB[i][1]),(PosB[i][0]+X//10,PosB[i][1]))
        if b1==i1 or b1==i2 or b2==i1 or b2==i2:
            return True
    return False

def tournerbateau(evt): #Tourne le bateau de 90°
    (x1,y1)=Bateaux.coords(B1)
    (x2,y2)=Bateaux.coords(B2)
    (x3,y3)=Bateaux.coords(B3)
    if evt.x>x1-X/10 and evt.x<x1+X/10 and evt.y>y1-X/5 and evt.y<y1+X/5:
        B='B1'
        (x,y)=(x1,y1)
    if evt.x>x2-X/10 and evt.x<x2+X/10 and evt.y>y2-X/5 and evt.y<y2+X/5:
        B='B2'
        (x,y)=(x2,y2)
    if evt.x>x3-X/10 and evt.x<x3+X/10 and evt.y>y3-X/5 and evt.y<y3+X/5:
        B='B3'
        (x,y)=(x3,y3)
    tournerbateau2(x,y,B)

def tournerbateau2(x,y,B):
    global B1,B2,B3
    (b1,b2)=(x+X/10,y+X/10)
    if SensBateaux[B]=='vertical':
        if B=='B1':
            Bateaux.delete(B1)
            B1=Bateaux.create_image(b1,b2,image=bateauh)
            PosB['B1']=(b1,b2)
        if B=='B2':
            Bateaux.delete(B2)
            B2=Bateaux.create_image(b1,b2,image=bateauh)
            PosB['B2']=(b1,b2)
        if B=='B3':
            Bateaux.delete(B3)
            B3=Bateaux.create_image(b1,b2,image=bateauh)
            PosB['B3']=(b1,b2)
        SensBateaux[B]='horizontal'
    elif SensBateaux[B]=='horizontal':
        if B=='B1':
            Bateaux.delete(B1)
            B1=Bateaux.create_image(b1,b2,image=bateauv)
            PosB['B1']=(b1,b2)
        if B=='B2':
            Bateaux.delete(B2)
            B2=Bateaux.create_image(b1,b2,image=bateauv)
            PosB['B2']=(b1,b2)
        if B=='B3':
            Bateaux.delete(B3)
            B3=Bateaux.create_image(b1,b2,image=bateauv)
            PosB['B3']=(b1,b2)
        SensBateaux[B]='vertical'
    if superposition(B)==True:
        tournerbateau2(x,y,B)
    
def tournerimage(img): #Tourne une image à 90°
    (X,Y)=img.size
    if X>=Y:
        (X1,Y1)=(X,X)
    else:
        (X1,Y1)=(Y,Y)
    img=img.resize((X1,Y1))
    img=img.rotate(270)
    img=img.resize((Y,X))
    return(img)

def valider():
    global ETAT,FVALIDER,Valider,TextValider
    global Wait,Score
    Valider.destroy()
    TextValider.destroy()
    FVALIDER.destroy()
    ETAT+=1
    if ETAT==2:
        Bombes.bind("<Button-1>",poserBombe)
        Bateauxrestants.set("Bateaux adverses restants : {}".format(score))
        Score=Label(INFOS,textvariable=Bateauxrestants,fg="white")
        Score.pack(fill='both', expand=True)
    else:
        FVALIDER=Frame(INFOS)
        Wait=Label(FVALIDER,text="Votre adversaire place ses bateaux...",bg="gold",fg="white")
        Wait.pack(side=TOP,fill='both', expand=True)
        FVALIDER.pack(side=TOP,fill='both', expand=True)
    Bateaux.bind("<Button-1>")            
    Bateaux.unbind("<B1-Motion>")
    Bateaux.unbind("<ButtonRelease-1>")
    Bateaux.unbind("<Double-Button-1>")
    (x1,y1)=Bateaux.coords(B1)
    (x2,y2)=Bateaux.coords(B2)
    (x3,y3)=Bateaux.coords(B3)
    valider2(x1,y1,'B1')
    valider2(x2,y2,'B2')
    valider2(x3,y3,'B3')
    c.Send({"action":"ReadyToPlay","ready":"yes","ID":ID})

def valider2(x,y,B):
    if SensBateaux[B]=='vertical':
        PosBateaux[B].append([x,y-X/10])
        PosBateaux[B].append([x,y+X/10])
    else:
        PosBateaux[B].append([x-X/10,y])
        PosBateaux[B].append([x+X/10,y])
    BateauxTireur[B].append((x,y))

def bateauProcheMilieu():
    X=Y=0
    for i in BateauxTireur:
        if BateauxTireur[i][0][0]>X:
            X=BateauxTireur[i][0][0]
            Y=BateauxTireur[i][0][1]
    return(X,Y)

def tournerMissile(angle):
    imgM=Image.open(chemin+'missile.png')
    imgM=imgM.resize((int(X*0.1),int(X*0.1)))
    imgM=imgM.rotate(angle)
    missile=ImageTk.PhotoImage(imgM)
    return missile

def animationMissile(x2,y2):
    global dx,dy,n,X,M
    x2+=X
    (x1,y1)=bateauProcheMilieu()
    dx=x2-x1
    dy=y2-y1
    missile=tournerMissile(-(atan(dy/dx)*180/pi))
    M=Bateaux.create_image(x1,y1,image=missile)
    Bateaux.image=missile
    def animate(Canvas,M,xf):
        l=sqrt(2*11**2)/sqrt(dx**2+dy**2)
        DX=l*dx
        DY=l*dy
        x0,y0=Canvas.coords(M)
        Canvas.move(M,DX,DY)
        if x0>=xf:
            Canvas.delete(M)
            if xf==x2-X:
                Canvas.delete(M)
                c.Send({"action":"BombDropped","bomb":[x2-X,y2],"screensize":X,"ID":ID})
            else:
                M=Bombes.create_image(0,y0,image=missile)
                Bombes.image=missile
                animate(Bombes,M,x2-X)
        else:
            Canvas.after(15, animate, Canvas,M,xf)
    animate(Bateaux,M,Bateaux.winfo_width())

def animationNuages():
    global Bateaux,N1,N2,N3,N4,N5,N6,N7
    x=Bateaux.coords(N3)[0]
    Bateaux.move(N1,-8,0)
    Bateaux.move(N2,-8,0)
    Bateaux.move(N3,-8,0)
    Bateaux.move(N4,-8,0)
    Bateaux.move(N5,-8,0)
    Bateaux.move(N6,-8,0)
    Bateaux.move(N7,-8,0)
    if x<=-100:
        Bateaux.delete(N1)
        Bateaux.delete(N2)
        Bateaux.delete(N3)
        Bateaux.delete(N4)
        Bateaux.delete(N5)
        Bateaux.delete(N6)
        Bateaux.delete(N7)
    else:
        Bateaux.after(20, animationNuages)

def retryY():
    global repM,repA
    c.Send({"action":"retry","rep":"yes","ID":ID})
    repM="yes"
    retry(repM,repA)

def retry(rep1,rep2):
    global ETAT,T,FVALIDER,Valider,TextValider,FQUITTER,Quitter,GameWin
    
    if rep1=="yes" and rep2=="yes":
        ETAT=0
        if End['bg']=='firebrick' and GameWin==0:
            T=1
        for widget in Bateaux.winfo_children():
           widget.destroy()
        for widget in Bombes.winfo_children():
           widget.destroy()
        for widget in FRETRY.winfo_children():
           widget.destroy()
        FRETRY.destroy()
        Light.destroy()
        End.destroy()
        InitialisationVarFondBateauxNuages()
        animationNuages()
        
        FVALIDER=Frame(INFOS,bg="gold")
        TextValider=Label(FVALIDER,text="Placez vos bateaux, puis valider",bg="gold",fg="white")
        TextValider.pack()
        Valider=Button(FVALIDER,text='Valider',command=valider) #Valider les positions des bateaux et passer à la phase de jeu
        Valider.pack()
        FVALIDER.pack(side=TOP,fill='both', expand=True)
        centrerFenetre(Plateau,1) 

        Bateaux.bind("<Button-1>",prendrebateau)    
        Bateaux.bind("<B1-Motion>",deplacerbateau)
        Bateaux.bind("<ButtonRelease-1>",corrigerpositions)
        Bateaux.bind('<Double-Button-1>',tournerbateau)
        
    if rep2=="no":
        REPA="no"
        for widget in FRETRY.winfo_children():
           widget.destroy()
        FRETRY.destroy()
        
        FQUITTER=Frame(FBOTTOM)
        Text1=Label(FQUITTER,text='Votre adversaire a quitté la partie')
        Text1.pack()
        Ok=Button(FQUITTER,text='Ok',command=c.quit)
        Ok.pack()
        FQUITTER.pack()

    if rep1=="yes" and rep2==0:
        for widget in FRETRY.winfo_children():
           widget.destroy()
        Text1=Label(FRETRY,text="En attente d'une réponse de votre adversaire...")
        Text1.pack()
        centrerFenetre(Plateau,1) 
        
    if rep2=="yes" and rep1==0:
        for widget in FRETRY.winfo_children():
           widget.destroy()
        Continu=Button(FRETRY,text='Continuer la partie',command=retryY)
        Continu.pack()
        Text1=Label(FRETRY,text='Votre adversaire vous attend pour continuer')
        Text1.pack()
        centrerFenetre(Plateau,1) 

def geoliste(g):
        r=[i for i in range(0,len(g)) if not g[i].isdigit()]
        return [int(g[0:r[0]]),int(g[r[0]+1:r[1]]),int(g[r[1]+1:r[2]]),int(g[r[2]+1:])]

def centrerFenetre(Canvas,i):
    Canvas.update_idletasks()
    l,h,x,y=geoliste(Canvas.geometry())
    positionRight=(Canvas.winfo_screenwidth()-l)//2
    positionDown=(Canvas.winfo_screenheight()-h)//2
    if ((x==positionRight or y==positionDown) and i==1) or i==0:
        Canvas.geometry("+{}+{}".format(positionRight, positionDown))

def IsButton(x):
    for i in range(len(x)):
        if x[i-1]=='b' and x[i]=='u' and x[i+1]=='t' and x[i+2]=='t' and x[i+3]=='o' and x[i+4]=='n':
            return True

def SendInvit(To):
    global LenMsgRcd,MessagesReceived,InvitSended
    n=0
    if Playing==0:
        c.Send({"action":"SendInvit","To":To})
        InvitSended.append(To)
        for j in InvitReceived:
            if j==To:
                n+=1
        if n==0:
            MessagesReceived.append({"msg":("Vous","avez","envoyé","une","invitation","a",To),"fg":"green"})
        for i in range(len(MessagesReceived)-1,-1,-1):
            nbwordid=0
            for nbword in range(len(MessagesReceived[i]["msg"])):
                for ji in InvitReceived:
                    mot=MessagesReceived[i]["msg"][nbword]
                    if (mot==ji and ji==To and nbword==0) or (mot=="vous" and nbword==1) or (mot=="a" and nbword==2) or (mot=="envoyé" and nbword==3) or (mot=="une" and nbword==4) or (mot=="invitation" and nbword==5):
                        nbwordid+=1
                        if nbwordid==6 and MessagesReceived[i]["display"]=="yes":
                            MessagesReceived[i]["display"]="no"
                            LenMsgRcd+=1

def RefInvit(To):
    global LenMsgRcd,frm,InvitReceived
    if Playing==0:
        c.Send({"action":"RefInvit","To":To})
        for i in range(len(MessagesReceived)-1,-1,-1):
            nbwordid=0
            for nbword in range(len(MessagesReceived[i]["msg"])):
                for ji in InvitReceived:
                    mot=MessagesReceived[i]["msg"][nbword]
                    if (mot==ji and ji==To and nbword==0) or (mot=="vous" and nbword==1) or (mot=="a" and nbword==2) or (mot=="envoyé" and nbword==3) or (mot=="une" and nbword==4) or (mot=="invitation" and nbword==5):
                        nbwordid+=1
                        if nbwordid==6 and MessagesReceived[i]["msg"][0]==To and MessagesReceived[i]["display"]=="yes":
                            MessagesReceived[i]["display"]="no"
                            InvitReceived.remove(To)
                            LenMsgRcd+=1

def SuppButtonsInvit():
    for i in range(len(MessagesReceived)-1,-1,-1):
        nbwordid=0
        for nbword in range(len(MessagesReceived[i]["msg"])):
            for ji in InvitReceived:
                mot=MessagesReceived[i]["msg"][nbword]
                if (mot=="vous" and nbword==1) or (mot=="a" and nbword==2) or (mot=="envoyé" and nbword==3) or (mot=="une" and nbword==4) or (mot=="invitation" and nbword==5):
                    nbwordid+=1
                    if nbwordid==5 and MessagesReceived[i]["display"]=="yes":
                        MessagesReceived[i]["display"]="no"

def MsgConnPlayers():   #message de connexion et deconnexion de joueur
    global MessagesReceived,LenListP,P
    if len(ListPlayers)!=LenListP and (len(ListPlayers)-LenListP)>0:
        if (len(ListPlayers)-LenListP)==1:
            MessagesReceived.append({"msg":(ListPlayers[len(ListPlayers)-1][0],"a","rejoint","le","salon"),"fg":"purple"})
    elif len(ListPlayers)!=LenListP and (len(ListPlayers)-LenListP)<0:
        JoueurManquant=list(set(P)-set(ListPlayers))[0][0]
        if PhaseAttenteJoueurs>0:
            MessagesReceived.append({"msg":(JoueurManquant,"vient","de","quitter","le","salon"),"fg":"purple"})
        else:
            MessagesReceived.append({"msg":(JoueurManquant,"vient","de","se","déconnecter"),"fg":"purple"})
    P=ListPlayers
    LenListP=len(ListPlayers)
    
def AlreadyInvit(To):
    global MessagesReceived
    MessagesReceived.append({"msg":("Vous","avez","déjà","invité",To),"fg":"deeppink"})

def GoInTournament():
    c.Send({"action":"GoInTournament"})

def StopTournament():
    global MessagesReceived,LiveDisplayClassement,FinalRanking
    n=0
    m=0
    for i in LiveGame:
        if i["etat"]=="EnCours":
            n+=1
    for j in range(1,len(ListPlayers)):
        if ListPlayers[0][1]==ListPlayers[j][1]:
            m+=1
    if n==0 and m==0:
        c.Send({"action":"StopTournament"})
        LiveDisplayClassement="no"
        FinalRanking=ListPlayers
    elif n!=0:
        MessagesReceived.append({"msg":"qu'il y a des matchs en cours...","fg":"red2"})
        MessagesReceived.append({"msg":"Il n'est pas possible d'arrêter le tournoi tant","fg":"red2"})
    elif m!=0:
        MessagesReceived.append({"msg":"qu'il y a égalité avec le premier...","fg":"red2"})
        MessagesReceived.append({"msg":"Il n'est pas possible d'arrêter le tournoi tant","fg":"red2"})

def IsAnInvit(msg):
    nbwordid=0
    for nbword in range(len(msg["msg"])):
        for ji in InvitReceived:
            mot=msg["msg"][nbword]
            if (mot==ji and nbword==0) or (mot=="vous" and nbword==1) or (mot=="a" and nbword==2) or (mot=="envoyé" and nbword==3) or (mot=="une" and nbword==4) or (mot=="invitation" and nbword==5):
                nbwordid+=1
                if nbwordid==6 and msg["display"]=="yes":
                    return True
    return False

def RefreshTabClass():  #rafraichissement des données du classement des joueurs
    global Hote
    rang=1
    for widget in CCLASSEMENT.winfo_children():
        widget.destroy()

    if LiveDisplayClassement=="yes":
        Ranking=ListPlayers
        textClass="Classement"
    else:
        Ranking=FinalRanking
        textClass="Classement Final"

    cclas=Label(CCLASSEMENT,text=textClass,font='Verdana 14 bold underline')
    cclas.grid(row=0, column=0,columnspan=4,sticky=E+W)

    cnum=Label(CCLASSEMENT, text="Rang")
    cnum.grid(row=1, column=0,sticky=E+W)

    cname=Label(CCLASSEMENT, text="Joueurs")
    cname.grid(row=1, column=1,sticky=E+W)

    cscore=Label(CCLASSEMENT, text="Score")
    cscore.grid(row=1, column=2,sticky=E+W)

    for i in range(len(Ranking)):
        g='Verdana 14'
        if Ranking[i][0]==nickname:
            g='Verdana 14 bold'
        if i>0 and Ranking[i][1]==Ranking[i-1][1]:
            label=Label(CCLASSEMENT, text="-",font=g)
        elif i==0 or (i>0 and Ranking[i][1]!=Ranking[i-1][1]):
            label=Label(CCLASSEMENT, text=rang,font=g)
            rang+=1
        label.grid(row=i+2, column=0,sticky=E+W)

        label=Label(CCLASSEMENT, text=Ranking[i][0],font=g)
        label.grid(row=i+2, column=1,sticky=E+W)

        label=Label(CCLASSEMENT, text=Ranking[i][1],font=g)
        label.grid(row=i+2, column=2,sticky=E+W)

            
        if PhaseAttenteJoueurs==0:
            if nickname==Hote:
                btn=Button(CCLASSEMENT, text="Terminer le tournoi",command=StopTournament)
                btn.grid(row=100, column=0,columnspan=4,sticky=S+E+W)  
            for j in range(len(ListPlayers)):
                if ListPlayers[j][0]==nickname and ListPlayers[i][0]!=nickname and abs(ListPlayers[i][1]-ListPlayers[j][1])<=300:
                    if len(InvitSended)==0 and len(InvitReceived)==0:
                        n=0
                        for a in range(len(LiveGame)):
                            if (ListPlayers[i][0]==LiveGame[a]["J1"] or ListPlayers[i][0]==LiveGame[a]["J2"]) and LiveGame[a]["etat"]=="EnCours":
                                button=Button(CCLASSEMENT, text="En jeu")
                                n+=1
                        if n==0:
                            button=Button(CCLASSEMENT, text="Inviter",command=lambda To=ListPlayers[i][0]: SendInvit(To))
                        button.grid(row=i+2, column=3,sticky=E+W)
                    else:
                        n=0
                        for invitation in InvitReceived:
                            if invitation==ListPlayers[i][0]:
                                button=Button(CCLASSEMENT, text="Rejoindre",command=lambda To=ListPlayers[i][0]: SendInvit(To))
                                n+=1
                        for playersinvited in InvitSended:
                            if playersinvited==ListPlayers[i][0]:
                                button=Button(CCLASSEMENT, text="Invité",command=lambda To=ListPlayers[i][0]: AlreadyInvit(To))
                                n+=1
                        for a in range(len(LiveGame)):
                            if (ListPlayers[i][0]==LiveGame[a]["J1"] or ListPlayers[i][0]==LiveGame[a]["J2"]) and LiveGame[a]["etat"]=="EnCours":
                                button=Button(CCLASSEMENT, text="En jeu")
                                n+=1
                        if n==0:
                            button=Button(CCLASSEMENT, text="Inviter",command=lambda To=ListPlayers[i][0]: SendInvit(To))
                        button.grid(row=i+2, column=3,sticky=E+W)
                                                            

        elif nickname==ListPlayers[0][0] and len(ListPlayers)>1 and PhaseAttenteJoueurs>0:
            MsgConnPlayers()
            Hote=ListPlayers[0][0]
            label=Label(CCLASSEMENT, text=(len(ListPlayers),"joueurs","(16","max)"))
            label.grid(row=99, column=0,columnspan=4,sticky=S+E)
            label=Button(CCLASSEMENT, text="Appuyer pour commencer le tournoi",command=GoInTournament)
            label.grid(row=100, column=0,columnspan=4,sticky=S+E+W)                    
        elif PhaseAttenteJoueurs>0:
            MsgConnPlayers()
            Hote=ListPlayers[0][0]
            if len(ListPlayers)==1:
                label1=Label(CCLASSEMENT, text=(len(ListPlayers),"joueur","(16","max)"))
            else:
                label1=Label(CCLASSEMENT, text=(len(ListPlayers),"joueurs","(16","max)"))
            label1.grid(row=99, column=0,columnspan=4,sticky=S+E)

            if nickname==ListPlayers[0][0]:
                label=Label(CCLASSEMENT, text="Vous est l'hôte de la partie")
            else:
                label=Label(CCLASSEMENT, text=(ListPlayers[0][0],"est","l'hôte","de","la","partie"))
            label.grid(row=100, column=0,columnspan=4,sticky=S+E+W)
        MsgConnPlayers()

    Grid.columnconfigure(CCLASSEMENT, 1, weight=1)
    Grid.rowconfigure(CCLASSEMENT, 99, weight=1000)
    Grid.rowconfigure(CCLASSEMENT, 100, weight=1)

def RefreshTabInfos():  #rafraichissement des messages, invitations reçues, envoyées, refusées...
    global LenMsgRcd,frm,buttonValiderInvit,buttonRefuserInvit,frm
    if len(MessagesReceived)!=LenMsgRcd:
        LenMsgRcd=len(MessagesReceived)
        for widget in frm.winfo_children():
            widget.destroy()
        for i in range(len(MessagesReceived)-1,-1,-1):
            if IsAnInvit(MessagesReceived[i])==True:
                frm2=Frame(frm)
                message=Label(frm2,text=MessagesReceived[i]["msg"],fg=MessagesReceived[i]["fg"],font="Verdana 13")
                message.grid(row=len(MessagesReceived)-i, column=0,sticky=E+W)
                buttonValiderInvit=Button(frm2, text="✅",command=lambda To=MessagesReceived[i]["msg"][0]: SendInvit(To))
                buttonValiderInvit.grid(row=len(MessagesReceived)-i, column=1,sticky=E+W)
                buttonRefuserInvit=Button(frm2, text="❌",command=lambda To=MessagesReceived[i]["msg"][0]: RefInvit(To))#,buttonValiderInvit.forget(),buttonRefuserInvit.forget()])
                buttonRefuserInvit.grid(row=len(MessagesReceived)-i, column=2,sticky=E+W)
                frm2.grid(row=len(MessagesReceived)-i, column=0,sticky=N+E+W)
                Grid.columnconfigure(frm2, 0, weight=1)
            else: 
                message=Label(frm,text=MessagesReceived[i]["msg"],fg=MessagesReceived[i]["fg"],font="Verdana 13")
                message.grid(row=len(MessagesReceived)-i, column=0,sticky=N+E+W)
                                              
                
        frm.update()
        cnv.create_window(0, 0, window=frm, anchor=NW)
        cnv.configure(scrollregion=cnv.bbox(ALL))
        Grid.columnconfigure(cnv, 0, weight=1)
        CINFOS.grid(row=0,column=1,sticky=N+S+E+W)
        FCONSOLE.grid_columnconfigure(1, minsize=3.4/9*XCJ)

def RefreshTabMatch():  #rafraichissement des scores de tous les matchs en direct
    n=1
    for widget in CMATCHLIVE.winfo_children():
        widget.destroy()
    label=Label(CMATCHLIVE, text="Matchs en Direct",font="Verdana 14 bold underline")
    label.grid(row=0, column=0,sticky=E+W)
    for i in range(len(LiveGame)):
        if LiveGame[i]["etat"]=="EnCours":
            label=Label(CMATCHLIVE,text=(LiveGame[i]["J1"],LiveGame[i]["S1"],"-",LiveGame[i]["S2"],LiveGame[i]["J2"]),font="Verdana 15",bd=0,highlightthickness=2,highlightbackground="firebrick")
            label.grid(row=n,column=0,sticky=E+W)
            n+=1
    Grid.columnconfigure(CMATCHLIVE, 0, weight=1)

def RefreshTab():
    RefreshTabClass()
    RefreshTabInfos()
    RefreshTabMatch()
     
#JEU#############################################
def InitialisationVarFondBateauxNuages():   #définition de toutes les variable du jeu
    global repM,repA,REPA,ETAT,score,BR
    global SensBateaux,PosBateaux,BateauxTireur,PosBateauxTouchés,BateauxCoulés,PosB,ListPoints
    global Bateaux,Bombes,B1,B2,B3,N1,N2,N3,N4,N5,N6,N7
    global FQUITTER,Quitter,Plateau

    repM=0
    repA=0
    REPA=0
    score=3
    BR=3
        
    SensBateaux={'B1':'vertical','B2':'vertical','B3':'vertical'}
    PosBateaux={'B1':[],'B2':[],'B3':[]}
    BateauxTireur={'B1':[],'B2':[],'B3':[]}
    PosBateauxTouchés={'B1':[],'B2':[],'B3':[]}
    BateauxCoulés={'B1':[],'B2':[],'B3':[]}
    ListPoints=[]
    MakeListPoints()

    Bateaux.create_image(X/2,X/2,image=oceanG)
    Bombes.create_image(X/2,X/2,image=oceanD)
    plateau(Bateaux)
    plateau(Bombes)
    Bombes.create_line(0,0,0,X,fill='firebrick',width=5)
    Bateaux.create_line(X,0,X,X,fill='firebrick',width=5)

    B1=Bateaux.create_image(X/10,X/5,image=bateauv)
    B2=Bateaux.create_image(3*X/10,X/5,image=bateauv)
    B3=Bateaux.create_image(5*X/10,X/5,image=bateauv)
    PosB={'B1':Bateaux.coords(B1),'B2':Bateaux.coords(B2),'B3':Bateaux.coords(B3)}

    N1=Bateaux.create_image(X*0.4,X*0.65,image=nuage1)
    N2=Bateaux.create_image(X*0.2,X*0.4,image=nuage1)
    N3=Bateaux.create_image(X*0.8,X*0.75,image=nuage1)
    N4=Bateaux.create_image(X*0.8,X*0.2,image=nuage1)
    N5=Bateaux.create_image(X*0.7,X*0.45,image=nuage2)
    N6=Bateaux.create_image(X//3,X*0.85,image=nuage2)
    N7=Bateaux.create_image(X*0.3,X*0.15,image=nuage2)

    Bombes.create_image(X*0.4,X*0.65,image=nuage1)
    Bombes.create_image(X*0.2,X*0.4,image=nuage1)
    Bombes.create_image(X*0.8,X*0.75,image=nuage1)
    Bombes.create_image(X*0.8,X*0.2,image=nuage1)
    Bombes.create_image(X*0.7,X*0.45,image=nuage2)
    Bombes.create_image(X//3,X*0.85,image=nuage2)
    Bombes.create_image(X*0.3,X*0.15,image=nuage2)

def Plateau2JeuStart():     #nécéssaier pour démarrer, mais aucune idée de pourquoi il faut cette fonction
    global PlateauStart,img3
    PlateauStart=Toplevel()
    X=int(PlateauStart.winfo_screenwidth()*0.75)//2
    lC,hC,xC,yC=geoliste(Console.geometry())
    PlateauStart.geometry('0x0')
    img3=img3.resize((X//5,X//5))

def Plateau2Jeu():  #creation fenetre d'une partie de jeu
    global X, Plateau,INFOS,P,Bateaux,Bombes,FBOTTOM,ScoreGameWin,FQUITTER,Quitter,Playing,ETAT,GameWin,GameLose
    global imgFG,imgFD,img,img3,imgC1,imgC2,oceanG,oceanD,bateauv,bateauh,explosion,nuage1,nuage2
    global Bateauxrestants,NbPartiesGagnees,nicknameAdversaire
    global InitialisationVarFondBateauxNuages

    ETAT=-1
    Playing=1
    GameWin=0
    GameLose=0

    Plateau=Toplevel()
    Plateau.title('Titanic the game')
    X=int(Plateau.winfo_screenwidth()*0.75)//2
    lC,hC,xC,yC=geoliste(Console.geometry())
    Plateau.geometry("+{}+{}".format(xC, yC))

    #IMAGES
    imgFG=imgFG.resize((X,X))
    oceanG=ImageTk.PhotoImage(imgFG)
    imgFD=imgFD.resize((X,X))
    oceanD=ImageTk.PhotoImage(imgFD)

    img=img.resize((int((img.size[0]*((14*X)/45))/img.size[1]),int(((14*X)/40))))
    img2=tournerimage(img)
    bateauv=ImageTk.PhotoImage(img)
    bateauh=ImageTk.PhotoImage(img2)

    img3=img3.resize((X//5,X//5))
    explosion=ImageTk.PhotoImage(img3)

    imgC1=imgC1.resize((int((imgC1.size[0]*(X//5)/imgC1.size[1])),X//5))
    imgC2=imgC2.resize((int((imgC2.size[0]*(X//4)/imgC2.size[1])),X//4))
    nuage1=ImageTk.PhotoImage(imgC1)
    nuage2=ImageTk.PhotoImage(imgC2)

    #INFORMATIONS
    Bateauxrestants=StringVar()
    NbPartiesGagnees=StringVar()
    #NbPartiesGagnees.set("Manche(s) gagnée(s) : {}".format(GameWin)+"/"+format(GameWin+GameLose)+" contre "+format(nicknameAdversaire))

    INFOS=Frame(Plateau)
    INFOS.pack(side=TOP,fill='both', expand=True)

    #PLATEAU
    P=Frame(Plateau)
    P.pack()

    #CARTE BATEAU
    Bateaux=Canvas(P,width=X, height=X,bd=0,highlightthickness=0)
    Bateaux.pack(side=LEFT)

    #CARTE BOMBE
    Bombes=Canvas(P,width=X, height=X,bd=0,highlightthickness=0)
    Bombes.pack(side=RIGHT)

    #AFFICHAGE BAS
    FBOTTOM=Frame(Plateau)

    ScoreGameWin=Label(FBOTTOM,textvariable=NbPartiesGagnees)
    ScoreGameWin.pack(anchor='w')

    FQUITTER=Frame(FBOTTOM)
    Quitter=Button(FQUITTER,text='Quitter la partie', command=c.close)
    Quitter.pack()
    FQUITTER.pack(anchor='n')

    FBOTTOM.pack(side=BOTTOM,fill='both', expand=True)
    
    InitialisationVarFondBateauxNuages()

#CONSOLE#########################################
def Console2Jeu():  #creation fenetre console, salon de jeu
    global Console,FCONSOLE,CCLASSEMENT,CINFOS,CMATCHLIVE,LenMsgRcd,frm,cnv,XCJ,YCJ
    global ListPlayers,nickname,LenListP,P
    global Playing,RefreshTabClass,RefreshTabInfos,RefreshTabMatch

    Console=Tk()
    Console.title('Titanic The Game')
    XCJ=int(Console.winfo_screenwidth()*0.75)
    YCJ=XCJ//2
    LenListP=-1
    P=[]

    FCONSOLE=Frame(Console,bd=0,highlightthickness=0)

    #CLASSEMENT
    CCLASSEMENT=Frame(FCONSOLE,width=2.8/9*XCJ,height=YCJ,bd=0,highlightthickness=2,highlightbackground="grey")
    CCLASSEMENT.grid(row=0,column=0,sticky=N+S+E+W)
    FCONSOLE.grid_columnconfigure(0, minsize=2.8/9*XCJ)

    #INFORMATIONS - TCHAT CENTRAL
    CINFOS=Frame(FCONSOLE,width=3.4/9*XCJ,height=YCJ,bd=0,highlightthickness=2,highlightbackground="grey")
    CINFOS.grid_rowconfigure(0, weight=1)
    CINFOS.grid_columnconfigure(0, weight=1)
    cnv=Canvas(CINFOS)
    cnv.grid(row=0,column=0,sticky=N+S+E+W)

    vScroll=Scrollbar(CINFOS, orient=VERTICAL, command=cnv.yview)
    vScroll.grid(row=0, column=1, sticky='ns')

    cnv.configure(yscrollcommand=vScroll.set)
    frm = Frame(cnv)

    CINFOS.grid(row=0,column=1,sticky=N+S+E+W)
    FCONSOLE.grid_columnconfigure(1, minsize=3.4/9*XCJ)

    #MATCHS EN LIVE
    CMATCHLIVE=Frame(FCONSOLE,width=2.8/9*XCJ,height=YCJ,bd=0,highlightthickness=2,highlightbackground="grey")
        
    CMATCHLIVE.grid(row=0,column=2,sticky=N+S+E+W)
    FCONSOLE.grid_columnconfigure(2, minsize=2.8/9*XCJ)
    FCONSOLE.grid_rowconfigure(0, minsize=YCJ)

    CQUITTER=Frame(FCONSOLE,width=XCJ,bd=0,highlightthickness=0,bg='grey')
    Quitter=Label(CQUITTER,text='Quitter le tournoi', bg='grey',fg='white')
    Quitter.pack()
    Quitter.bind("<Button-1>",lambda event: c.quit())
    CQUITTER.grid(row=1,column=0,columnspan=3,sticky=N+S+E+W)

    FCONSOLE.pack(expand=True,fill='both')

    centrerFenetre(Console,0)
    Plateau2JeuStart()

Console2Jeu()

c.Loop()
