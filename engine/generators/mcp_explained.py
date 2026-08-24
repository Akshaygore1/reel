#!/usr/bin/env python3
"""MCP Explained — polished logical diagram and physical adapter rejection rig."""
import os, sys, math
from concurrent.futures import ProcessPoolExecutor
from PIL import Image, ImageDraw

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from blueprint_engine import (W,H,FPS,BG,AMBER,TEAL,BLUE,WHITE,MUTED,DIM,RED,GREEN,
    MONO,MONOB,SANS,SANSB,ease,alpha,lerp,track,finish,draw_caption_pill,
    draw_telemetry_hud,draw_blueprint_grid)
from diagram import (ServiceNode,draw_connector,draw_packet,draw_group,draw_protocol_bus,
    draw_step_badge,draw_prompt_bubble,draw_result_panel)

DURATION,TOTAL_FRAMES=18.0,540
BEAT_2,BEAT_3=162,324
CAPTIONS=[
 (0,"the model can reason — but today’s weather is not in its weights."),
 (90,"the host needs live context to answer this prompt."),
 (162,"custom integrations duplicate auth, schemas, and retry logic."),
 (270,"three proprietary plugs. three brittle failure surfaces."),
 (324,"MCP replaces one-off adapters with a shared protocol."),
 (405,"initialize → tools/list → tools/call is one inspectable flow."),
 (495,"structured result returns: 22°C · rain. answer grounded."),]

def header(d,intro):
    draw_blueprint_grid(d)
    d.rounded_rectangle([285,148,435,172],radius=12,fill=(18,14,20),outline=alpha(RED,intro*.75))
    d.ellipse([297,156,303,162],fill=alpha(RED,intro)); d.text((311,160),"@buildebugship",font=MONOB(12),fill=alpha(WHITE,intro),anchor="lm")
    track(d,(W/2,192),"CUSTOM ADAPTERS  vs  OPEN PROTOCOL",MONOB(11),alpha(MUTED,intro),sp=2,anchor="mm")
    t1,t2="MCP ","EXPLAINED"; w1,w2=d.textlength(t1,font=SANSB(40)),d.textlength(t2,font=SANSB(40)); sx=W/2-(w1+w2)/2
    d.text((sx,228),t1,font=SANSB(40),fill=alpha(WHITE,intro),anchor="lm"); d.text((sx+w1,228),t2,font=SANSB(40),fill=alpha(TEAL,intro),anchor="lm")
    d.text((W/2,266),"how AI apps connect to live tools without integration chaos",font=SANS(13),fill=alpha(BLUE,intro),anchor="mm")

def adapter_plug(d,cx,y,index,label,reject,opacity):
    col=(BLUE,AMBER,RED)[index]; x=cx+lerp(-70,0,ease((reject-20)/20)) if reject<40 else cx
    x+=math.sin(reject*1.8)*5 if 38<reject<65 else 0
    d.line([(x-84,y),(x-54,y)],fill=alpha(col,opacity),width=4)
    d.rounded_rectangle([x-54,y-23,x+4,y+23],radius=7,fill=(13,17,25),outline=alpha(col,opacity),width=2)
    for px,py in [(-7,0),(0,-8),(7,7)][:index+1]: d.rectangle([x+4,y+py-3,x+18+px/2,y+py+3],fill=alpha(col,opacity))
    d.rounded_rectangle([cx+30,y-27,cx+70,y+27],radius=9,fill=(8,11,17),outline=alpha(RED if reject>40 else DIM,opacity),width=2)
    if reject>48:
        d.line([(cx+39,y-10),(cx+61,y+10)],fill=alpha(RED,opacity),width=3); d.line([(cx+61,y-10),(cx+39,y+10)],fill=alpha(RED,opacity),width=3)
    d.text((cx,y+42),label,font=MONOB(9),fill=alpha(col,opacity),anchor="mm")

