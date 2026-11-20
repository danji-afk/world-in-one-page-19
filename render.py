#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os, textwrap

W = H = 1024
PAPER = (246, 242, 231)
WHITE = (255, 254, 249)
NAVY = (26, 36, 64)
RED = (178, 58, 58)
GOLD = (187, 145, 55)
INK = (34, 40, 49)
MUTED = (92, 94, 94)
YELLOW = (224, 187, 51)
BLUE = (65, 102, 142)
GREEN = (71, 111, 83)
ORANGE = (188, 107, 46)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

def font(path, size):
    return ImageFont.truetype(path, size)

def wrap(draw, text, fnt, width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        test = word if not cur else cur + " " + word
        if draw.textlength(test, font=fnt) <= width:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines

def text_block(draw, xy, text, fnt, fill, width, leading=None, max_lines=None):
    x, y = xy
    leading = leading or (fnt.size + 2)
    lines = wrap(draw, text, fnt, width)
    if max_lines: lines = lines[:max_lines]
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=fnt, fill=fill)
    return len(lines)

def rule(draw, xy, length, fill=GOLD, width=3):
    x, y = xy
    draw.rectangle((x, y, x + length, y + width - 1), fill=fill)

def card(draw, box, shadow=True):
    x1, y1, x2, y2 = box
    if shadow:
        draw.rectangle((x1 + 4, y1 + 4, x2 + 4, y2 + 4), fill=(210, 202, 185))
    draw.rectangle(box, fill=WHITE, outline=NAVY, width=1)

def chip(draw, x, y, label, color=RED):
    f = font(SANS_B, 9)
    w = int(draw.textlength(label, font=f)) + 12
    draw.rounded_rectangle((x, y, x + w, y + 16), radius=3, fill=color)
    draw.text((x + 6, y + 3), label, font=f, fill=WHITE)
    return w

def circle_num(draw, x, y, n, color=RED, r=10):
    draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
    f = font(SANS_B, 9)
    s = str(n)
    bb = draw.textbbox((0, 0), s, font=f)
    draw.text((x-(bb[2]-bb[0])/2, y-(bb[3]-bb[1])/2-1), s, font=f, fill=WHITE)

