import sys
from time import sleep, localtime
import random

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

LenLP=0
ClassementPlayers=[]
LiveGame=[]
CreateGame=[]
PlayersReady={}
n=0
MaxPlayer=16

class ClientChannel(Channel):
    """
    This is the server representation of a connected client.
    """
    def __init__(self, *args, **kwargs):
        self.nickname = ""
        Channel.__init__(self, *args, **kwargs)
    
    def Close(self):
        self._server.DelPlayer(self)

    def Network_ListPlayers(self,data):
        self.Send({"action":"ListPlayers",'ListPlayers': self._server.ListPlayers(),'LiveGame': LiveGame})

    def Network_GoInTournament(self,data):
        global MaxPlayer
        self._server.GoInTournament()
        MaxPlayer=len([p.nickname for p in self._server.players])

    def Network_StopTournament(self,data):
        self._server.StopTournament({"hote":self.nickname})

    def Network_SendInvit(self,data):
        self._server.SendInvit({"To": data["To"], "From": self.nickname})

    def Network_RefInvit(self,data):
        self._server.RefInvit({"To": data["To"], "From": self.nickname})                               

    def Network_CreateGame(self,data):
        global LiveGame
        CreateGame.append((self.nickname,data["Adv"]))
        if len(CreateGame)%2==0:
            while CreateGame!=[]:
                for i in CreateGame:
                    for j in CreateGame:
                        if i[0]==j[1] and i[1]==j[0] and i!=j:
                            LiveGame.append({"J1":i[1],"J2":i[0],"S1":0,"S2":0,"J1R":"no","J2R":"no","BR1":3,"BR2":3,"etat":"EnCours","L":[i[1],i[0]]})
                            CreateGame.remove(i)
                            CreateGame.remove(j)
                            for a in self._server.players:
                                a.Send({"action":"Messages","msg":(i[1],"est","en","train","de","jouer","un","match","contre",i[0]),"fg":"firebrick" })

    def Network_ReadyToPlay(self,data):
        global n
        n+=1
        if LiveGame[data["ID"]]["J1"]==self.nickname:
            who=LiveGame[data["ID"]]["J2"]
        else:
            who=LiveGame[data["ID"]]["J1"]
        self._server.SendToOthersR({"who":who})
        if LiveGame[data["ID"]]["J1"]==self.nickname:
            LiveGame[data["ID"]]["J1R"]=data["ready"]
        if LiveGame[data["ID"]]["J2"]==self.nickname:
            LiveGame[data["ID"]]["J2R"]=data["ready"]
        if (LiveGame[data["ID"]]["S1"]+LiveGame[data["ID"]]["S2"])%2==0 and LiveGame[data["ID"]]["J1R"]=="yes" and LiveGame[data["ID"]]["J2R"]=="yes":
            self._server.SendToAllP1({"P1":random.randint(1,2),"ID":data["ID"]})
        if (LiveGame[data["ID"]]["S1"]+LiveGame[data["ID"]]["S2"])%2==1 and LiveGame[data["ID"]]["J1R"]=="yes" and LiveGame[data["ID"]]["J2R"]=="yes":
            self._server.SendToAllP1Bis({"ID":data["ID"]})
                  
    def Network_BombDropped(self, data):
        self._server.SendToOthersB({"bomb": data["bomb"], "screensize": data["screensize"], "ID":data["ID"], "who": self.nickname})

    def Network_Touched(self, data):
        global LiveGame
        self._server.SendToOthersT({"touched": data["touched"], "bomb": data["bomb"], "B":data["B"], "ID":data["ID"], "who": self.nickname})
        if data["touched"]=="Coulé" and LiveGame[data["ID"]]["J1"]==self.nickname:
            LiveGame[data["ID"]]["BR2"]-=1
            if LiveGame[data["ID"]]["BR2"]==0:
                LiveGame[data["ID"]]["S2"]+=1
                LiveGame[data["ID"]]["BR1"]=3
                LiveGame[data["ID"]]["BR2"]=3
                LiveGame[data["ID"]]["J1R"]="no"
                LiveGame[data["ID"]]["J2R"]="no"
        if data["touched"]=="Coulé" and LiveGame[data["ID"]]["J2"]==self.nickname:
            LiveGame[data["ID"]]["BR1"]-=1
            if LiveGame[data["ID"]]["BR1"]==0:
                LiveGame[data["ID"]]["S1"]+=1
                LiveGame[data["ID"]]["BR1"]=3
                LiveGame[data["ID"]]["BR2"]=3
                LiveGame[data["ID"]]["J1R"]="no"
                LiveGame[data["ID"]]["J2R"]="no"

    def Network_retry(self,data):
        self._server.SendToOthersRep({"rep": data["rep"], "ID":data["ID"], "who": self.nickname})        

    def Network_nickname(self, data):
        if len([p.nickname for p in self._server.players])>MaxPlayer:
            self.Send({"action":"quit"})
        self.nickname = data["nickname"]
        self.score=1000
        self._server.PrintPlayers()
        self.Send({"action":"start"})

    def Network_GameWinner(self, data):
        global LenLP
        LiveGame[data["ID"]]["etat"]="Fini"
        for g in self._server.players:
            if g.nickname==data["Winner"]:
                for p in self._server.players:
                    if p.nickname==data["Loser"]:
                        g.score=int(g.score+(100-(1/3)*(g.score-p.score)))
                        p.score=int(p.score-(100-(1/3)*(g.score-p.score)))
                        LenLP-=1
                        for a in self._server.players:
                            a.Send({"action":"Messages","msg":(data["Winner"],"a","gagné","le","match","contre",data["Loser"]),"fg":"purple" })