def draw_beat1(base,d,fr,a):
    host=ServiceNode(205,455,310,150,"AI HOST","Travel assistant · model ready","ai","waiting","LIVE CONTEXT: MISSING",{"user":"left","tool":"right"})
    draw_prompt_bubble(d,[48,480,185,552],"Should I pack an umbrella in Mumbai?",ease((fr-18)/18)*a)
    p=draw_connector(base,(185,516),host.layout().ports["user"],BLUE,reveal=ease((fr-40)/25))
    if fr>=42: draw_packet(base,p,(fr-42)/28,"prompt",BLUE,a)
    host.draw(base,a)
    d.rounded_rectangle([252,548,468,580],radius=8,fill=(8,11,17),outline=alpha(AMBER,a*.6)); d.text((360,564),"NO CURRENT FORECAST",font=MONOB(10),fill=alpha(AMBER,a),anchor="mm")
    for x in range(515,635,18): d.line([(x,530),(x+9,530)],fill=alpha(DIM,a),width=2)
    ServiceNode(535,460,137,120,"LIVE API","Mumbai weather","weather","neutral","UNREACHABLE",{"in":"left"}).draw(base,a*.7)

def draw_beat2(base,d,fr,a):
    ServiceNode(250,418,220,92,"AI HOST","three one-off SDKs","ai","failure","INTEGRATION DEBT",{"out":"bottom"}).draw(base,a)
    draw_group(d,[55,540,665,910],"CUSTOM ADAPTER WORKBENCH",RED,a)
    for i,(label,hit) in enumerate([("AUTH LAYER",181),("SCHEMA MAP",229),("RETRY LOOP",278)]):
        y=610+i*104; local=fr-(hit-28); col=(BLUE,AMBER,RED)[i]
        d.rounded_rectangle([80,y-30,225,y+30],radius=9,fill=(13,17,25),outline=alpha(col,a*.65),width=1)
        d.text((98,y-6),f"CUSTOM #{i+1}",font=MONOB(10),fill=alpha(WHITE,a),anchor="lm"); d.text((98,y+13),label,font=MONO(8),fill=alpha(MUTED,a),anchor="lm")
        adapter_plug(d,360,y,i,("OAuth ≠ key","array ≠ object","429 ≠ timeout")[i],local,a)
    if fr>285:
        pulse=.55+.45*math.sin(fr*.45); d.rounded_rectangle([170,866,550,900],radius=17,fill=(26,10,15),outline=alpha(RED,a*pulse),width=2)
        d.text((360,883),"✗ 3 ADAPTERS · 3 FAILURE SURFACES",font=MONOB(10),fill=alpha(RED,a*pulse),anchor="mm")

def flow_layout():
    return {"user":ServiceNode(44,470,126,102,"USER","umbrella?","user","request","PROMPT",{"out":"right"}),
      "host":ServiceNode(205,438,190,166,"AI HOST","MCP client inside","ai","protocol","CLIENT READY",{"in":"left","bus":"right","answer":"bottom"}),
      "server":ServiceNode(445,438,190,166,"WEATHER MCP","tool: get_forecast","server","protocol","TOOLS: 1",{"bus":"left","api":"right"}),
      "api":ServiceNode(562,685,126,112,"WEATHER API","live Mumbai feed","weather","success","200 OK",{"in":"top"})}

