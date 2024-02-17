"""
Core codes of tkintertools

Structure of Class:
```text
+-------+       +-------------+
| tk.Tk |       | tk.Toplevel |
+-------+       +-------------+
    |                  |          +----------------------------+
    v                  v          |  Only works on Windows OS  |
+--------+      +--------------+  |   +--------------------+   |
| tkt.Tk | ---> | tkt.Toplevel | -+-> | tkt.NestedToplevel |   |
+--------+      +--------------+  |   +--------------------+   |
                                  +----------------------------+
+-----------+        +------------+
| tk.Canvas | -----> | tkt.Canvas |
+-----------+        +------------+
               +-------+
               | Image |
               +-------+
                   |
                   v
+-------+      +--------+      +------+
| Shape | ---> | Widget | <--- | Text |
+-------+      +--------+      +------+
                   ^
                   |
               +---------+
               | Feature |
               +---------+
```
"""

import ctypes
import math
import platform
import tkinter
import typing
from tkinter import font

from . import _tools, color, constants

if platform.system() == "Windows":  # Set DPI awareness
    ctypes.WinDLL("shcore").SetProcessDpiAwareness(1)


class Tk(tkinter.Tk):
    """
    Main window

    In general, there is only one main window
    """

    def __init__(
        self,
        size: tuple[int, int] = (1280, 720),
        position: tuple[int, int] | None = None,
        *,
        title: str = "",
        **kw,
    ) -> None:
        """
        * `size`: the size of the window, default value is 1280x720(px)
        * `position`: the position of the window, default value indicates that the location is random
        * `title`: the title of the window, default value is an empty string
        * `**kw`: compatible with other parameters of class `tkinter.Tk`
        """
        if self.__class__ == Tk:  # NOTE: Subclasses of tkt.Tk do not inherit tk.Tk
            tkinter.Tk.__init__(self, **kw)

        self._initial_size = list(size)
        self._size = self._initial_size[:]
        self._ratio = [1., 1.]
        self._canvases: list[Canvas] = []
        self._theme: dict[str, str | bool | None] = self.master._theme if isinstance(
            self.master, tkinter.Wm) else {}

        self.title(title)
        self.theme(**self._theme)
        self.geometry(size=size, position=position)

        self.bind("<Configure>", lambda _: self._zoom())

    def geometry(
        self,
        *,
        size: tuple[int, int] | None = None,
        position: tuple[int, int] | None = None
    ) -> tuple[int, int, int, int] | None:
        """
        Change the size and position of the window and return the current size and position of the window

        * `size`: the size of the window, if it is None, does not change anything
        * `position`: the position of the window, if it is None, does not change anything
        """
        if size is not None and position is not None:
            self.wm_geometry(
                f"{size[0]}x{size[1]}+{position[0]}+{position[1]}")
        elif size is not None:
            self.wm_geometry(f"{size[0]}x{size[1]}")
        elif position is not None:
            self.wm_geometry(f"+{position[0]}+{position[1]}")
        return *self._size, self.winfo_x(), self.winfo_y()

    def get_canvases(self) -> tuple["Canvas", ...]:
        """Retrun all instances of `Canvas` of the window"""
        return tuple(self._canvases)

    def center(self) -> None:
        """Center the window"""
        # self.update()  # ALPHA: What is the chance that the center will fail without this line of code?
        if self.master is None or self.__class__ == Toplevel:
            parent_width = self.winfo_screenwidth()
            parent_height = self.winfo_screenheight()
        else:
            parent_width = self.master._size[0]
            parent_height = self.master._size[1]
        x = (parent_width - self._size[0]) // 2
        y = (parent_height - self._size[1]) // 2
        self.geometry(position=(x, y))

    def _zoom(self) -> None:
        """Internal Method: Zoom contents of the window"""
        # self.update()  # ALPHA
        if self._size != (size := [self.winfo_width(), self.winfo_height()]):
            self._size = size
            self._ratio[0] = self._size[0] / self._initial_size[0]
            self._ratio[1] = self._size[1] / self._initial_size[1]
            for canvas in self._canvases:
                canvas._zoom()

    def theme(
        self,
        *,
        dark: bool | None = None,
        bordercolor: str | None = None,
        captioncolor: str | None = None,
        titlecolor: str | None = None,
        background: str | None = None,
    ) -> None:
        """
        Change the theme of the window

        * `dark`: whether it is in dark mode
        * `bordercolor`: window border color
        * `captioncolor`: window caption color
        * `titlecolor`: window title color
        * `background`: window background color

        ATTENTION: some parameter only works on Windows OS!
        """
        self.update()
        try:
            HWND = ctypes.windll.user32.GetParent(self.winfo_id())
            if dark is None:
                dark = _tools._is_dark()
            if dark is not None:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    HWND, 20, ctypes.byref(ctypes.c_int(dark)), 4)
            for i, value in enumerate((bordercolor, captioncolor, titlecolor)):
                if value is not None:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        HWND, 34 + i, ctypes.byref(ctypes.c_int(color.str_to_hex(value, reverse=True))), 4)
        except:
            _tools._warning(
                "Some parameters are not available on the current OS!")
        if background is not None:
            self["bg"] = background
        self._theme.update(
            dark=dark, bordercolor=bordercolor, captioncolor=captioncolor,
            titlecolor=titlecolor, background=background)

    def alpha(self, value: float | None = None) -> float | None:
        """
        Set or get the transparency of the window

        * `value`: the transparency of the window, range is 0~1
        """
        return self.attributes("-alpha", value)

    def fullscreen(self, value: bool | None = True) -> bool | None:
        """
        Set or get whether the window is full-screen

        * `value`: indicate whether the window is full-screen

        ATTENTION: This method should be called later
        """
        self.update()
        if value is None:
            return bool(self.attributes("-fullscreen"))
        self.attributes("-fullscreen", value)
        if not value:  # When you cancel the full-screen state, the `theme` method is invalidated
            self.theme(**self._theme)

    def toolwindow(self, value: bool | None = True) -> bool | None:
        """
        Set or get whether the window is tool-window

        * `value`: indicate whether the window is tool-window
        """
        return bool(self.attributes("-toolwindow", value))

    def topmost(self, value: bool | None = True) -> bool | None:
        """
        Set or get whether the window is pinned or not

        * `value`: indicate whether the window is topmost
        """
        return bool(self.attributes("-topmost", value))

    def transparentcolor(self, value: str | None = None) -> str | None:
        """
        Set or get the penetration color of the window

        * `value`: the penetration color of the window
        """
        return self.attributes("-transparentcolor", value)

    def shutdown(self, func: typing.Callable | None, *args, **kw) -> None:
        """
        Set a function that will be called when the window is closed

        * `func`: the function that was called
        * `*args`: the variable-length argument of the called function
        * `**kw`: the keyword argument of the function being called

        ATTENTION: Regardless of whether the function is successfully called or not,
        the window will still close gracefully
        """
        def _wrapper() -> None:
            """Ensure that the window closes gracefully"""
            try:
                func(*args, **kw)
            finally:
                self.destroy()
        self.protocol("WM_DELETE_WINDOW", _wrapper)


