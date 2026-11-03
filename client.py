from websockets.sync.client import connect
import json

def SendData(socket,data):
    socket.send(json.dumps(data))

with connect("ws://localhost:9119") as websocket:
    SendData(websocket, {"Type":"GetTeamData", "Team":11146})
    for request in websocket:
        message = json.loads(request)
        print(message)