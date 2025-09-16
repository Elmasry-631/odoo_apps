from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics

# تسجيل الخط اللي بيدعم العربي
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))




from . import wizerd