class Toplevel(tkinter.Toplevel, Tk):
    """
    Toplevel window

    It can be used as a pop-up window, or it can be customized to put anything you want to show in it
    """

    def __init__(
        self,
        master: Tk | typing.Self | "NestedToplevel" | None = None,
        size: tuple[int, int] = (960, 540),
        position: tuple[int, int] | None = None,
        *,
        title: str | None = None,
        transient: bool = False,
        focus: bool = True,
        **kw,
    ) -> None:
        """
        * `master`: parent widget
        * `size`: the size of the window, default value is 960x540(px)
        * `position`: the position of the window, default value indicates that the location is random
        * `title`: title of window, default is the same as title of master
        * `transient`: instruct the window manager that this window is transient with regard to its master
        * `focus`: whether direct input focus to this window
        * `**kw`: compatible with other parameters of class `tkinter.Toplevel`
        """
        tkinter.Toplevel.__init__(self, master, **kw)
        Tk.__init__(self, size, position, title=title)
        if focus:
            self.focus_set()
        if transient:
            self.transient(self.master)


class NestedToplevel(Toplevel):
    """
    A window nested within another window

    ATTENTION: this CLASS only works on Windows OS
    """

    def __init__(
        self,
        master: Tk | Toplevel | typing.Self | "Canvas" | None = None,
        size: tuple[int, int] = (640, 360),
        position: tuple[int, int] | None = None,
        *,
        title: str | None = None,
        transient: bool = False,
        focus: bool = False,
        **kw,
    ) -> None:
        """
        * `master`: parent widget
        * `size`: the size of the window, default value is 640x360(px)
        * `position`: the position of the window, default value indicates that the location is random
        * `title`: title of window, default is the same as title of master
        * `transient`: instruct the window manager that this window is transient with regard to its master
        * `focus`: whether direct input focus to this window
        * `**kw`: compatible with other parameters of class `tkinter.Toplevel`
        """
        if platform.system() != "Windows":
            raise RuntimeError("This CLASS only works on Windows OS!")
        Toplevel.__init__(self, master, size, position,
                          title=title, transient=transient, **kw)
        self._handle = ctypes.windll.user32.GetParent(self.winfo_id())
        self._nested(self.master, focus=focus)

    def _nested(self, parent: tkinter.Misc | None = None, *, focus: bool = False) -> None:
        """
        Internal Method: Nest the window in its parent

        * `parent`: parent widget
        * `focus`: whether direct input focus to this window
        """
        ctypes.windll.user32.SetParent(
            self._handle, parent.winfo_id() if parent else None)
        if not focus:
            self.master.focus_set()


