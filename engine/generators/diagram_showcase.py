#!/usr/bin/env python3
"""Static component showcase for visual QA of the shared diagram system."""
import os,sys
from PIL import Image,ImageDraw
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..")))
from blueprint_engine import W,H,BG,BLUE,TEAL,GREEN,RED,AMBER,WHITE,MUTED,MONOB
from diagram import ServiceNode,draw_connector,draw_packet,draw_group,draw_protocol_bus,draw_result_panel

def render():
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im); d.text((40,50),"DIAGRAM SYSTEM · COMPONENT SHOWCASE",font=MONOB(18),fill=WHITE)
    nodes=[]
    kinds=[("AI Host with an intentionally very long title","multi-line subtitle wraps without touching borders","ai","request"),("MCP Client","protocol negotiation","client","protocol"),("Weather Server","tools/list · tools/call","server","waiting"),("Live API","22°C · rain","weather","success"),("Files","resources","files","neutral"),("Database","query tool","database","failure")]
    for i,(title,sub,icon,state) in enumerate(kinds):
        x=40+(i%2)*335; y=130+(i//2)*160; nodes.append(ServiceNode(x,y,300,122,title,sub,icon,state,state.upper(),{"in":"left","out":"right"}))
    # connectors below nodes and in every cardinal direction
    for a,b,col in [(nodes[0],nodes[1],BLUE),(nodes[2],nodes[3],TEAL),(nodes[4],nodes[5],RED)]:
        draw_connector(im,a.layout().ports["out"],b.layout().ports["in"],col)
    for node in nodes: node.draw(im)
    draw_group(d,[40,640,680,940],"GROUP + PROTOCOL + RESULT",TEAL)
    draw_protocol_bus(d,[90,715,630,749],"MCP · JSON-RPC")
    p=draw_connector(im,(120,800),(600,860),GREEN,waypoints=[(360,800),(360,860)])
    draw_packet(im,p,.55,"structured result",GREEN)
    draw_result_panel(d,[180,890,540,960],"RESULT","22°C · rain",1,GREEN)
    d.text((40,1030),"COLOR STATES  blue=request  amber=waiting  red=failure",font=MONOB(10),fill=MUTED)
    return im

if __name__=="__main__":
    out=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(__file__),"..","..","output","diagram_showcase.png")
    os.makedirs(os.path.dirname(os.path.abspath(out)),exist_ok=True); render().save(out); print(out)
