#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os
from collections import Counter
from functools import lru_cache

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
DISPLAY = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
ITALIC = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Oblique.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

@lru_cache(maxsize=None)
def font(path, size):
    return ImageFont.truetype(path, size)


TEXT_BLOCKS = []
STORY_CHIPS = []


def text_size(draw, text, fnt):
    bb = draw.textbbox((0, 0), text, font=fnt, anchor="lt")
    return max(fnt.getlength(text), bb[2])-min(0,bb[0]), bb[3]-bb[1], bb


def check_box(text, box, width, height):
    x1, y1, x2, y2 = box
    ok = (0 <= x1 <= x2 <= W and 0 <= y1 <= y2 <= H
          and width <= x2-x1+0.01 and height <= y2-y1+0.01)
    if not ok:
        print(f"OVERFLOW {text!r}: {width:.2f}×{height:.2f} in {box}")
    assert ok, f"Text exceeds its box: {text!r}"


def checked_text(draw, box, text, fnt, fill=NAVY, *, align="left"):
    """Measure advance and visible ink; never crop or silently overflow."""
    x1, y1, x2, _ = box
    width, height, bb = text_size(draw, text, fnt)
    check_box(text, box, width, height)
    x = x1 if align == "left" else x2-width if align == "right" else (x1+x2-width)/2
    draw.text((x-min(0, bb[0]), y1-bb[1]), text, font=fnt, fill=fill, anchor="lt")
    TEXT_BLOCKS.append((text, box))