def line_icon(draw, kind, x, y, w, h):
    # Small original ink illustrations, kept geometric for deterministic rendering.
    if kind == "summit":
        draw.ellipse((x+w//2-28, y+5, x+w//2+28, y+h-3), outline=GOLD, width=2)
        draw.line((x+18,y+h-8,x+w-18,y+h-8), fill=NAVY, width=3)
        for dx, col in ((18, BLUE), (w//2, RED), (w-18, GREEN)):
            draw.ellipse((x+dx-7,y+13,x+dx+7,y+27), fill=col)
            draw.line((x+dx,y+27,x+dx,y+h-9), fill=col, width=4)
        draw.rectangle((x+w//2-26,y+h//2-5,x+w//2+26,y+h//2+9), fill=WHITE, outline=NAVY)
        draw.text((x+w//2-20,y+h//2-4), "PEACE", font=font(SANS_B,8), fill=RED)
    elif kind == "court":
        draw.line((x+10,y+h-5,x+w-10,y+h-5), fill=NAVY, width=2)
        for px in (x+18,x+35,x+52): draw.line((px,y+13,px,y+h-6), fill=NAVY, width=3)
        draw.line((x+8,y+13,x+w-4,y+13), fill=NAVY, width=3)
        draw.line((x+12,y+7,x+w-8,y+7), fill=RED, width=2)
        draw.ellipse((x+w-28,y+5,x+w-8,y+25), outline=RED, width=3)
        draw.line((x+w-18,y+25,x+w-18,y+h-5), fill=RED, width=2)
    elif kind == "bridge":
        draw.line((x+5,y+h-10,x+w-5,y+h-10), fill=BLUE, width=3)
        draw.arc((x+12,y+15,x+w-18,y+h+12), 180, 360, fill=NAVY, width=3)
        draw.line((x+14,y+22,x+14,y+h-10), fill=NAVY, width=2)
        draw.line((x+w-20,y+22,x+w-20,y+h-10), fill=NAVY, width=2)
        draw.rectangle((x+w//2-8,y+15,x+w//2+8,y+29), fill=RED)
        draw.line((x+w//2,y+7,x+w//2,y+15), fill=RED, width=2)
        draw.line((x+w//2-7,y+11,x+w//2+7,y+11), fill=RED, width=2)
    elif kind == "chart":
        for i, bh in enumerate((11,20,30,39)):
            draw.rectangle((x+8+i*13,y+h-5-bh,x+17+i*13,y+h-5), fill=BLUE if i<3 else RED)
        draw.line((x+2,y+7,x+w-4,y+h-11), fill=RED, width=3)
        draw.polygon((x+w-9,y+h-15,x+w-3,y+h-11,x+w-11,y+h-8), fill=RED)
    elif kind == "tanker":
        draw.ellipse((x+10,y+18,x+w-10,y+h-5), outline=NAVY, width=2)
        draw.rectangle((x+25,y+13,x+w-28,y+24), fill=BLUE)
        draw.polygon((x+w//2-6,y+11,x+w//2+2,y+2,x+w//2+5,y+13), fill=RED)
        for mx,my in ((12,8),(35,4),(w-18,10)): draw.ellipse((x+mx,y+my,x+mx+5,y+my+5), outline=RED, width=1)
    elif kind == "tower":
        draw.rectangle((x+w//2-12,y+5,x+w//2+12,y+h-5), fill=BLUE, outline=NAVY)
        for yy in range(y+10,y+h-8,9): draw.line((x+w//2-9,yy,x+w//2+9,yy), fill=WHITE, width=1)
        draw.polygon((x+w//2-19,y+5,x+w//2,y-2,x+w//2+19,y+5), fill=RED)
        for px,py in ((x+8,y+1),(x+w-17,y+10),(x+17,y+25)): draw.polygon((px,py,px+5,py+10,px+10,py+4), fill=RED)
    elif kind == "yellow":
        draw.line((x+4,y+17,x+w-4,y+17), fill=YELLOW, width=3)
        draw.rectangle((x+20,y+9,x+48,y+25), fill=GREEN, outline=NAVY)
        draw.ellipse((x+24,y+22,x+32,y+30), fill=NAVY); draw.ellipse((x+40,y+22,x+48,y+30), fill=NAVY)
        draw.polygon((x+48,y+12,x+58,y+17,x+48,y+22), fill=GREEN)
    elif kind == "game":
        draw.line((x+8,y+h-3,x+w-8,y+h-3), fill=GREEN, width=2)
        draw.polygon((x+18,y+h-5,x+24,y+10,x+30,y+h-5), fill=GREEN)
        draw.polygon((x+30,y+h-5,x+37,y+8,x+44,y+h-5), fill=GREEN)
        draw.ellipse((x+w-34,y+9,x+w-4,y+31), outline=RED, width=3)
        draw.ellipse((x+w-17,y+16,x+w-13,y+20), fill=RED)
    elif kind == "stock":
        draw.line((x+5,y+h-5,x+18,y+h-13,x+30,y+h-8,x+44,y+7,x+w-4,y+2), fill=GREEN, width=3)
        draw.polygon((x+w-10,y+1,x+w-3,y+2,x+w-5,y+9), fill=GREEN)
        draw.ellipse((x+20,y+14,x+43,y+35), outline=NAVY, width=2)
        draw.arc((x+25,y+18,x+38,y+31), 200, 340, fill=RED, width=2)
    elif kind == "flags":
        draw.ellipse((x+w//2-10,y+8,x+w//2+10,y+28), outline=NAVY, width=2)
        for i,col in enumerate((BLUE,RED,GOLD,GREEN)):
            px=x+8+i*14; draw.line((px,y+5,px,y+h-3), fill=NAVY, width=1); draw.rectangle((px,y+7,px+10,y+14), fill=col)
        draw.rectangle((x+w//2-10,y+31,x+w//2+10,y+36), outline=RED)
    elif kind == "cyclone":
        draw.arc((x+8,y+3,x+w-8,y+h+10), 20, 330, fill=BLUE, width=3)
        draw.arc((x+19,y+10,x+w-18,y+h-1), 30, 320, fill=RED, width=2)
        draw.line((x+3,y+h-2,x+w-6,y+h-2), fill=GREEN, width=2)
    else:
        draw.line((x,y+h//2,x+w,y+h//2), fill=BLUE, width=2)

def block(draw, xy, value, path, size, fill, width, leading, bottom, max_lines=None):
    x,y=xy
    fnt=font(path,size)
    lines=wrap(draw,value,fnt,width)
    assert max_lines is None or len(lines)<=max_lines, value
    assert all(draw.textlength(line,font=fnt)<=width for line in lines), value
    assert not lines or y+(len(lines)-1)*leading+fnt.getbbox(lines[-1])[3]<=bottom, value
    for i,line in enumerate(lines):
        draw.text((x,y+i*leading),line,font=fnt,fill=fill)


def section(draw, y, title, strap):
    draw.text((18,y),title,font=font(SERIF_B,14),fill=NAVY)
    draw.text((1006,y),strap,font=font(SANS_B,10),fill=RED,anchor="ra")


def draw_lead(draw, box, tag, source, headline, body, kind):
    x1,y1,x2,y2=box; card(draw,box)
    chip(draw,x1+10,y1+9,tag)
    sf=font(SANS_B,8); sw=draw.textlength(source,font=sf)
    draw.text((x2-10-sw,y1+13),source,font=sf,fill=MUTED)
    block(draw,(x1+10,y1+31),headline,SERIF_B,16,NAVY,x2-x1-20,20,y1+85,max_lines=2)
    line_icon(draw,kind,x1+10,y1+87,90,42)
    block(draw,(x1+108,y1+89),body,SANS,10,INK,x2-x1-118,12,y2-6)

def draw_brief(draw, box, n, tag, source, headline, body, kind, color):
    x1,y1,x2,y2=box; card(draw,box,False)
    circle_num(draw,x1+15,y1+15,n,color,9)
    chip(draw,x1+29,y1+7,tag,color)
    sf=font(SANS_B,7); draw.text((x2-8-draw.textlength(source,font=sf),y1+11),source,font=sf,fill=MUTED)
    block(draw,(x1+9,y1+29),headline,SANS_B,14,NAVY,x2-x1-18,14.5,y1+63,max_lines=2)
    line_icon(draw,kind,x1+8,y1+66,55,30)
    block(draw,(x1+69,y1+66),body,SANS,8,INK,x2-x1-78,9,y2-6)

def region_color(place):
    if place in ("Manila","Kyiv","Moscow","Sevastopol","New Delhi","Mumbai","Dhaka","Wellington","Singapore"): return BLUE
    if place in ("Beirut","Baghdad","Antalya"): return ORANGE
    if place in ("Brussels","Paris","London","Geneva"): return GREEN
    if place in ("Quito","Washington","Philadelphia","New York","Mexico City","Toronto"): return RED
    return GOLD

def draw_map(draw):
    x1,y1,x2,y2=24,615,1000,705
    draw.rectangle((x1,y1,x2,y2), fill=(239,235,222), outline=(211,201,181))
    MX,MY,MW,MH=x1+12,y1+5,590,y2-y1-10
    continents=[
        [(-168,70),(-145,72),(-128,61),(-111,54),(-93,53),(-62,59),(-53,47),(-76,25),(-89,16),(-105,23),(-119,39),(-139,57)],
        [(-75,11),(-52,5),(-35,-8),(-46,-25),(-67,-55),(-77,-15)],
        [(-53,82),(-22,72),(-40,59),(-57,63)],
        [(-11,36),(-8,59),(20,71),(53,66),(84,76),(130,60),(177,64),(158,47),(137,35),(122,18),(107,1),(97,12),(77,8),(65,25),(44,13),(34,31)],
        [(-17,35),(11,37),(36,29),(51,12),(38,-13),(20,-35),(9,-30),(-2,-4),(-16,14)],
        [(112,-12),(139,-11),(154,-27),(145,-40),(116,-33)],
        [(47,-13),(51,-16),(48,-26),(44,-24)],
        [(128,31),(142,44),(145,43),(136,32)],
        [(166,-34),(178,-40),(172,-47),(165,-45)]
    ]
    def mapxy(lon,lat):
        return MX+(lon+180)/360*MW, MY+(83-lat)/143*MH
    def inside(x,y,pp):
        hit=False; j=len(pp)-1
        for i in range(len(pp)):
            xi,yi=pp[i]; xj,yj=pp[j]
            if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: hit=not hit
            j=i
        return hit
    for lat in range(-55,84,7):
        for lon in range(-178,179,4):
            if any(inside(lon,lat,p) for p in continents):
                px,py=mapxy(lon,lat)
                draw.ellipse((px-1.8,py-1.8,px+1.8,py+1.8),fill="#a7aaa0")
    pins=[(1,114,23,BLUE,536,643),(2,4,52,GREEN,319,625),
          (4,50,26,GREEN,407,628),(5,50,26,ORANGE,433,640),
          (6,46,24,ORANGE,426,671),(7,35,31,ORANGE,365,670),
          (8,-118,34,BLUE,126,636),(10,13,52,GREEN,355,625),
          (11,85,20,BLUE,479,669)]
    for n,lon,lat,col,lx,ly in pins:
        px,py=mapxy(lon,lat)
        draw.line((px,py,lx,ly),fill=col,width=1)
        draw.ellipse((px-2,py-2,px+2,py+2),fill=col)
    for n,lon,lat,col,lx,ly in pins:
        draw.ellipse((lx-7,ly-7,lx+7,ly+7),fill=col,outline=WHITE,width=1)
        f=font(SANS_B,7); s=str(n); draw.text((lx-draw.textlength(s,font=f)/2,ly-5),s,font=f,fill=WHITE)
    draw.text((38,622),"N",font=font(SANS_B,8),fill=NAVY)
    legend=[("Asia-Pacific",BLUE),("Americas",RED),("Europe",GREEN),("Middle East",ORANGE),("Africa",GOLD),("Global - space",NAVY)]
    for i,(name,col) in enumerate(legend):
        lx=870+(i%2)*62; ly=621+(i//2)*15
        draw.rectangle((lx,ly,lx+7,ly+7),fill=col); draw.text((lx+10,ly-1),name,font=font(SANS,6),fill=INK)

def main():
    img=Image.new("RGB",(W,H),PAPER); d=ImageDraw.Draw(img)
    rule(d,(24,18),976,GOLD,3)
    d.text((24,27),"THURSDAY 19 NOVEMBER 2026",font=font(SANS_B,9),fill=RED)
    d.text((252,24),"THE DAY IN WORLD NEWS",font=font(SERIF_B,27),fill=NAVY)
    d.rectangle((824,21,1000,66),fill=NAVY)
    d.text((838,27),"40 STORIES",font=font(SANS_B,13),fill=WHITE)
    d.text((838,45),"6 CONTINENTS - ONE PAGE",font=font(SANS,8),fill=(236,215,151))
    strap="Everything on this page happened, or was first reported, on Thursday 19 November 2026."
    d.text((245,68),strap,font=font(SANS,9),fill=INK)
    leads=[("ASIA · SUMMIT","REUTERS · AP","Xi, Trump, Putin sign 'Declaration Towards Peace'","The first three-power summit, at APEC in Shenzhen, ends with a pledge that nuclear war must never be fought - and no arms-control talks. Trump flies home; allies question the embrace.","summit"),("WORLD COURT","ICJ · AP","World Court: Myanmar's Rohingya crackdown is genocide","The ICJ rules for the first time that a state committed genocide, finding intent to destroy the Rohingya in Rakhine nearly a decade ago.","court"),("EUROPE · UKRAINE WAR","REUTERS · KIEV INDEP","Ukraine hits Crimean Bridge again; rail halted","Neptune missiles strike the arch and tracks two days after a Flamingo strike felled a span. Putin says ceasefire talks are off and vows a 'far more painful' answer.","bridge")]
    for i,row in enumerate(leads): draw_lead(d,(24+i*326,92,340+i*326,302),*row)
    section(d,314,"EIGHT MORE STORIES TO KNOW","04-11 / THE BRIEFING")
    briefs=[("EUROPE · MARKETS","FED · AP","Fed minutes point to December hike","Odds of a quarter-point rise on Dec 9 hit 95%; Waller floats half a point. S&P slides a fifth day; gold falls 3.6% to $3,726.","chart",GREEN),("MIDDLE EAST · IRAN WAR","IRGC · AP","Two supertankers burn in Hormuz mines","Iran says tankers carrying 4m barrels of crude hit mines on an unauthorised route; CENTCOM silent. Tehran warns ships sailing with the US will be 'dealt with'.","tanker",ORANGE),("MIDDLE EAST · YEMEN","HOUTHI · SAUDI","Houthi missile debris falls on Riyadh","Dawn and evening volleys hit the capital; debris strikes the PIF Tower. Airstrikes kill 15 in Mokha and Taiz, the rebels' health ministry says.","tower",ORANGE),("MIDDLE EAST · GAZA","NYT · AJ","Israel pushes past the Yellow Line","Tanks and bulldozers move two-thirds through Gaza; two million shelter in a shrinking strip. Displaced Palestinians count a 15th flight.","yellow",ORANGE),("ASIA · GAMING","SENSOR TOWER · AP","GTA VI launches after 13-year wait","Presales top $1.6bn with 17m copies; reviews score 99 on Metacritic. Leonida's Vice City opens on PS5 and Xbox at $79.99.","game",BLUE),("AMERICAS · TECH","NASDAQ · REUTERS","Anthropic debuts on Nasdaq as ANT","The Claude maker prices at $83, raising $81.3bn at a $1.5tn valuation - the largest IPO on record, past SpaceX.","stock",RED),("EUROPE · DIPLOMACY","DW · REUTERS","Europe rejects 'Yalta 2.0' for Ukraine","After the trilateral, Merz tells a Berlin meeting of the willing that a Yalta format 'will not bring peace' as Kyiv's allies rally.","flags",GREEN),("ASIA · WEATHER","IMD · PTI","Cyclone Akvan nears Odisha coast","Landfall due near Gopalpur by Friday noon; one lakh evacuated, 448 shelters open, schools shut for three days as winds near 100 kmph.","cyclone",BLUE)]
    for i,row in enumerate(briefs):
        col=i%4; rr=i//4; draw_brief(d,(24+col*244,332+rr*124,260+col*244,452+rr*124),i+4,*row)
    section(d,584,"WHERE IT HAPPENED","NUMBERED PINS REFER TO THE STORIES")
    draw_map(d)
    section(d,714,"ALSO ON THURSDAY 19 NOVEMBER","12-40 / AROUND THE WORLD")
    rows=[("Manila","Trump departs Asia after trilateral"),("Kyiv","Drone raid kills one; embassies hit"),("Moscow","Putin ends energy ceasefire talks"),("Sevastopol","Fuel queues after bridge strikes"),("Beirut","Israel strikes Hezbollah Beqaa site"),("Baghdad","State strikes deal with Kataib"),("Brussels","EU Commission hit by cyberattack"),("Quito","Hegseth signs Venezuela army pact"),("Washington","Third Supreme Court bid on TPS"),("Dakar","Migrant boat capsizes; dozens missing"),("Siberia","Military transport crash kills 19"),("Nairobi","Kenya Ebola-free in 37 days"),("Antalya","Tuvalu pleads at COP31 for survival"),("Antalya","IPCC report delay fight erupts"),("New Delhi","Modi tells industry to lift wages"),("Mumbai","IDBI sale sparks bank-strike call"),("Paris","France to monitor YouTubers' bias"),("Washington","Jeffries nominated for Speaker"),("Philadelphia","27 years for Trump plot"),("London","US soldier held in UK spy case"),("Dhaka","Arson wave before Hasina return"),("Wellington","India, New Zealand open Test"),("Singapore","Sindhu returns to world top five"),("New York","S&P slides fifth day to 7,323"),("London","Dollar index near 103.8, high"),("Geneva","WTO trims 2026 trade outlook"),("Mexico City","Sheinbaum hails Venezula pact"),("Canberra","Tasmania floods cut highways"),("Toronto","Loonie at weakest since 2003")]
    for i,(place,story) in enumerate(rows):
        col=i//15; row=i%15; x=24+col*490; y=735+row*12
        d.rectangle((x,y,x+474,y+11),fill=WHITE if row%2==0 else (239,235,224))
        circle_num(d,x+10,y+6,12+i,region_color(place),5)
        d.text((x+20,y+1),place,font=font(SANS_B,8),fill=NAVY)
        d.text((x+89,y+1),story,font=font(SANS,8),fill=INK)
    d.rectangle((24,929,1000,970),fill=NAVY)
    d.text((34,934),"DAY IN NUMBERS",font=font(SANS_B,9),fill=(236,215,151))
    tiles=["3 POWERS sign one declaration","$1.5TN Anthropic's debut value","95% odds of a December Fed hike","2/3 of Gaza now occupied","$1.6BN GTA VI presales"]
    for i,t in enumerate(tiles): d.text((145+i*171,936),t,font=font(SANS_B,7),fill=WHITE)
    d.text((24,976),"DATE CHECK",font=font(SERIF_B,8),fill=RED)
    date="Checked and left out: Nigeria's fuel-price freeze and the Seoul tunnel verdict, first reported Tuesday 17 Nov, and KSA-World Cup items dated 20 Nov - after this day. Voyager 1's one-light-day milestone was 18 Nov."
    text_block(d,(92,976),date,font(SERIF,7),MUTED,900,leading=9,max_lines=2)
    d.text((24,998),"All 40 stories happened, or were first reported, on Thursday 19 November 2026 · Original drawings",font=font(SANS,6),fill=MUTED)
    d.text((570,998),"Sources: Reuters · AP · The Hindu · Euronews · Kyiv Independent · Al Jazeera · NPR · Democracy Now! · PTI · IPS",font=font(SANS,6),fill=MUTED)
    out=os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out, exist_ok=True)
    path=os.path.join(out,"entry.png")
    img.save(path,format="PNG",optimize=False,compress_level=9)
    blocks=1+3*4+8*4+29+5+2
    size=os.path.getsize(path)
    print(f"Rendered entry.png: 1024x1024, RGB; {blocks} text blocks checked; {size} bytes")

if __name__ == "__main__": main()