class Canvas(tkinter.Canvas):
    """
    Scalable Canvas

    The parent widget of all widgets of tkintertools is Canvas
    """

    def __init__(
        self,
        master: Tk | Toplevel | NestedToplevel | typing.Self,
        *,
        expand: typing.Literal["", "x", "y", "xy"] = "xy",
        keep_ratio: typing.Literal["min", "max", "full"] | None = None,
        free_anchor: bool = False,
        **kw,
    ) -> None:
        """
        * `master`: parent widget
        * `expand`: the mode of expand, `x` is horizontal, and `y` is vertical
        * `keep_ratio`: the mode of aspect ratio, `min` follows the minimum value,
        `max` follows the maximum value, and `full` follows the maximum possible value
        * `free_anchor`: whether the anchor point is free-floating
        * `**kw`: compatible with other parameters of class `tkinter.Canvas`
        """
        tkinter.Canvas.__init__(self, master, **kw)
        self._initial_size = [None, None]
        self._size = self._initial_size[:]
        self._initial_position = [None, None]
        self._position = self._initial_position[:]
        self._ratio = [1., 1.]

        self._canvases: list[Canvas] = []
        self._widgets: list[Widget] = []
        self._items: list[int] = []
        self._texts: dict[int, list[int, font.Font]] = {}
        self._images: dict[int, list[Image]] = {}

        self._expand = expand
        self._free_anchor = free_anchor
        self._keep_ratio = keep_ratio

        self.master._canvases.append(self)

        self.bind("<Motion>", self._touch)
        self.bind("<Any-Key>", self._input)
        self.bind("<Button-1>", self._click)
        self.bind("<Button-2>", self._click)
        self.bind("<Button-3>", self._click)
        self.bind("<B1-Motion>", self._touch)
        self.bind("<B2-Motion>", self._touch)
        self.bind("<B3-Motion>", self._touch)
        self.bind("<MouseWheel>", self._wheel)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<ButtonRelease-2>", self._release)
        self.bind("<ButtonRelease-3>", self._release)
        self.bind("<Configure>", lambda _: self._zoom_self())

    def get_canvases(self) -> tuple[typing.Self, ...]:
        """Retrun all child `Canvas` of the `Canvas`"""
        return tuple(self._canvases)

    def get_widgets(self) -> tuple["Widget", ...]:
        """Retrun all `Widget` of the `Canvas`"""
        return tuple(self._widgets)

    def get_items(self) -> tuple[int, ...]:
        """Retrun all items of the `Canvas`"""
        return tuple(self._items)

    def get_texts(self) -> tuple[int, ...]:
        """Retrun all texts of the `Canvas`"""
        return tuple(self._texts)

    def get_images(self) -> tuple[int, ...]:
        """Retrun all image of the `Canvas`"""
        return tuple(self._images)

    def _zoom_init(self) -> None:
        """"""
        self._size = self._initial_size = [
            self.winfo_width(), self.winfo_height()]

        anchor = self.place_info().get("anchor", None)
        if anchor == "nw" or anchor == None:
            dx = 0
            dy = 0
        elif anchor == "n":
            dx = self._initial_size[0] // 2
            dy = 0
        elif anchor == "w":
            dx = 0
            dy = self._initial_size[1] // 2
        elif anchor == "ne":
            dx = self._initial_size[0]
            dy = 0
        elif anchor == "sw":
            dx = 0
            dy = self._initial_size[1]
        elif anchor == "e":
            dx = self._initial_size[0]
            dy = self._initial_size[1] // 2
        elif anchor == "s":
            dx = self._initial_size[0]
            dy = self._initial_size[1] // 2
        elif anchor == "se":
            dx = self._initial_size[0]
            dy = self._initial_size[1]
        else:
            dx = self._initial_size[0] // 2
            dy = self._initial_size[1] // 2

        self._position = self._initial_position = [
            self.winfo_x()+dx, self.winfo_y()+dy]

    def _zoom(self) -> None:
        """Internal Method: Relative zooming for contents of the `Canvas`"""
        if not self.winfo_viewable():
            return
        if self.place_info():  # 仅 Place 布局
            if self._keep_ratio == "max":
                ratio_x = ratio_y = max(self.master._ratio)
            elif self._keep_ratio == "min":
                ratio_x = ratio_y = min(self.master._ratio)
            elif self._keep_ratio == "full":
                ratio_x = self.master._size[0] / self._initial_size[0]
                ratio_y = self.master._size[1] / self._initial_size[1]
                ratio_x = ratio_y = min(ratio_x, ratio_y)
            else:
                ratio_x, ratio_y = self.master._ratio
            if "x" in self._expand:
                self.place(width=self._initial_size[0]*ratio_x)
            if "y" in self._expand:
                self.place(height=self._initial_size[1]*ratio_y)
            if self._free_anchor:
                self.place(x=self._initial_position[0]*self.master._ratio[0],
                           y=self._initial_position[1]*self.master._ratio[1])

    def _zoom_self(self) -> None:
        """Internal Method: Scale the `Canvas` itself, and return its own relative scale"""
        if self._initial_size == [None, None]:
            self._zoom_init()
        last_ratio = self._size[:]
        self._position = [self.winfo_x(), self.winfo_y()]
        self._size = [self.winfo_width(), self.winfo_height()]
        self._ratio = [self._size[0] / self._initial_size[0],
                       self._size[1] / self._initial_size[1]]

        relative_ratio = self._size[0] / \
            last_ratio[0], self._size[1] / last_ratio[1]
        self._zoom_widgets(relative_ratio)
        self._zoom_items(relative_ratio)
        self._zoom_texts(relative_ratio)
        self._zoom_images(relative_ratio)

        for canvas in self._canvases:
            canvas._zoom()

    def _zoom_widgets(self, relative_ratio: tuple[float, float]) -> None:
        """控件数据修改"""
        for widget in self._widgets:
            widget.shape._size[0] *= relative_ratio[0]
            widget.shape._size[1] *= relative_ratio[1]
            widget.shape._position[0] *= relative_ratio[0]
            widget.shape._position[1] *= relative_ratio[1]

    def _zoom_items(self, relative_ratio: tuple[float, float]) -> None:
        """元素位置缩放"""
        for item in self.find_all():
            self.coords(item, *[c * relative_ratio[i & 1]
                        for i, c in enumerate(self.coords(item))])

    def _zoom_texts(self, relative_ratio: tuple[float, float]) -> None:
        """字体大小缩放"""
        for text, value in self._texts.items():
            value[0] *= math.sqrt(relative_ratio[0]*relative_ratio[1])
            font_ = value[1].copy()
            font_.config(size=round(value[0]))
            self.itemconfigure(text, font=font_)

    def _zoom_images(self, relative_ratio: tuple[float, float]) -> None:
        """图像大小缩放（采用相对的绝对缩放）"""
        # for image, value in self._images.items():
        #     if value[0] and value[0].extension != "gif":
        #         value[1] = value[0].zoom(
        #             temp_x * rate_x, temp_y * rate_y, precision=1.2)
        #         self.itemconfigure(image, image=value[1])

    def destroy(self) -> None:
        # Override: 兼容原生 tkinter 的容器控件
        if _canvases := getattr(self.master, "_canvases", None):
            _canvases.remove(self)
        return tkinter.Canvas.destroy(self)

    def create_text(self, *args, **kw) -> int:
        # Override: 添加对 text 类型的 _CanvasItemId 的字体大小的控制
        if not (font_ := kw.get("font")):
            kw["font"] = font.Font(family=constants.FONT, size=constants.SIZE)
        elif isinstance(font_, str):
            kw["font"] = font.Font(family=font_, size=constants.SIZE)
        elif isinstance(font_, int):
            kw["font"] = font.Font(family=constants.FONT, size=-abs(font_))
        elif isinstance(font_, font.Font):
            kw["font"].config(size=-abs(font_.cget("size")))
        else:
            font_ = list(font_)
            font_[1] = -abs(font_[1])
            length = len(font_)
            kw["font"] = font.Font(family=font_[0], size=font_[1],
                                   weight=font_[2] if length > 2 else "normal",
                                   slant=font_[3] if length > 3 else "roman")
            # XXX
        text = tkinter.Canvas.create_text(self, *args, **kw)
        self._texts[text] = [kw["font"].cget("size"), kw["font"]]
        return text

    def create_image(self, *args, **kw) -> int:
        # Override: 添加对 image 类型的 _CanvasItemId 的图像大小的控制
        image = tkinter.Canvas.create_image(self, *args, **kw)
        self._images[image] = [kw.get("image"), None]
        if self._images[image][0].__class__ == Image:
            self._images[image][0] = self._images[image][0].image
        return image

    def itemconfigure(self, tagOrId: str | int, **kw) -> dict[str, tuple[str, str, str, str, str]] | None:
        # Override: 创建空 image 的 _CanvasItemId 时漏去对图像大小的控制
        if kw.get("image").__class__ == Image:
            self._images[tagOrId] = [kw.get("image"), None]
        return tkinter.Canvas.itemconfigure(self, tagOrId, **kw)

    def _touch(self, event: tkinter.Event) -> bool:
        """"""
        for widget in self.get_widgets()[::-1]:
            if widget.feature._touch(event):
                # if not widget._through:
                #     continue
                return True
        self.configure(cursor="arrow")
        return False

    def _click(self, event: tkinter.Event) -> bool:
        """"""
        for widget in self.get_widgets()[::-1]:
            if widget.feature._click(event):
                if widget._through:
                    continue
                return True
        return False

    def _release(self, event: tkinter.Event) -> bool:
        """"""
        for widget in self.get_widgets()[::-1]:
            if widget.feature._release(event):
                if widget._through:
                    continue
                return True
        return False

    def _wheel(self, event: tkinter.Event) -> bool:
        """"""
        for widget in self.get_widgets()[::-1]:
            if widget.feature._wheel(event):
                if widget._through:
                    continue
                return True
        return False

    def _input(self, event: tkinter.Event) -> bool:
        """"""
        for widget in self.get_widgets()[::-1]:
            if widget.feature._input(event):
                if widget._through:
                    continue
                return True
        return False


