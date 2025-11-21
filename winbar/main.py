# appbar_with_tray.py -- Windows only
from carelinklib import CareLink
import psutil
import time
import sys
import signal
import ctypes
from ctypes import wintypes
from PySide6 import QtWidgets, QtCore, QtGui

# ---------------- Windows AppBar helpers ----------------
class RECT(ctypes.Structure):
  _fields_ = [('left', wintypes.LONG),
        ('top', wintypes.LONG),
        ('right', wintypes.LONG),
        ('bottom', wintypes.LONG)]

class APPBARDATA(ctypes.Structure):
  _fields_ = [('cbSize', wintypes.DWORD),
        ('hWnd', wintypes.HWND),
        ('uCallbackMessage', wintypes.UINT),
        ('uEdge', wintypes.UINT),
        ('rc', RECT),
        ('lParam', ctypes.c_int)]

###########################################
###########################################
###########################################

index = 0
cl = CareLink()
cl.main()
last_n_cache = [ sgs.get('sg',0) for sgs in cl.carelink_get_last_n__blood_sugar_data(12)]

###########################################
###########################################
###########################################

_shell = ctypes.windll.shell32
_user = ctypes.windll.user32
SHAppBarMessage = _shell.SHAppBarMessage

ABM_NEW = 0
ABM_REMOVE = 1
ABM_QUERYPOS = 2
ABM_SETPOS = 3

ABE_LEFT = 0
ABE_TOP = 1
ABE_RIGHT = 2
ABE_BOTTOM = 3

def get_primary_screen_size():
  return _user.GetSystemMetrics(0), _user.GetSystemMetrics(1)

def register_appbar(hwnd, edge=ABE_TOP, thickness=36):
  data = APPBARDATA()
  data.cbSize = ctypes.sizeof(APPBARDATA)
  data.hWnd = wintypes.HWND(hwnd)
  data.uEdge = edge
  sw, sh = get_primary_screen_size()
  if edge == ABE_TOP:
    data.rc.left = 0; data.rc.top = 0; data.rc.right = sw; data.rc.bottom = thickness
  elif edge == ABE_BOTTOM:
    data.rc.left = 0; data.rc.top = sh - thickness; data.rc.right = sw; data.rc.bottom = sh
  elif edge == ABE_LEFT:
    data.rc.left = 0; data.rc.top = 0; data.rc.right = thickness; data.rc.bottom = sh
  else:
    data.rc.left = sw - thickness; data.rc.top = 0; data.rc.right = sw; data.rc.bottom = sh
  SHAppBarMessage(ABM_NEW, ctypes.byref(data))
  SHAppBarMessage(ABM_QUERYPOS, ctypes.byref(data))
  SHAppBarMessage(ABM_SETPOS, ctypes.byref(data))
  return data.rc

def unregister_appbar(hwnd):
  data = APPBARDATA()
  data.cbSize = ctypes.sizeof(APPBARDATA)
  data.hWnd = wintypes.HWND(hwnd)
  SHAppBarMessage(ABM_REMOVE, ctypes.byref(data))

