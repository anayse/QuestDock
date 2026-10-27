"""Cached supersampled orb artwork; no animation or per-frame raster work."""
from functools import lru_cache
from PIL import Image, ImageDraw


@lru_cache(maxsize=48)
def artwork(size, level, ready, hover):
    scale=4
    image=Image.new('RGBA',(size*scale,size*scale))
    draw=ImageDraw.Draw(image)
    def box(a,b,c,d):return tuple(round(v*size*scale/56) for v in (a,b,c,d))
    # Concentric shaded disc, smooth orbit and a faceted crystalline emblem.
    for radius in range(round(26*size*scale/56),0,-1):
        t=radius/(26*size*scale/56)
        color=(int(24+10*(1-t)),int(28+10*(1-t)),int(46+16*(1-t)),255)
        center=size*scale/2
        draw.ellipse((center-radius,center-radius,center+radius,center+radius),fill=color)
    draw.ellipse(box(2,2,54,54),outline='#a69be9' if hover else '#626386',width=scale)
    draw.arc(box(6,6,50,50),0,360,fill='#373e58',width=2*scale)
    if level:draw.arc(box(6,6,50,50),-90,-90+360*level/20,fill='#a798ff',width=2*scale)
    points=[(28,11),(38,23),(28,35),(18,23)]
    points=[(int(x*size*scale/56),int(y*size*scale/56)) for x,y in points]
    draw.polygon(points,fill='#b9afff')
    draw.polygon([points[0],points[1],points[2]],fill='#8370d9')
    draw.polygon([points[0],points[3],(round(28*size*scale/56),round(23*size*scale/56))],fill='#e1ddff')
    if ready:draw.ellipse(box(43,4,51,12),fill='#f3ce91',outline='#171b2d',width=scale)
    image=image.resize((size,size),Image.Resampling.LANCZOS)
    return image