class Shape:
    """
    Base Class: The Shape of a `Widget`

    You can view all of its standard derivatives in file: shapes.py
    """

    def __init__(self) -> None:
        self._master: Canvas | None = None
        self._size: list[int, int] = [None, None]
        self._position: list[int, int] = [None, None]
        self._items_inside: list[int] = []
        self._items_outline: list[int] = []
        self._is_transparency: bool = False
        self._temp_data: tuple[list[str]] = [], []
        self._id: str = hex(id(self))[2:]

    def borderwidth(self, value: int | None) -> int | None:
        """
        Set or get the borderwidth of the `Shape`

        * `value`: the borderwidth of the `Shape` 
        """
        if value is None:
            return self._master.itemcget(self._items_outline[0], "width")
        for item in self._items_outline:
            self._master.itemconfigure(item, width=value)

    def center(self) -> tuple[int, int]:
        """Return the geometric center of the `Shape`"""
        return tuple(p + s // 2 for p, s in zip(self._position, self._size))

    def region(self) -> tuple[int, int, int, int]:
        """Return the decision region of the `Shape`"""
        width, height = self._size
        x, y = self._position
        return x, y, x+width, y+height

    def move(self, dx: int, dy: int) -> None:
        """Move the `Shape`"""
        self._position[0] += dx
        self._position[1] += dy
        for item in self._master.find_withtag(self._id):
            self._master.move(item, dx, dy)

    def moveto(self, x: int, y: int) -> None:
        """Move the `Shape` to a certain position"""
        return self.move(x-self.region[0], y-self.region[1])

    def destroy(self) -> None:
        """Destroy the `Shape`"""
        self._master.delete(*self._master.find_withtag(self._id))
        self._items_inside.clear()
        self._items_outline.clear()
        self._master = None

    def disappear(self) -> bool:
        """
        Let the `Shape` disappear

        ATTENTION: Instead of clearing the shape, making the shape disappear is not clearing the shape,
        you can use the `appear` method to restore the original state
        """
        if self._is_transparency:
            return False
        for item in self._items_inside:
            self._temp_data[0].append(self._master.itemcget(item, "fill"))
            self._master.itemconfigure(item, fill="")
        for item in self._items_outline:
            self._temp_data[1].append(self._master.itemcget(item, "outline"))
            self._master.itemconfigure(item, outline="")
        return True

    def appear(self) -> bool:
        """
        Let the `Shape` appear

        ATTENTION: Contrary to the effect of the method disappear
        """
        if not self._is_transparency:
            return False
        for item, data in zip(self._items_inside, self._temp_data[0]):
            self._master.itemconfigure(item, fill=data)
        for item, data in zip(self._items_outline, self._temp_data[1]):
            self._master.itemconfigure(item, outline=data)
        self._temp_data = [], []
        return True

    def detect(self, position: tuple[int, int]) -> bool:
        """
        Detect whether the specified coordinates are within the `Shape`

        * `position`: the specified coordinates
        """
        if all(0 <= (position[i] - self._position[i]) <= self._size[i] for i in range(2)):
            return True
        return False

    def display(self, master: Canvas, size: tuple[int, int], position: tuple[int, int]) -> None:
        """
        Display the `Shape` on a `Canvas`

        * `master`: a Canvas
        * `size`: the size of the `Shape`
        * `position`: the position of the `Shape`
        """
        self._master = master
        self._size = list(size)
        self._position = list(position)
        item = master.create_rectangle(*self.region(), tags=id(self))
        self._items_inside.append(item)
        self._items_outline.append(item)

    def configure(self, fill: str | None = None, outline: str | None = None) -> None:
        """"""
        if fill is not None:
            for item in self._items_inside:
                self._master.itemconfigure(item, fill=fill)
        if outline is not None:
            for item in self._items_outline:
                self._master.itemconfigure(item, outline=outline)


class Text:
    """Base Class: The text of a `Widget`"""

    def __init__(
        self,
        text: str = "",
        *,
        family: str = constants.FONT,
        size: int = constants.SIZE,
        weight: typing.Literal["normal", "bold"] = "normal",
        slant: typing.Literal["roman", "italic"] = "roman",
        underline: bool = False,
        overstrike: bool = False,
        anchor: typing.Literal["n", "w", "s", "e", "nw",
                               "ne", "sw", "se", "center"] = "center",
        justify: typing.Literal["left", "center", "right"] = "left",
        angle: float = 0,
        limit: int = math.inf,
        cursor: str = "|",
        show: str | None = None,
        read_only: bool = False,
        bbox_limit: tuple[int, int, int, int] | None = None,
    ) -> None:
        """
        * `text`: the value of `Text`

        * `anchor`: anchor mode of value
        * `justify`: justify mode of value
        * `angle`: rotation angle of value
        * `limit`: the limitation of value length
        * `cursor`: 
        * `show`: 
        * `read_only`: 
        * `bbox_limit`: 
        """
        self._master: Canvas | None = None
        self._length: int = len(text)
        self._position: list[int, int] = [None, None]
        self._text: str = text
        self._font: font.Font = font.Font(
            family=family, size=size, weight=weight, slant=slant,
            underline=underline, overstrike=overstrike)
        self._anchor: typing.Literal["n", "w", "s", "e",
                                     "nw", "ne", "sw", "se", "center"] = anchor
        self._justify: typing.Literal["left", "center", "right"] = justify
        self._angle: int = angle
        self._limit: int = limit
        self._cursor: str = cursor
        self._show: str | None = show
        self._read_only: bool = read_only
        self._bbox_limit: tuple[int, int, int, int] = bbox_limit
        self._items: list[int] = []
        self._is_transparency: bool = False
        self._temp_data: list[str] = []

    def center(self) -> tuple[int, int]:
        """Return the geometric center of the `Text`"""
        return tuple(self._position)

    def region(self) -> tuple[int, int, int, int]:
        """Return the decision region of the `Text`"""
        width_half = self._font.measure(self._text)/2
        height_half = -self._font.cget("size") / 2
        x, y = self._position
        return x-width_half, y-height_half, x+width_half, y+height_half

    def move(self, dx: int, dy: int) -> None:
        """Move the `Text`"""
        self._position[0] += dx
        self._position[1] += dy
        for item in self._items:
            self._master.move(item, dx, dy)

    def moveto(self, x: int, y: int) -> None:
        """Move the `Text` to a certain position"""
        return self.move(x-self.region[0], y-self.region[1])

    def destroy(self) -> None:
        """Destroy the `Text`"""
        self._master.delete(*self._items)
        self._items.clear()
        self._master = None

    def disappear(self) -> bool:
        """
        Let the `Text` disappear

        ATTENTION: Instead of clearing the text, making the text disappear is not clearing the text,
        you can use the `appear` method to restore the original state
        """
        if self._is_transparency:
            return False
        for item in self._items:
            self._temp_data.append(self._master.itemcget(item, "fill"))
            self._master.itemconfigure(item, fill="")
        return True

    def appear(self) -> bool:
        """
        Let the `Text` appear

        ATTENTION: Contrary to the effect of the method disappear
        """
        if not self._is_transparency:
            return False
        for item, data in zip(self._items, self._temp_data):
            self._master.itemconfigure(item, fill=data)
        self._temp_data.clear()
        return True

    def detect(self, position: tuple[int, int]) -> bool:
        """
        Detect whether the specified coordinates are within the `Text`

        * `position`: the specified coordinates
        """
        x1, y1, x2, y2 = self.region()
        if 0 <= position[0] - x1 <= x2 and 0 <= position[1] - y1 <= y2:
            return True
        return False

    def get(self) -> str:
        """Get the value of `Text`"""
        return self._text

    def set(self, text: str) -> None:
        """Set the value of `Text`"""
        if (length := len(text)) > self._limit:
            raise ValueError
        self._text = text
        self._length = length
        self.configure()

    def append(self, text: str) -> None:
        """Append value to the value of `Text`"""
        if self._length + (length := len(text)) > self._limit:
            raise ValueError
        self._text = self._text + text
        self._length += length
        self.configure()

    def delete(self, num: int) -> None:
        """Remove a portion of the `Text` value from the trail"""
        if num > self._length:
            raise ValueError
        self._text = self._text[:-num]
        self._length -= num
        self.configure()

    def clear(self) -> None:
        """Clear the value of `Text`"""
        self._text = ""
        self._length = 0
        self.configure()

    def display(self, master: Canvas, position: tuple[int, int]) -> None:
        """
        Display the `Text` on a `Canvas`

        * `master`: a Canvas
        * `position`: the position of the `Shape`
        """
        self._master = master
        self._position = position
        self._items.append(master.create_text(
            *position, text=self._text, font=self._font,
            angle=self._angle, anchor=self._anchor))

    def configure(
        self,
        *,
        text: str | None = None,
        family: str | None = None,
        size: int | None = None,
        weight: typing.Literal["normal", "bold"] | None = None,
        slant: typing.Literal["roman", "italic"] | None = None,
        underline: bool | None = None,
        overstrike: bool | None = None,
        anchor: typing.Literal["n", "w", "s", "e", "nw",
                               "ne", "sw", "se", "center"] | None = None,
        justify: typing.Literal["left", "center", "right"] | None = None,
        angle: float | None = None,
        fill: str | None = None
    ) -> None:
        """Modify the properties of `Text`"""
        self._text = self._text if text is None else text

        if family is not None:
            self._font.config(family=family)
        if size is not None:
            self._font.config(size=size)
        if weight is not None:
            self._font.config(weight=weight)
        if slant is not None:
            self._font.config(slant=slant)
        if underline is not None:
            self._font.config(underline=underline)
        if overstrike is not None:
            self._font.config(overstrike=overstrike)

        self._anchor = self._anchor if anchor is None else anchor
        self._justify = self._justify if justify is None else justify
        self._angle = self._angle if angle is None else angle
        for item in self._items:
            if self._master.itemcget(item, "tag") == "cursor":
                continue
            self._master.itemconfigure(
                item, text=self._text, font=self._font, justify=self._justify,
                angle=self._angle, anchor=self._anchor)
            if fill is not None:
                self._master.itemconfigure(item, fill=fill)


class Image(tkinter.PhotoImage):
    """Base Class: an image of a `Widget`"""

    def __init__(
        self,
        filepath: str
    ) -> None:
        """"""
        self.filepath = filepath
        self.extension = self._get_extension()
        self.image = None

    def _get_extension(self) -> str:
        """Internal Method: Get extension of the image file"""
        if "." in self.filepath:
            return self.filepath.rsplit(".", 1)[-1]
        return ""


class Feature:
    """Base Class: The features of a `Widget`"""

    def __init__(
        self
    ) -> None:
        """"""
        self.master: Widget | None = None
        self._state: typing.Literal["normal", "hover",
                                    "click", "error", "disabled"] | None = None
        self._data_shape: list[dict[str, str]] = []
        self._data_text: list[dict[str, str]] = []
        self._data_image: list[dict[str, str]] = []

    def bind(self, master: "Widget") -> None:
        """"""
        self.master = master

    def _touch(self, event: tkinter.Event) -> bool:
        """"""
        return False

    def _click(self, event: tkinter.Event) -> bool:
        """"""
        return False

    def _release(self, event: tkinter.Event) -> bool:
        """"""
        return False

    def _wheel(self, event: tkinter.Event) -> bool:
        """"""
        return False

    def _input(self, event: tkinter.Event) -> bool:
        """"""
        return False


class Widget:
    """
    Base Widget Class

    `Widget` = [`Shape`] + [`Text`] + [`Image`] + `Feature`
    """

    def __init__(
        self,
        master: Canvas,
        size: tuple[int, int],
        position: tuple[int, int],
        *,
        shape: Shape,
        text: Text,
        feature: Feature,
        image: Image | None = None,
        through: bool = False
    ) -> None:
        """"""
        self.master = master
        self._size = size
        self._position = position
        self._through = through

        self.shape = shape
        self.feature = feature
        self.text = text
        self.image = image

        self.shape.display(master, size, position)
        self.text.display(master, [p + s / 2 for p, s in zip(position, size)])
        self.feature.bind(self)
        self.master._widgets.append(self)

    def destroy(self) -> None:
        """Destroy the `Widget`"""
        self.shape.destroy()
        self.text.destroy()

    def move(self, dx: int, dy: int) -> None:
        """"""
        self.shape.move(dx, dy)
        self.text.move(dx, dy)

    def moveto(self, x: int, y: int) -> None:
        """"""
        self.shape.moveto(x, y)
        self.text.moveto(x, y)

    def disappear(self) -> None:
        """"""
        self.shape.disappear()
        self.text.disappear()

    def appear(self) -> None:
        """"""
        self.shape.appear()
        self.text.appear()

    @typing.overload
    def state(self) -> str: ...

    @typing.overload
    def state(self, __state: typing.Literal['default',
              'hover', 'selected', 'disabled', 'error']) -> None: ...

    def state(self, __state: typing.Literal['default', 'hover', 'selected', 'disabled', 'error'] | None = None) -> str | None:
        """"""

    def configure(self) -> None:
        """"""
