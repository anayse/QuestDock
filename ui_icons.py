"""Fixed-size, supersampled icons: no font fallback or emoji substitution."""
import math
from functools import lru_cache
from PIL import Image,ImageDraw


@lru_cache(maxsize=12)
def icon(name,size):
    scale=4;n=size*scale
    image=Image.new('RGBA',(n,n));draw=ImageDraw.Draw(image)
    if name=='coin':
        draw.ellipse((2*scale,2*scale,n-2*scale,n-2*scale),fill='#edc583',outline='#b98b4e',width=scale)
        draw.ellipse((4*scale,4*scale,n-4*scale,n-4*scale),outline='#fff0b8',width=scale)
    elif name=='info':
        draw.ellipse((scale,scale,n-scale,n-scale),outline='#9aa4bd',width=scale)
        draw.ellipse((n*.44,n*.24,n*.56,n*.36),fill='#b8b0e8')
        draw.rounded_rectangle((n*.45,n*.44,n*.55,n*.76),radius=scale/2,fill='#b8b0e8')
    else:
        points=[]
        for i in range(64):
            angle=i*math.tau/64;radius=n*(.45 if i%8 in (2,3,4,5) else .35)
            points.append((n/2+math.cos(angle)*radius,n/2+math.sin(angle)*radius))
        draw.polygon(points,fill='#a7b0c9')
        draw.ellipse((n*.34,n*.34,n*.66,n*.66),fill=(0,0,0,0))
    return image.resize((size,size),Image.Resampling.LANCZOS)


def level_progress(earned):
    earned=max(0,int(earned))
    return 1+earned//200,earned%200,200