def display_date(img, draw, box, text):
    """Set 88px display type in a condensed lockup, preserving vertical scale."""
    fnt = font(DISPLAY,88)
    width, height, _ = text_size(draw,text,fnt)
    mask = Image.new("L", (int(width+1),height))
    bb = fnt.getbbox(text,anchor="lt")
    ImageDraw.Draw(mask).text((-min(0,bb[0]),-bb[1]),text,font=fnt,fill=255,anchor="lt")
    x1,y1,x2,y2 = box
    mask = mask.crop(mask.getbbox())
    mask = mask.resize((min(mask.width,x2-x1),min(mask.height,y2-y1)),Image.Resampling.LANCZOS)
    check_box(text,box,*mask.size)
    img.paste(NAVY,(x1,y1+(y2-y1-mask.height)//2),mask)
    TEXT_BLOCKS.append((text,box))


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for word in text.split():
        test = word if not cur else cur + " " + word
        if fnt.getlength(test) <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def paragraph(draw, box, text, fnt, fill=INK, leading=13, inset=None):
    """Flow around an illustration, retaining every word in reading order."""
    x1, y1, x2, y2 = box
    words = text.split()
    line_no = 0
    while words:
        y = y1 + line_no*leading
        x = x1 + (inset[0] if inset and line_no*leading < inset[1] else 0)
        line = words.pop(0)
        while words and fnt.getlength(line+" "+words[0]) <= x2-x:
            line += " " + words.pop(0)
        checked_text(draw, (x, y, x2, min(y+leading, y2)), line, fnt, fill)
        line_no += 1
    return y1 + line_no*leading


def rule(draw, xy, length, fill=NAVY, width=1):
    x, y = xy
    draw.rectangle((x, y, x+length, y+width-1), fill=fill)


def card(draw, box, shadow=False):
    draw.rectangle(box, fill=WHITE, outline=(191, 189, 179), width=1)


def circle_num(draw, x, y, n, color=NAVY, r=8, *, reference=False):
    if not reference:
        STORY_CHIPS.append(n)
    draw.ellipse((x-r, y-r, x+r, y+r), fill=color)
    label_r = max(r-1, 7)
    checked_text(draw, (x-label_r, y-4, x+label_r, y+5), str(n), font(SANS_B, 8), WHITE, align="center")


def tracked(draw, box, text, fnt, spacing=1.1, fill=NAVY, align="left"):
    widths = [text_size(draw,c,fnt)[0] for c in text]
    total = sum(widths) + spacing*(len(text)-1)
    x1, y1, x2, y2 = box
    check_box(text,box,total,max(text_size(draw,c,fnt)[1] for c in text))
    x = x2-total if align == "right" else (x1+x2-total)/2 if align == "center" else x1
    for c,w in zip(text,widths):
        checked_text(draw, (x, y1, x+w, y2), c, fnt, fill)
        x += w+spacing

def line_icon(draw, kind, x, y, w, h):
    # Small original ink illustrations, kept geometric for deterministic rendering.
    if kind == "summit":
        draw.ellipse((x+w//2-28, y+5, x+w//2+28, y+h-3), outline=GOLD, width=2)
        draw.line((x+18,y+h-8,x+w-18,y+h-8), fill=NAVY, width=3)
        for dx, col in ((18, BLUE), (w//2, RED), (w-18, GREEN)):
            draw.ellipse((x+dx-7,y+13,x+dx+7,y+27), fill=col)
            draw.line((x+dx,y+27,x+dx,y+h-9), fill=col, width=4)
        draw.rectangle((x+w//2-26,y+h//2-5,x+w//2+26,y+h//2+9), fill=WHITE, outline=NAVY)
        checked_text(draw,(x+w//2-20,y+h//2-3,x+w//2+23,y+h//2+8),"PEACE",font(SANS_B,8),RED,align="center")
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

def section(draw, y, title, strap=""):
    checked_text(draw, (14,y,780,y+15), title, font(SERIF_B,13))
    if strap:
        checked_text(draw, (785,y+2,1010,y+14), strap, font(SANS_B,8), RED, align="right")


def draw_lead(draw, box, n, tag, source, headline, body, kind):
    x1,y1,x2,y2 = box
    card(draw, box)
    rule(draw, (x1,y1), x2-x1, RED, 2)
    circle_num(draw, x1+15,y1+15,n,RED)
    checked_text(draw, (x1+29,y1+11,x2-8,y1+21), tag, font(SANS_B,8))
    checked_text(draw, (x1+9,y1+27,x2-9,y1+36), source, font(SANS_B,7), MUTED)
    end = paragraph(draw, (x1+9,y1+43,x2-9,y1+100), headline, font(SERIF_B,16), NAVY, 18)
    line_icon(draw,kind,x1+9,end+4,78,44)
    paragraph(draw, (x1+9,end+3,x2-9,y2-6),body,font(SANS,11),leading=12.5,inset=(87,48))


def draw_brief(draw, box, n, tag, source, headline, body, kind, color):
    x1,y1,x2,y2 = box
    card(draw, box)
    rule(draw,(x1,y1),x2-x1,color)
    circle_num(draw,x1+13,y1+11,n,NAVY)
    checked_text(draw,(x1+26,y1+7,x1+142,y1+17),tag,font(SANS_B,7))
    checked_text(draw,(x1+145,y1+7,x2-8,y1+17),source,font(SANS_B,7),MUTED,align="right")
    paragraph(draw,(x1+8,y1+21,x2-72,y1+66),headline,font(SANS_B,15),NAVY,15)
    line_icon(draw,kind,x2-66,y1+21,60,44)
    paragraph(draw,(x1+8,y1+66,x2-8,y2-3),body,font(SANS,12),leading=13,fill=NAVY)


# Assign by the story's geographic focus; worldwide is a scope, not a seventh region.
REGION_NAMES = ("ASIA-PACIFIC", "EUROPE", "MIDDLE EAST", "AMERICAS", "AFRICA", "OCEANIA", "WORLDWIDE")
REGION_COLORS = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6")
ASIA, EUROPE, MIDEAST, AMERICAS, AFRICA, OCEANIA, WORLD = range(len(REGION_NAMES))
STORY_REGIONS = (
    ASIA,WORLD,EUROPE,AMERICAS,MIDEAST,MIDEAST,MIDEAST,WORLD,AMERICAS,EUROPE,ASIA,
    ASIA,EUROPE,EUROPE,EUROPE,MIDEAST,MIDEAST,EUROPE,AMERICAS,AMERICAS,AFRICA,
    ASIA,AFRICA,WORLD,WORLD,ASIA,ASIA,EUROPE,AMERICAS,AMERICAS,EUROPE,ASIA,
    OCEANIA,ASIA,AMERICAS,WORLD,WORLD,AMERICAS,OCEANIA,AMERICAS,
)


def draw_map(draw):
    """Compact dot-matrix atlas; high-contrast numbered pins match the list."""
    x1,y1,x2,y2=14,657,1009,711
    draw.rectangle((x1,y1,x2,y2),fill=(239,235,222),outline=(211,201,181))
    MX,MY,MW,MH=x1+22,y1+5,570,44
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
                draw.ellipse((px-1.4,py-1.4,px+1.4,py+1.4),fill="#a7aaa0")
    pins=[(1,114,23,536,681),(2,4,52,319,669),(4,50,26,394,669),
          (5,50,26,433,679),(6,46,24,420,699),(7,35,31,365,697),
          (8,-118,34,126,681),(10,13,52,350,669),(11,85,20,479,698)]
    for n,lon,lat,lx,ly in pins:
        px,py=mapxy(lon,lat)
        draw.line((px,py,lx,ly),fill=NAVY,width=1)
        draw.ellipse((px-2,py-2,px+2,py+2),fill=NAVY)
    for n,lon,lat,lx,ly in pins:
        assert n in STORY_CHIPS and x1+9<lx<x2-9 and y1+9<ly<y2-9
        draw.ellipse((lx-9,ly-9,lx+9,ly+9),fill=NAVY,outline=WHITE,width=1)
        checked_text(draw,(lx-7,ly-4,lx+7,ly+5),str(n),font(SANS_B,8),WHITE,align="center")
    checked_text(draw,(628,663,997,677),"WHERE IT HAPPENED",font(SERIF_B,13))
    checked_text(draw,(628,680,997,694),"numbers match the stories",font(SANS,10))


def draw_story_list(draw, rows):
    """Measure each full list line and reject any horizontal or vertical overflow."""
    start_y, pitch = 731, 13.6
    story_font = font(SANS,12)
    place_font = font(SANS_B,12)
    placed = []
    for i,(place,story) in enumerate(rows):
        col,row = divmod(i,15)
        x=14+col*502; y=round(start_y+row*pitch)
        w,h=493,13
        draw.rectangle((x,y,x+w,y+h-1),fill=WHITE if row%2==0 else (239,235,224))
        circle_num(draw,x+9,y+6,12+i,NAVY,6)
        color = REGION_COLORS[STORY_REGIONS[11+i]]
        draw.rectangle((x+19,y+2,x+21,y+10),fill=color)
        label_x=x+123
        checked_text(draw,(x+26,y,label_x-4,y+h),place,place_font)
        # The original rows have no separate source suffix to trim.
        checked_text(draw,(label_x,y,x+w-4,y+h),story,story_font)
        placed.append((12+i,place,story,y))
    return placed


def main():
    global TEXT_BLOCKS, STORY_CHIPS
    TEXT_BLOCKS, STORY_CHIPS = [], []
    img=Image.new("RGB",(W,H),PAPER); d=ImageDraw.Draw(img)

    # Masthead: classic display date with an independently measured calendar lockup.
    tracked(d,(14,7,510,18),"THE WORLD IN ONE DAY",font(SANS_B,8),1.35,NAVY)
    tracked(d,(550,7,1009,18),"DAY 323 OF 2026 · ONE-PAGE EDITION",font(SANS_B,8),0.7,NAVY,align="right")
    calendar=(918,19,1009,92)
    d.rectangle(calendar,fill=WHITE,outline=RED,width=2)
    checked_text(d,(921,24,1006,34),"NOVEMBER 2026",font(SANS_B,8),RED,align="center")
    checked_text(d,(921,35,1006,78),"19",font(SERIF_B,52),NAVY,align="center")
    tracked(d,(921,79,1006,89),"THURSDAY",font(SANS_B,8),1.0,RED,align="center")
    display_date(img,d,(14,18,907,93),"Thursday 19 November 2026")
    strap="Trump, Xi and Putin share one table · World Court finds genocide in Myanmar · Cyclone Akvan closes on India's coast"
    checked_text(d,(14,94,1009,106),strap,font(ITALIC,11),RED)

    d.rectangle((14,109,1009,127),fill=WHITE,outline=NAVY)
    checked_text(d,(22,114,218,125),"40 STORIES FROM 6 REGIONS",font(SANS_B,10))
    counts=Counter(STORY_REGIONS)
    assert len(STORY_REGIONS)==40 and set(counts)==set(range(len(REGION_NAMES)))
    for i,(name,color) in enumerate(zip(REGION_NAMES,REGION_COLORS)):
        x=218+i*112
        d.ellipse((x,114,x+8,122),fill=color,outline=NAVY)
        checked_text(d,(x+13,114,x+108,125),f"{name} {counts[i]}",font(SANS_B,8.5))

    checked_text(d,(14,131,142,153),"THE DAY IN NUMBERS",font(SANS_B,9))
    stats=[("3","presidents one table"),("$81.3bn","Anthropic record IPO"),
           ("13 yrs","GTA VI wait"),("730,000+","Rohingya findings 2017"),
           ("204,070","evacuated Odisha"),("551,864","Korean exam takers"),
           ("4.9%","Australian jobless"),("48 hrs","left of COP31 Antalya")]
    for i,(value,caption) in enumerate(stats):
        x=143+i*108
        d.line((x-4,130,x-4,154),fill=(211,201,181))
        checked_text(d,(x,129,x+103,148),value,font(SANS_B,19),RED)
        checked_text(d,(x,148,x+102,157),caption,font(SANS,8))

    d.rectangle((14,159,1009,189),fill=WHITE,outline=NAVY)
    checked_text(d,(22,168,130,178),"THE DAY BY HOURS",font(SANS_B,9))
    events=[("00:00","AUCKLAND","GTA VI unlocks"),("08:40","SEOUL","exam begins"),
            ("04:42","RIYADH","air-raid sirens"),("09:30","JAKARTA","law passed"),
            ("P.M.","SHENZHEN","three leaders meet"),("10:00","THE HAGUE","genocide ruling"),
            ("09:30","NEW YORK","markets open")]
    tf=font(SANS_B,8.5)
    for i,(time,city,event) in enumerate(events):
        x=135+i*124
        d.line((x-4,164,x-4,184),fill=(211,201,181))
        checked_text(d,(x,164,x+29,174),time,tf,RED)
        checked_text(d,(x+33,164,x+120,174),city,tf)
        checked_text(d,(x,176,x+120,186),event,font(SANS,8.5))

    leads=[("ASIA · SUMMIT","REUTERS · AP","Xi, Trump, Putin sign 'Declaration Towards Peace'","The first three-power summit, at APEC in Shenzhen, ends with a pledge that nuclear war must never be fought - and no arms-control talks. Trump flies home; allies question the embrace.","summit"),("WORLD COURT","ICJ · AP","World Court: Myanmar's Rohingya crackdown is genocide","The ICJ rules for the first time that a state committed genocide, finding intent to destroy the Rohingya in Rakhine nearly a decade ago.","court"),("EUROPE · UKRAINE WAR","REUTERS · KIEV INDEP","Ukraine hits Crimean Bridge again; rail halted","Neptune missiles strike the arch and tracks two days after a Flamingo strike felled a span. Putin says ceasefire talks are off and vows a 'far more painful' answer.","bridge")]
    lead_y,lead_h=195,154
    lead_w=325
    for i,row in enumerate(leads):
        x=14+i*335
        draw_lead(d,(x,lead_y,x+lead_w,lead_y+lead_h),i+1,*row)
    checked_text(d,(695,337,1000,348),"COP31 ANTALYA · 48 HRS LEFT",font(SANS_B,8),RED,align="right")

    section(d,354,"EIGHT MORE STORIES TO KNOW","04–11 / THE BRIEFING")
    briefs=[("EUROPE · MARKETS","FED · AP","Fed minutes point to December hike","Odds of a quarter-point rise on Dec 9 hit 95%; Waller floats half a point. S&P slides a fifth day; gold falls 3.6% to $3,726.","chart",GREEN),("MIDDLE EAST · IRAN WAR","IRGC · AP","Two supertankers burn in Hormuz mines","Iran says tankers carrying 4m barrels of crude hit mines on an unauthorised route; CENTCOM silent. Tehran warns ships sailing with the US will be 'dealt with'.","tanker",ORANGE),("MIDDLE EAST · YEMEN","HOUTHI · SAUDI","Houthi missile debris falls on Riyadh","Dawn and evening volleys hit the capital; debris strikes the PIF Tower. Airstrikes kill 15 in Mokha and Taiz, the rebels' health ministry says.","tower",ORANGE),("MIDDLE EAST · GAZA","NYT · AJ","Israel pushes past the Yellow Line","Tanks and bulldozers move two-thirds through Gaza; two million shelter in a shrinking strip. Displaced Palestinians count a 15th flight.","yellow",ORANGE),("ASIA · GAMING","SENSOR TOWER · AP","GTA VI launches after 13-year wait","Presales top $1.6bn with 17m copies; reviews score 99 on Metacritic. Leonida's Vice City opens on PS5 and Xbox at $79.99.","game",BLUE),("AMERICAS · TECH","NASDAQ · REUTERS","Anthropic debuts on Nasdaq as ANT","The Claude maker prices at $83, raising $81.3bn at a $1.5tn valuation - the largest IPO on record, past SpaceX.","stock",RED),("EUROPE · DIPLOMACY","DW · REUTERS","Europe rejects 'Yalta 2.0' for Ukraine","After the trilateral, Merz tells a Berlin meeting of the willing that a Yalta format 'will not bring peace' as Kyiv's allies rally.","flags",GREEN),("ASIA · WEATHER","IMD · PTI","Cyclone Akvan nears Odisha coast","Landfall due near Gopalpur by Friday noon; one lakh evacuated, 448 shelters open, schools shut for three days as winds near 100 kmph.","cyclone",BLUE)]
    for i,row in enumerate(briefs):
        col=i%4; rr=i//4
        x=14+col*251; y=371+rr*136
        draw_brief(d,(x,y,x+242,y+132),i+4,*row)

    draw_map(d)
    section(d,715,"ALSO ON THURSDAY 19 NOVEMBER 2026","12–40 / AROUND THE WORLD")
    rows=[("Manila","Trump departs Asia after trilateral"),("Kyiv","Drone raid kills one; embassies hit"),("Moscow","Putin ends energy ceasefire talks"),("Sevastopol","Fuel queues after bridge strikes"),("Beirut","Israel strikes Hezbollah Beqaa site"),("Baghdad","State strikes deal with Kataib"),("Brussels","EU Commission hit by cyberattack"),("Quito","Hegseth signs Venezuela army pact"),("Washington","Third Supreme Court bid on TPS"),("Dakar","Migrant boat capsizes; dozens missing"),("Siberia","Military transport crash kills 19"),("Nairobi","Kenya Ebola-free in 37 days"),("Antalya","Tuvalu pleads at COP31 for survival"),("Antalya","IPCC report delay fight erupts"),("New Delhi","Modi tells industry to lift wages"),("Mumbai","IDBI sale sparks bank-strike call"),("Paris","France to monitor YouTubers' bias"),("Washington","Jeffries nominated for Speaker"),("Philadelphia","27 years for Trump plot"),("London","US soldier held in UK spy case"),("Dhaka","Arson wave before Hasina return"),("Wellington","India, New Zealand open Test"),("Singapore","Sindhu returns to world top five"),("New York","S&P slides fifth day to 7,323"),("London","Dollar index near 103.8, high"),("Geneva","WTO trims 2026 trade outlook"),("Mexico City","Sheinbaum hails Venezula pact"),("Canberra","Tasmania floods cut highways"),("Toronto","Loonie at weakest since 2003")]
    # Leave room for the two-column 12px list and date-check/furniture.
    list_rows=draw_story_list(d,rows)
    assert len(list_rows)==29 and all(row[3]+13<=937 for row in list_rows)

    # Preserve the original secondary numbers rail as well as the new stat band.
    d.rectangle((14,939,1009,957),fill=NAVY)
    checked_text(d,(24,944,180,953),"THE DAY IN NUMBERS",font(SANS_B,9),(236,215,151))
    footer_stats=["3 POWERS sign one declaration","$1.5TN Anthropic's debut value","95% odds of a December Fed hike","2/3 of Gaza now occupied","$1.6BN GTA VI presales"]
    for i,t in enumerate(footer_stats):
        checked_text(d,(180+i*160,937,338+i*160,951),t,font(SANS_B,7),WHITE)
    d.line((14,963,1009,963),fill=RED)
    checked_text(d,(14,969,28,982),"✓",font(SANS_B,12),RED)
    checked_text(d,(29,970,104,981),"DATE CHECK",font(SERIF_B,9),RED)
    checked_text(d,(107,970,319,981),"LEFT OUT AS OTHER DAYS' NEWS",font(SANS_B,8),NAVY)
    date="Checked and left out: Nigeria's fuel-price freeze and the Seoul tunnel verdict, first reported Tuesday 17 Nov, and KSA-World Cup items dated 20 Nov - after this day. Voyager 1's one-light-day milestone was 18 Nov."
    datef=font(SERIF,8)
    for j,line in enumerate(wrap(d,date,datef,690)):
        checked_text(d,(319,969+j*10,1009,979+j*10),line,datef,NAVY)
    checked_text(d,(24,1001,558,1012),"All 40 stories happened, or were first reported, on Thursday 19 November 2026 · Original drawings",font(SANS,6),MUTED)
    checked_text(d,(568,1001,1000,1012),"Sources: Reuters · AP · The Hindu · Euronews · Kyiv Independent · Al Jazeera · NPR · Democracy Now! · PTI · IPS",font(SANS,6),MUTED)

    assert len(STORY_CHIPS)==40, f"Expected 40 numbered chips, found {len(STORY_CHIPS)}"
    counts=Counter(STORY_CHIPS)
    assert set(counts)==set(range(1,41)) and all(v==1 for v in counts.values()),counts
    out=os.environ.get("MAKEFUN_OUTPUT_DIR", ".")
    os.makedirs(out, exist_ok=True)
    path=os.path.join(out,"entry.png")
    img.save(path,format="PNG",optimize=False,compress_level=9)
    size=os.path.getsize(path)
    print(f"Rendered entry.png: 1024x1024 RGB; {len(TEXT_BLOCKS)} text blocks checked; {size} bytes")


if __name__ == "__main__":
    main()
