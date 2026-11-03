import requests
import json
import datetime
from websockets.sync.server import serve

class DataBase:
    BASE_URL = "https://api-statbotics.popcornpenguins.com/v3/"
    
    def __init__(self,url: str):
        self.BASE_URL = url
        
    def __init__(self):
        pass
    
    def request(self,query: str):
        return json.loads(requests.get(self.BASE_URL + query).content)

    def getTeam(self,teamNumber: int):
        return self.request("team/"+str(teamNumber))
    
    def getTeamMatches(self,teamNumber,year=datetime.datetime.now().year):
        return self.request("matches?team="+str(teamNumber)+"&"+"year="+str(year)+"&metric=time&ascending=false")
    
    def getTeamEvents(self,teamNumber,year=datetime.datetime.now().year):
        return self.request("team_events?team="+str(teamNumber)+"&"+"year="+str(year)+"&metric=time&ascending=false")
    
    def getNextMatch(self,teamNumber):
        matches = self.getTeamMatches(teamNumber)
        selectedMatch = None
        for match in matches:
            if match["status"] == "Completed":
                break
            selectedMatch = match
        return selectedMatch
    def getNextEvent(self,teamNumber):
            matches = self.getTeamEvents(teamNumber)
            selectedMatch = None
            for match in matches:
                if match["status"] == "Completed":
                    break
                selectedMatch = match
            return selectedMatch
    _teams = None
    def searchTeams(self, query, limit=8):
        if DataBase._teams is None:
            DataBase._teams = self.request("teams?")
        q = query.lower().strip()
        hits = [t for t in DataBase._teams if q in str(t["team"]) or q in t["name"].lower()]
        hits.sort(key=lambda t: (not str(t["team"]).startswith(q), t["team"]))
        return [{"team": t["team"], "name": t["name"]} for t in hits[:limit]]
db = DataBase()


class Connection:
    TeamNumber = None
    Websocket = None
    
    
    
    def SendData(self,dict):
        self.Websocket.send(json.dumps(dict))
        
    def GetNextMatch(self):
        
        if not self.TeamNumber:
             self.SendData({"Type":"NextMatch","Success":False,"Error":"No team number set"})
             return
        nextmatch = db.getNextMatch(self.TeamNumber)
        if not nextmatch:
            self.SendData({"Type":"NextMatch","Success":False,"Error":"No future matches found"})
            return
        self.SendData({"Type":"NextMatch","Success":True,"Data":nextmatch})
    
    def GetNextEvent(self):
            
            if not self.TeamNumber:
                 self.SendData({"Type":"NextEvent","Success":False,"Error":"No team number set"})
                 return
            nextmatch = db.getNextEvent(self.TeamNumber)
            if not nextmatch:
                self.SendData({"Type":"NextEvent","Success":False,"Error":"No future event found"})
                return
            self.SendData({"Type":"NextEvent","Success":True,"Data":nextmatch})
        
    def __init__(self,socket):
        self.Websocket = socket
        for request in self.Websocket:
            message = json.loads(request)
            match message["Type"]:
                case "GetTeamData":
                    self.SendData({
                        "Type":"TeamData",
                        "Data": db.getTeam(message["Team"]),
                        "Success": True
                    })
                case "GetNextMatch":
                    self.GetNextMatch()
                case "SetTeamNumber":
                    self.TeamNumber = message["Team"]
                case "GetMatches":
                    self.SendData({"Type":"Matches","Data":db.getTeamMatches(message["Team"]),"Success":True})
                case "GetEvents":
                    self.SendData({"Type":"Events","Data":db.getTeamEvents(message["Team"]),"Success":True})
                case "GetNextEvent":
                    self.GetNextEvent()
                case "SearchTeams":
                    self.SendData({"Type": "SearchResults", "Query": message["Query"],
                                "Data": db.searchTeams(message["Query"]), "Success": True})
                case "GetEventMatches":
                    self.SendData({"Type": "EventMatches", "Event": message["Event"],
                                "Data": db.request(f"matches?event={message['Event']}&limit=1000"),
                                "Success": True})

with serve(Connection, "localhost", 9119) as server:
        print("server running on ws://localhost:9119")
        server.serve_forever()

