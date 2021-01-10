import sys
from time import sleep, localtime
import random

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

PlayersReady = {}
n = 0


class ClientChannel(Channel):
    """
    This is the server representation of a connected client.
    """

    def __init__(self, *args, **kwargs):
        self.nickname = ""
        Channel.__init__(self, *args, **kwargs)

    def Close(self):
        self._server.DelPlayer(self)

    def Network_ListPlayers(self, data):
        self.Send({"action": "ListPlayers",
                   'ListPlayers': self._server.ListPlayers()})

    def Network_ReadyToPlay(self, data):
        global n
        n += 1
        self._server.SendToOthersR(
            {"ready": data["ready"], "who": self.nickname})
        PlayersReady[self.nickname] = data["ready"]
        if len(PlayersReady) == 2 and (n == 2 or n == 6):
            self._server.SendToAllP1({"P1": random.randint(1, 2)})
        if len(PlayersReady) == 2 and n == 4:
            self._server.SendToAllP1Bis({"P1": 0})

    def Network_BombDropped(self, data):
        self._server.SendToOthersB(
            {"bomb": data["bomb"], "screensize": data["screensize"],  "who": self.nickname})

    def Network_Touched(self, data):
        self._server.SendToOthersT(
            {"touched": data["touched"], "bomb": data["bomb"], "B": data["B"], "who": self.nickname})

    def Network_retry(self, data):
        self._server.SendToOthersRep(
            {"rep": data["rep"], "who": self.nickname})

    def Network_nickname(self, data):
        self.nickname = data["nickname"]
        self._server.PrintPlayers()
        self.Send({"action": "start"})
        self.Send({"action": "ListPlayers"})

    def Network_GameWinner(self, data):
        print(data['Winner'], "gagne la partie contre", data['Loser'])


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
        print("players' nicknames :", [p.nickname for p in self.players])

    def DelPlayer(self, player):
        global n
        print("Deleting Player " + player.nickname + " at "+str(player.addr))
        del self.players[player]
        if len(PlayersReady) != 0:
            del PlayersReady[player.nickname]
            n = 0

    def ListPlayers(self):
        return([p.nickname for p in self.players])

    def SendToAllP1(self, data):
        [p.Send({"action": "PlayerNumberOne", "P1": data["P1"], "listPlayers":[
                p.nickname for p in self.players], "nickname":p.nickname}) for p in self.players]

    def SendToAllP1Bis(self, data):
        [p.Send({"action": "PlayerNumberOneBis", "P1": data["P1"]})
         for p in self.players]

    def SendToOthersR(self, data):
        [p.Send({"action": "ReadyToPlay", "ready": data["ready"]})
         for p in self.players if p.nickname != data["who"]]

    def SendToOthersB(self, data):
        [p.Send({"action": "BombDropped", "bomb": data["bomb"], "screensize": data["screensize"]})
         for p in self.players if p.nickname != data["who"]]

    def SendToOthersT(self, data):
        [p.Send({"action": "Touched", "touched": data["touched"], "bomb": data["bomb"],
                 "B":data["B"]}) for p in self.players if p.nickname != data["who"]]

    def SendToOthersRep(self, data):
        [p.Send({"action": "retry", "rep": data["rep"]})
         for p in self.players if p.nickname != data["who"]]

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