def draw_beat3(base,d,fr,a):
    nodes=flow_layout(); assemble=ease((fr-BEAT_3)/22); draw_group(d,[28,412,692,875],"STANDARDIZED MCP FLOW",TEAL,a*assemble)
    user_path=draw_connector(base,nodes["user"].layout().ports["out"],nodes["host"].layout().ports["in"],BLUE,reveal=assemble)
    mcp_path=draw_connector(base,nodes["host"].layout().ports["bus"],nodes["server"].layout().ports["bus"],TEAL,reveal=assemble)
    api_path=draw_connector(base,nodes["server"].layout().ports["api"],nodes["api"].layout().ports["in"],BLUE,waypoints=[(658,521),(658,650),(625,650)],reveal=assemble)
    draw_protocol_bus(d,[397,510,443,532],"MCP",a*assemble)
    for node in nodes.values(): node.draw(base,a*assemble)
    if fr<354: draw_packet(base,user_path,(fr-326)/25,"prompt",BLUE,a)
    for start,end,path,label,col,rev in [(342,374,mcp_path,"initialize",TEAL,False),(374,410,mcp_path,"tools/list",TEAL,False),(410,449,mcp_path,"tools/call",BLUE,False),(449,474,api_path,"GET /Mumbai",BLUE,False),(474,501,api_path,"22°C · rain",GREEN,True),(501,526,mcp_path,"result",GREEN,True)]:
        if start<=fr<end: draw_packet(base,path,(fr-start)/(end-start),label,col,a,reverse=rev)
    for x,(show,n,label) in zip((100,245,390,535),[(350,1,"initialize"),(386,2,"tools/list"),(422,3,"tools/call"),(505,4,"result")]):
        draw_step_badge(d,(x,828),n,label,GREEN if fr>=show else DIM,a*(1 if fr>=show else .4))
    if fr>=510: draw_result_panel(d,[205,620,515,688],"HOST ANSWER","Pack an umbrella · 22°C · rain",ease((fr-510)/16),GREEN)

def render(fr):
    base=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(base); intro,a=ease(fr/14),ease((fr-8)/18); header(d,intro)
    if a<=.01:return base
    if fr<BEAT_2:
        draw_telemetry_hud(d,"MODEL","reasoning","LIVE CONTEXT","missing",a,TEAL,AMBER); status,col="PROMPT ARRIVES · MODEL NEEDS CURRENT DATA",BLUE; draw_beat1(base,d,fr,a)
    elif fr<BEAT_3:
        draw_telemetry_hud(d,"ADAPTERS","3 custom","FAILURE SURFACES","3",a,RED,RED); status,col="AUTH · SCHEMA · RETRIES ARE REBUILT PER API",RED; draw_beat2(base,d,fr,a)
    else:
        draw_telemetry_hud(d,"PROTOCOL","MCP","TOOL RESULT","22°C · rain" if fr>=495 else "pending",a,TEAL,GREEN if fr>=495 else AMBER); status,col="USER → HOST/CLIENT → MCP → SERVER → LIVE API",GREEN; draw_beat3(base,d,fr,a)
    track(d,(W/2,390),status,MONOB(9),alpha(col,a),sp=1,anchor="mm"); draw_caption_pill(d,fr,CAPTIONS,a)
    if fr>510:
        o=ease((fr-510)/20); track(d,(W/2,1090),"ONE PROTOCOL · DISCOVERABLE TOOLS · STRUCTURED CONTEXT",MONOB(10),alpha(TEAL,o),sp=1,anchor="mm")
        track(d,(W/2,1112),"HOST  ·  CLIENT  ·  SERVER  ·  TOOLS  ·  RESOURCES",MONO(9),alpha(DIM,o),sp=2,anchor="mm")
    return base

def render_and_save_frame(args):
    fr,out_dir=args; finish(render(fr),fr).save(os.path.join(out_dir,f"f_{fr:04d}.png"))

if __name__=="__main__":
    out_dir=os.environ.get("TMP_FRAMES_DIR") or (sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].isdigit() else os.path.join(os.path.dirname(__file__),"..","..","output","frames_mcp_explained")); os.makedirs(out_dir,exist_ok=True)
    frames=[int(x) for x in sys.argv[1:] if x.isdigit()] or list(range(TOTAL_FRAMES))
    with ProcessPoolExecutor() as executor:list(executor.map(render_and_save_frame,[(fr,out_dir) for fr in frames]))
    print(f"Rendered MCP Explained frames: {len(frames)}")