class MyServer(Server):
    channelClass = ClientChannel
    
    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.players = {}
        print('Server launched')
    
    def Connected(self, channel, addr):
        self.AddPlayer(channel)
    
    def AddPlayer(self, player):
        print("New Player connected")
        self.players[player] = True
 
    def PrintPlayers(self):
        print("players' nicknames :",[p.nickname for p in self.players])

    def DelPlayer(self, player):
        global n,LenLP,MaxPlayer,CreateGame,LiveGame
        print("Deleting Player " + player.nickname + " at "+str(player.addr))
        del self.players[player]
        if len(PlayersReady)!=0:
            del PlayersReady[player.nickname]
            n=0
        if len([p.nickname for p in self.players])==0:
            LenLP=0
            MaxPlayer=16
            CreateGame=[]
            LiveGame=[]

    def ListPlayers(self):
        global LenLP,ListPlayers
        if LenLP!=len(self.players) and [p.nickname for p in self.players][len([p.nickname for p in self.players])-1]!="" and len(self.players)<MaxPlayer+1:
            LenLP=len(self.players)
            ListPlayers=[]
            for p in self.players:
                ListPlayers.append((p.nickname,p.score))
        return sorted(ListPlayers, key=lambda ListPlayers: ListPlayers[1], reverse=True)

    def GoInTournament(self):
        [p.Send({"action":"GoInTournament"}) for p in self.players]

    def StopTournament(self,data):
        [p.Send({"action":"StopTournament","hote":data["hote"]}) for p in self.players]

    def SendInvit(self,data):
        [p.Send({"action":"InvitReceived","From": data["From"]}) for p in self.players if p.nickname == data["To"]]

    def RefInvit(self,data):
        [p.Send({"action":"InvitRefused","From": data["From"]}) for p in self.players if p.nickname == data["To"]]

    def SendToAllP1(self,data):
        for p in self.players:
            for a in LiveGame[data["ID"]]["L"]:
                if p.nickname==a:
                    p.Send({"action":"PlayerNumberOne", "P1": data["P1"],"ID":data["ID"]})

    def SendToAllP1Bis(self,data):
        for p in self.players:
            for a in LiveGame[data["ID"]]["L"]:
                if p.nickname==a:
                    p.Send({"action":"PlayerNumberOneBis","ID":data["ID"]})

    def SendToOthersR(self, data):
        [p.Send({"action":"ReadyToPlay"}) for p in self.players if p.nickname==data["who"]]
        
    def SendToOthersB(self, data):
        for p in self.players:
            for a in LiveGame[data["ID"]]["L"]:
                if p.nickname==a and a!=data["who"]:
                    p.Send({"action":"BombDropped","bomb": data["bomb"],"screensize": data["screensize"]})

    def SendToOthersT(self, data):
        for p in self.players:
            for a in LiveGame[data["ID"]]["L"]:
                if p.nickname==a and a!=data["who"]:
                    p.Send({"action":"Touched","touched": data["touched"], "bomb": data["bomb"], "B":data["B"]})

    def SendToOthersRep(self, data):
        for p in self.players:
            for a in LiveGame[data["ID"]]["L"]:
                if p.nickname==a and a!=data["who"]:
                    p.Send({"action":"retry", "rep" : data["rep"]})

    def Launch(self):
        while True:
            self.Pump()
            sleep(0.001)

# get command line argument of server, port
if len(sys.argv) != 2:
    print("Please use: python3", sys.argv[0], "host:port")
    print("e.g., python3", sys.argv[0], "localhost:31425")
else:
    host, port = sys.argv[1].split(":")
    s = MyServer(localaddr=(host, int(port)))
    s.Launch()