class DiagonalDotsWidget(QtWidgets.QWidget):
    def __init__(self, width_px=20, height_px=40, dot_color=QtGui.QColor("white"), dot_radius=1.5, parent=None):
        super().__init__(parent)
        self._w = int(width_px-5)
        self._h = int(height_px)
        self._dot_color = QtGui.QColor(dot_color)
        self._dot_radius = float(dot_radius)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        # keep fixed logical size (use scaled if your bar uses larger DPI)
        self.setFixedSize(self._w, self._h)

    def set_dot_color(self, qcolor):
        self._dot_color = QtGui.QColor(qcolor)
        self.update()

    def set_dot_radius(self, r):
        self._dot_radius = float(r)
        self.update()

    def paintEvent(self, event):
        # global cl
        global last_n_cache
        # global last_n_cache
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        # optional: draw rectangle border (uncomment if needed)
        # p.setPen(QtGui.QPen(QtGui.QColor(255,255,255,30)))

        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setColor(QtGui.QColor(255, 255, 255))

        # p.setPen(QtCore.Qt.NoPen)
        p.setPen(pen)
        p.setBrush(QtCore.Qt.NoBrush)   # no fill, just border
        p.drawRect(0,0,self._w-1,self._h-1)
        p.setBrush(self._dot_color)

        # p.drawRect(0,0,self._w-1,self._h-1)

        # number of points = min(width, height) to space evenly along diagonals
        # if index > 60 * 2 or index == 0:
        # last_n_cache = [ sgs.get('sg',0) for sgs in cl.carelink_get_last_n__blood_sugar_data(12)]
        # _n = [
        #         3,
        #         4.3,
        #         5.4,
        #         6.4,
        #         8.4,
        #         9.4,
        #         10.4,
        #         12.4,
        #         16.4,
        #         9.4,
        #         5.4,
        #         4.4,
        #      ]
        # _n = [ -9,-8,-7,-6,-5,-4,-3,-2,-1,0, 1,2,3,4,5,6,7,8,9 ]
        # _n = [ -9,9 ]
        # n = [ (self._h - x,(idx+1)*5) for idx,x in enumerate(_n) ]
        # n = [ (self._h - x, idx ) for idx,x in enumerate(_n) ]

        # n = [ ((idx+1)*3, self._h - x ) for idx,x in enumerate(_n) ]
        n = [ ((idx+1)*2.5, self._h - x *2) for idx,x in enumerate(last_n_cache) ]

        # n = [ ( idx, x ) for idx,x in enumerate(_n) ]
        # n = [ ( 9,9 ), (1,1), (-9,-9) ]
        # n = [ (1, self._h -3), ( 9.2, 9.3 ), (15.1,10.8) ]
        # n = max(2, min(self._w, self._h))
        # for i in range(n):
        # print(n)
        # print(self._h)
        for i in n:
            # compute evenly spaced coordinates along each diagonal
            # scale i to full width/height range
            # x = int(round(i * (self._w - 1) / (n - 1)))
            # y = int(round(i * (self._h - 1) / (n - 1)))
            x,y = i
            # draw dot on main diagonal (top-left -> bottom-right)
            cx = x + 0.5  # center pixel coordinate
            cy = y + 0.5
            # p.drawEllipse(QtCore.QPointF(cx, cy), self._dot_radius, self._dot_radius)
            p.drawPoint(QtCore.QPointF(x, y))

            # draw dot on opposite diagonal (top-right -> bottom-left)
            # ox = (self._w - 1 - x) + 0.5
            # oy = y + 0.5
            # p.drawEllipse(QtCore.QPointF(ox, oy), self._dot_radius, self._dot_radius)

        p.end()

