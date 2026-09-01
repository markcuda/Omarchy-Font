#!/usr/bin/env python3
from pathlib import Path
import struct, sys

U = 1000
SHAPES = {"█": (0, 0, 1, 1), "▀": (0, .5, 1, .5), "▄": (0, 0, 1, .5), "▌": (0, 0, .5, 1), "▐": (.5, 0, .5, 1)}
def p4(b): return b + b"\0" * (-len(b) % 4)
def glyph(rows):
    width = max(map(len, rows), default=1) * 100
    contours, points = [], []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch not in SHAPES: continue
            x, y, w, h = SHAPES[ch]; x0, x1 = round((c+x)*100), round((c+x+w)*100)
            y0 = (len(rows)-r-1)*100 + round(y*100); y1 = y0 + round(h*100)
            points += [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]; contours.append(len(points)-1)
    if not points: return struct.pack(">hhhhh", 0, 0, 0, width, 0), width
    b = struct.pack(">hhhhh", len(contours), 0, 0, width, len(rows)*100)
    b += struct.pack(">"+"H"*len(contours), *contours) + struct.pack(">H", 0) + bytes([1,1,1,1])*len(contours)
    encoded, px, py = b"", 0, 0
    for x, y in points:
        encoded += struct.pack(">hh", x-px, y-py); px, py = x, y
    return b + encoded, width
def table(tag, data): return tag, p4(data), len(data)
def main(src, dest):
    lines = Path(src).read_text(encoding="utf-8").splitlines(); hard, height, _, _, _, comments = lines[0].split()[:6]
    body, i, chars = lines[1+int(comments):], 0, []
    for _ in range(95):
        chars.append([body[i+j].replace(hard, " ").rstrip("@") for j in range(int(height))]); i += int(height)
    gs, widths = [struct.pack(">hhhhh", 0,0,0,0,0)], [600]
    for rows in chars:
        g, w = glyph(rows); gs.append(g); widths.append(max(w,100))
    glyf, offsets = b"", [0]
    for g in gs: glyf += g; offsets.append(len(glyf))
    loca = b"".join(struct.pack(">I", x) for x in offsets); n = len(gs)
    hmtx = b"".join(struct.pack(">HH", w, 0) for w in widths)
    sub = struct.pack(">HHHHHHH", 4, 32, 0, 4, 4, 1, 0)
    sub += struct.pack(">HHH", 126, 0xFFFF, 0) + struct.pack(">HH", 32, 0xFFFF)
    sub += struct.pack(">hh", -31, 1) + struct.pack(">HH", 0, 0)
    cmap = struct.pack(">HHHHI", 0, 1, 3, 1, 12) + sub
    head = struct.pack(">IIIIHHqqhhhhhhhhh", 0x10000,0,0,0x5F0F3CF5,0,1000,0,0,0,0,max(widths),int(height)*100,0,8,2,1,0)
    hhea = struct.pack(">IhhhhhhhhHhhhhhhh", 0x10000,900,-100,1000,0,max(widths),0,0,0,n,0,0,0,0,0,0,0)
    maxp = struct.pack(">IH" + "H"*13, 0x10000, n, *([max(struct.unpack(">h",g[:2])[0] for g in gs),4,0,0] + [0]*9))
    os2 = bytearray(78); struct.pack_into(">HhHHH", os2, 0, 0, 700, 400, 5, 0)
    names = [(1,"Omarchy Font"),(2,"Regular"),(4,"Omarchy Font"),(6,"OmarchyFont-Regular"),(0,"Delta Corps Priest 1 converted to vector outlines")]
    strings, recs = b"", []
    for nid, value in names:
        b=value.encode("utf-16-be"); recs.append((3,1,0x409,nid,len(b),len(strings))); strings += b
    name=struct.pack(">HHH",0,len(recs),6+12*len(recs))+b"".join(struct.pack(">HHHHHH",*r) for r in recs)+strings
    post=struct.pack(">IiiHH",0x30000,0,0,0,0)+b"\0"*16
    tabs=sorted(table(*x) for x in [(b"OS/2",bytes(os2)),(b"cmap",cmap),(b"glyf",glyf),(b"head",head),(b"hhea",hhea),(b"hmtx",hmtx),(b"loca",loca),(b"maxp",maxp),(b"name",name),(b"post",post)])
    count=len(tabs); mp=1<<(count.bit_length()-1); font=struct.pack(">IHHHH",0x10000,count,mp*16,count*16-mp*16,count-mp); records=[]; payload=b""; offset=12+16*count
    for tag,data,rawlen in tabs:
        checksum=sum(struct.unpack(">"+"I"*(len(data)//4),data))&0xffffffff; records.append(struct.pack(">4sIII",tag,checksum,offset,rawlen)); payload+=data; offset+=len(data)
    font += b"".join(records)+payload; hi=12+next(i for i,(tag,_,_) in enumerate(tabs) if tag==b"head")*16; hp=struct.unpack(">I",font[hi+8:hi+12])[0]; font=font[:hp]+b"\0\0\0\0"+font[hp+4:]
    adj=(0xB1B0AFBA-sum(struct.unpack(">"+"I"*(len(p4(font))//4),p4(font)))&0xffffffff); Path(dest).write_bytes(font[:hp]+struct.pack(">I",adj)+font[hp+4:])
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