class CircleWidget(QtWidgets.QWidget):
  def __init__(self, diameter=20, color=QtGui.QColor("white"), parent=None):
    super().__init__(parent)
    self._diameter = int(diameter)
    self._color = QtGui.QColor(color)
    # transparent background so it blends into the bar
    self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
    # keep a fixed logical size (you can adjust to fit bar)
    self.setFixedSize(self._diameter, self._diameter)

  def set_color(self, color):
    self._color = QtGui.QColor(color)
    self.update()

  def set_diameter(self, diameter):
    self._diameter = int(diameter)
    self.setFixedSize(self._diameter, self._diameter)
    self.update()

  def paintEvent(self, event):
    r = self.rect()
    painter = QtGui.QPainter(self)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(self._color)
    # draw circle centered in the widget, with slight padding
    pad = max(0, self._diameter // 12)
    rect = r.adjusted(pad, pad, -pad, -pad)
    painter.drawEllipse(rect)


# ---------------- Qt AppBar window ----------------
class TopBarWindow(QtWidgets.QWidget):
  def __init__(self, edge=ABE_TOP, thickness=36):
    super().__init__()
    self.edge = edge
    self.thickness = thickness

    flags = QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
    self.setWindowFlags(flags | QtCore.Qt.Tool)
    self.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)

    # SOLID BLACK OPAQUE BACKGROUND
    self.setAutoFillBackground(True)
    self.setStyleSheet("background-color: black;")
    # self.setWindowOpacity(1.0)

    # self.setFixedHeight(self.thickness)

    # sizing: for TOP/BOTTOM thickness is height; for LEFT/RIGHT thickness is width
    if self.edge in (ABE_LEFT, ABE_RIGHT):
        self.setFixedWidth(self.thickness)
        # self.setFixedWidth(50)
        # use vertical layout for left/right
        layout = QtWidgets.QVBoxLayout()
        # smaller margins for narrow bar
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)
        # layout.setSpacing(0)
    else:
        self.setFixedHeight(self.thickness)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

    # layout = QtWidgets.QHBoxLayout()
    # # layout.setContentsMargins(8, 4, 8, 4)
    # layout.setContentsMargins(4, 2, 4, 2)
    # # layout.setSpacing(10)
    # layout.setSpacing(6)

    self.widgets = []
    label_font = QtGui.QFont("Segoe UI", 8)
    # for label in ("CPU 12%", "Mem 11%", "Mail 3", "Clock"):
    for label in ("CPU 12%", "Mem 11%", "Clock", "BS"):
      w = QtWidgets.QLabel(label)
      w.setFont(label_font)
      w.setStyleSheet("border: 1px solid white; color: white; background: rgba(0,0,0,0); padding:4px;")
      w.setAlignment(QtCore.Qt.AlignCenter)
      # w.setStyleSheet("color: white; background: rgba(0,0,0,0); padding:0px;")
      # border: 1px solid white;
      # w.setFixedHeight(14)
      layout.addWidget(w)
      self.widgets.append(w)

    # circle = CircleWidget(diameter=max(12, self.thickness - 12), color=QtGui.QColor("white"))
    # layout.addWidget(circle)

    diag = DiagonalDotsWidget(width_px=40, height_px=40, dot_color=QtGui.QColor("white"), dot_radius=1.5)
    self.widgets.append(diag)
    layout.addWidget(diag)

    layout.addStretch()
    self.setLayout(layout)

    # self.bg_color = QtGui.QColor(0, 120, 215, 220)
    self.bg_color = QtGui.QColor(0, 0, 0, 255//2)  # slight transparency
    self.hwnd = None
    self.appbar_registered = False

  def showEvent(self, event):
    super().showEvent(event)
    if not self.appbar_registered:
      # ensure widget has native window and get HWND
      self.hwnd = int(self.winId())
      rc = register_appbar(self.hwnd, edge=self.edge, thickness=self.thickness)
      self.setGeometry(rc.left, rc.top, rc.right - rc.left, rc.bottom - rc.top)
      self.appbar_registered = True

  def paintEvent(self, event):
    p = QtGui.QPainter(self)
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setPen(QtCore.Qt.NoPen)
    p.setBrush(self.bg_color)
    # p.drawRoundedRect(self.rect(), 6, 6)
    p.drawRoundedRect(self.rect(), 2, 2)

  def closeEvent(self, event):
    if self.hwnd and self.appbar_registered:
      unregister_appbar(self.hwnd)
    super().closeEvent(event)

# ---------------- Tray + main ----------------
def make_tray_icon_pixmap(size=64, text="APP"):
  pix = QtGui.QPixmap(size, size)
  pix.fill(QtCore.Qt.transparent)
  p = QtGui.QPainter(pix)
  p.setRenderHint(QtGui.QPainter.Antialiasing)
  p.setBrush(QtGui.QColor(0,120,215))
  p.setPen(QtCore.Qt.NoPen)
  p.drawEllipse(0, 0, size-1, size-1)
  p.setPen(QtGui.QColor("white"))
  font = QtGui.QFont("Segoe UI", max(8, size//4), QtGui.QFont.Bold)
  p.setFont(font)
  fm = QtGui.QFontMetrics(font)
  w = fm.horizontalAdvance(text)
  h = fm.height()
  p.drawText((size-w)//2, (size+h)//2 - fm.descent(), text)
  p.end()
  return pix


def main():
  if sys.platform != "win32":
    print("Windows only")
    return

  app = QtWidgets.QApplication(sys.argv)
  app.setQuitOnLastWindowClosed(False)  # keep app alive when window closed (tray controls quit)

  # create top bar
  # bar = TopBarWindow(edge=ABE_TOP, thickness=24)
  bar = TopBarWindow(edge=ABE_LEFT, thickness=40)
  bar.show()

  # create tray icon
  tray = QtWidgets.QSystemTrayIcon()
  tray.setIcon(QtGui.QIcon(make_tray_icon_pixmap(64, "TSK")))
  tray.setToolTip("TopBar App")

  # context menu with Quit action
  menu = QtWidgets.QMenu()
  show_action = menu.addAction("Show/Hide Bar")
  quit_action = menu.addAction("Quit")
  tray.setContextMenu(menu)

  def toggle_bar():
    if bar.isVisible():
      bar.hide()
    else:
      bar.show()

  def quit_app():
    # unregister appbar if necessary and quit
    if bar.hwnd and bar.appbar_registered:
      unregister_appbar(bar.hwnd)
    tray.hide()
    QtCore.QTimer.singleShot(0, app.quit)

  show_action.triggered.connect(toggle_bar)
  quit_action.triggered.connect(quit_app)

  # double-click could toggle as well
  tray.activated.connect(lambda reason: toggle_bar() if reason == QtWidgets.QSystemTrayIcon.DoubleClick else None)

  tray.show()

  # 9 or 10pt
  # after creating `app = QApplication(...)` and creating windows/tray:
  def handle_sigint(signum, frame):
    # ask Qt to quit cleanly
    QtCore.QTimer.singleShot(0, app.quit)

  # install signal handler
  signal.signal(signal.SIGINT, handle_sigint)

  def update_status():
    global index
    global last_n_cache
    global cl
    """Update system status"""
    # while True:
      # try:
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    current_time = time.strftime("%H:%M:%S")

    # self.cpu_label.config(text=f"CPU: {cpu:.1f}%")
    # self.ram_label.config(text=f"")
    # self.time_label.config(text=current_time)

    # Update window title with info
    # self.root.title(f"Status Bar - CPU: {cpu:.1f}% | RAM: {ram:.1f}%")
    bar.widgets[0].setText(f"CPU\n{cpu:.0f}%")
    bar.widgets[1].setText(f"RAM\n{ram:.0f}%")
    bar.widgets[2].setText('\n'.join(current_time.split(':')))

    if index >= 60*2 or index == 0:
        cl.main()
        current_bs = cl.carelink_get_current_blood_sugar_level()
        last_n_cache = [ sgs.get('sg',0) for sgs in cl.carelink_get_last_n__blood_sugar_data(12)]
        bar.widgets[3].setText(str(current_bs))
        bar.widgets[4].update()
        index = 0
    else:
        index+=1
    # bar.widgets[-1].setText(QtCore.QTime.currentTime().toString("HH:mm:ss"))

      # except Exception as e:
      #    print(f"Update error: {e}")

  # cl = CareLink()
  # cl.main()
  # last_n = cl.carelink_get_last_n__blood_sugar_data()
  # current_bs = cl.carelink_get_current_blood_sugar_level()

  # small clock updater (optional)
  timer = QtCore.QTimer()
  timer.timeout.connect(update_status)
  timer.start(1000)

  sys.exit(app.exec())

if __name__ == "__main__":
  main()

