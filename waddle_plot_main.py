import pickle
import tkinter as tk
#from tkinter import ttk
import tkinter.ttk as ttk
import turtle
from tkinter.constants import *
import time
import threading
# TODO: Why do I need the following? What's going on with the namespace?
from tkinter import Checkbutton
from tkinter import IntVar
from tkinter import Menu
from tkinter import filedialog as fd

import planar
from planar import Vec2
from waddle_plot import Wad, LineDefs, SideDefs, Vertexes, Level
from pickle import dump, load

from math import isclose
import zipfile

class MapViewer(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        tk.Frame.pack(self)
        self.menubar = Menu(self)
        file = Menu(self.menubar, tearoff=0)
        file.add_command(label="Open a wadfile/zip archive of wadfiles...", command=self.openFile_dialog)
        self.menubar.add_cascade(label="File", menu=file)

        # Canvas
        self.canvas = tk.Canvas(width=800, height=600)
        self.canvas.pack(side="bottom")
        #self.canvas.configure(scrollregion=(-640, -360, 640, 360))

        # Labels from level stats
        """self.map_stats_frame = tk.LabelFrame(master=self)
        #self.map_stats_frame.__init__(self)
        self.map_stats_frame.pack(side="right")
        self.map_stats = {"vertexnum_label": tk.Label(master=self.map_stats_frame, text="Vertexes")}
        self.map_stats["vertexnum_label"].pack(side="left", padx=5, pady=5)"""

        self.vnum = None
        self.onLine = None


        # turtle opts
        self.t_turtle = turtle.RawTurtle(self.canvas)

        # Trying to add a 2nd turtle for concurrent drawing..
        self.t_turtle2 = turtle.RawTurtle(self.canvas)

        self.screen = self.t_turtle.getscreen()
        self.ONE_SIDED_COLOR = "GREEN"
        self.TWO_SIDED_COLOR = "RED"
        self.BACKGROUND_COLOR = "BLACK"
        self.screen.bgcolor(self.BACKGROUND_COLOR)
        # Menubar - NOT working. Something is going on with the namespace....


        # buttons
        prevmap_btn = tk.Button(self, text="Prev MAP", command=self.prev_map)
        prevmap_btn.pack(side="left", padx=5, pady=5)
        nextmap_btn = tk.Button(self, text="Next MAP", command=self.next_map)
        nextmap_btn.pack(side="left", padx=5, pady=5)
        # Map Select Box Widget
        map_select_label = ttk.Label(text="MAP:")
        map_select_label.pack(side="left")

        self.selected_map_var = tk.StringVar()
        self.selected_map_box = ttk.Combobox(textvariable=self.selected_map_var)
        self.selected_map_box.bind('<<ComboboxSelected>>', self.cb_change_map)

        # var for Checkbutton state
        self.cb = IntVar()

        # Animate Checkbutton
        self.anim_check_btn = Checkbutton(self, text="Live-Plot(slow)", variable=self.cb, onvalue=1, offvalue=0, state=NORMAL, command=self.isChecked)
        self.anim_check_btn.pack(side="left", padx=5, pady=5)


        # Progress Bar (on draw) - can't get working
        #self.progress_bar = ttk.Progressbar(orient=tk.HORIZONTAL, mode='determinate')
        #self.progress_bar.pack(side="right", padx=5, pady=5)
        # DEBUGGING ==========================================================
        # self.debug_points = self.getPoints("vectors.bin")
        # self.canvas.create_line()
        # ===================================================================
        # ============================|
        # These two are set...      # |
        self._wadfile = None        # |
        self.level = None           # |
        # =============================
        # here...                   # |
        self.game = "DOOM"
        # to load and display a level at startup from a static location
        # self.loadWad("C:\Pydevel\WOS.wad")    # |
        # self.loadLevel("MAP01")      # |
        # =============================
        # Need a better way than this...
        self.doom_maps = ["E1M1", "E1M2", "E1M3", "E1M4", "E1M5", "E1M6", "E1M7", "E1M8", "E1M9",
                          "E2M1", "E2M2", "E2M3", "E2M4", "E2M5", "E2M6", "E2M7", "E2M8", "E2M9",
                          "E3M1", "E3M2", "E3M3", "E3M4", "E3M5", "E3M6", "E3M7", "E3M8", "E3M9",
                          "E4M1", "E4M2", "E4M3", "E4M4", "E4M5", "E4M6", "E4M7", "E4M8", "E4M9"]
        self.doom2_maps = ["MAP01", "MAP02", "MAP03", "MAP04", "MAP05", "MAP06", "MAP07", "MAP08", "MAP09", "MAP10",
                           "MAP11", "MAP12", "MAP13", "MAP14", "MAP15", "MAP16", "MAP17", "MAP18", "MAP19", "MAP20",
                           "MAP21", "MAP22", "MAP23", "MAP24", "MAP25", "MAP26", "MAP27", "MAP28", "MAP29", "MAP30",
                           "MAP31", "MAP32"]
        # Map selection combo box
        self.selected_map_box['values'] = self.doom2_maps
        self.selected_map_box['state'] = 'readonly'
        self.selected_map_box.pack(side='left')
        # This tracks the current drawn level
        self.map_ptr = self.doom2_maps.index("MAP01")
        # print("__init__: map pointer is :  {}".format(self.map_ptr))

        root.title("WADdle Plot - v0.9")

        """if self.game is "DOOM":
            self.map_ptr = self.doom_maps[0] + 1
        else:
            self.map_ptr = self.doom2_maps[0] + 1"""
        # self._points_toFile(all_levels="wos_levels.bin") <-- fix this function
        # ======================================
        self.map_x_max = None
        self.map_x_min = None
        self.map_y_max = None
        self.map_y_min = None
        # This could be wrong
        self.screen_x_max = -400 + 10
        self.screen_x_min = 400 - 10
        self.screen_y_max = -300 + 10
        self.screen_y_min = 300 - 10
        # =======================
        # self.world_to_screen()  <--- plot() calls this

        # Set initial value of the combo-box
        self.selected_map_box.current(newindex=self.map_ptr)
        #print('hi')
        self.screen.tracer(0)
        #self.plot()



    def openFile_dialog(self):
        """Calls the tk.filedialog to open a wadfile..."""

        filetypes = (
            ('wadfiles', '*.wad'),
            ('zipfile archive', '*.zip'),
            ('All files', '*.*')
        )

        filename = fd.askopenfilename(
            title='Open a DOOM wadfile or a zipfile that contains wadfiles',
            initialdir='/',
            filetypes=filetypes
        )

        if filename.endswith('.wad') or filename.endswith('.WAD'):
            self.loadWad(filename)
            self.loadLevel(self.doom2_maps[self.doom2_maps.index("MAP01")])
            self.map_ptr = self.doom2_maps.index(self.level.map)
            self.plot()
            # Update combo-box...
            self.selected_map_box.current(newindex=self.map_ptr)

        elif filename.endswith('.zip'):
            # setup a ttk.combobox widget for archive-file selection
            self.archive_loaded_display = tk.StringVar()
            self.archived_loaded_box = ttk.Combobox(textvariable=self.archive_loaded_display)
            self.archived_loaded_box.bind('<<ComboboxSelected>>', self.cb_change_archive_wadfile)
            # load the zipfile
            self.wad_archive = zipfile.ZipFile(filename)
            # we only want the .wad files showing up in the combobox, not .txt describing said wadfiles
            wad_archive_wadfile_names = []
            for f in self.wad_archive.namelist():
                if f.endswith('.wad'):
                    wad_archive_wadfile_names.append(f)
            # TODO: setup a text widget for viewing the txt files describing the wads
            self.archived_loaded_box["values"] = wad_archive_wadfile_names
            self.archived_loaded_box["state"] = "readonly"
            self.archived_loaded_box.pack(side='left', anchor='sw', padx=5, pady=5)
            self.archived_loaded_box.current(newindex=0)
            # close the zipfile
            self.wad_archive.close()


        else:
            print("{} is an INVALID wadfile!".format(filename))

    def cb_change_archive_wadfile(self, evt):
        print('hi from cb change archive fuck')

    def progress_begin(self):
            time.sleep(5)
            #self.progress_bar.start()

            # Checkbutton state func

    def isChecked(self):
        if self.cb.get() == 1:
            self.screen.tracer(1)
        if self.cb.get() == 0:
            self.screen.tracer(0)

    def cb_change_map(self, evt):
        """Changes to the selected level in the combo box"""
        print("cb_change_map: Switching to and plotting level {}".format(self.selected_map_box.get()))
        # showinfo(title="Map", message=msg)
        self.level = None
        self.loadLevel(self.doom2_maps[self.doom2_maps.index(self.selected_map_box.get())])
        self.map_ptr = self.doom2_maps.index(self.level.map)
        self.plot()

    def prev_map(self):
        self.level = None
        self.loadLevel(self.doom2_maps[self.map_ptr - 1])
        self.map_ptr = self.doom2_maps.index(self.level.map)
        self.plot()
        # Update the combo box to reflect the level change
        self.selected_map_box.current(newindex=self.map_ptr)

    def next_map(self):
        self.level = None

        if self.map_ptr == 31:
            self.loadLevel(self.doom2_maps[0])
            self.map_ptr = self.doom2_maps.index(self.level.map)
            self.plot()
            # Update...
            self.selected_map_box.current(newindex=self.map_ptr)
            return

        self.loadLevel(self.doom2_maps[self.map_ptr + 1])
        try:
            self.map_ptr = self.doom2_maps.index(self.level.map)
        except AttributeError as whoo:
            print(whoo)
            print(whoo.args)
        self.plot()
        # Update the combo box to reflect the change
        self.selected_map_box.current(newindex=self.map_ptr)

    def draw_map(self):
        """Draws the currently loaded level"""
        self.plot()

    def getPoints(self, points_file: str) -> list:
        """
        Load a list of points from a FILE that was written
        by  _points_toFile

        param: points_file = path to points file
         """
        # TODO: Change this function to support the output format of
        #       points_to_file UPDATE: This is done?
        # TODO: Support loading an all_levels file...

        points_file = open(points_file, 'rb')
        points = pickle.load(points_file)
        points_file.close()

        xPoints = []
        yPoints = []
        for p in points:
            xPoints.append(p[0])
            yPoints.append(p[1])

        del points

        points = []
        for x, y in zip(xPoints, yPoints):
            points.append((x, y))

        return points

    def _points_toFile(self, p_file=False, all_levels=False):
        """"
        Write points data to a FILE. This is an instance method!
        This should NOT be called apart
        from __init__, due to the assumption that the level data has already
        been assembled by: self.loadlevel()

        PARAM: points_file = Name of written file
        """

        # Write a single level
        if p_file:
            out_file = open(p_file, 'wb')

            xPoints = []
            yPoints = []
            for linedef in self.level.lines.lines:
                xPoints.append(linedef['line-segment'].start.x)
                yPoints.append(linedef['line-segment'].start.y)
                xPoints.append(linedef['line-segment'].end.x)
                yPoints.append(linedef['line-segment'].end.y)

            points = []
            for x, y in zip(xPoints, yPoints):
                points.append((x, y))

            pickle.dump(points, out_file)
            out_file.close()

        # Write all levels within the loaded wadfile
        # File size is 1/2 of wadfile. Not even worth it...
        if all_levels:
            out_file = open(all_levels, 'wb')
            m_ptr = self.map_ptr
            print("m_ptr is {}".format(m_ptr))
            loaded_level = None

            xPoints = []
            yPoints = []

            print("Writing all level-points to {}".format(all_levels))
            i= 0
            while i < len(self.doom2_maps):
                loaded_level = self.level
                print("Writing points for {} to {}".format(self.level.map, all_levels))

                for line in loaded_level.lines.lines:
                    xPoints.append(line['line-segment'].start.x)
                    yPoints.append(line['line-segment'].start.y)
                    xPoints.append(line['line-segment'].end.x)
                    xPoints.append(line['line-segment'].end.y)

                points = []
                for x, y in zip(xPoints, yPoints):
                    points.append((x, y))
                pickle.dump(points, out_file)
                i += 1

            out_file.close()

    def loadWad(self, wadfile: str):
        """
        Loads a wadfile. Sets a self.wadfile attribute in instance
        """

        _wadfile = open(wadfile, 'rb')
        self._wadfile = Wad(_wadfile)

    def loadLevel(self, level: str):
        """ Loads a level.\n
        param: ExMx (DOOM) or MAPxx(DOOM2)
        """
        try:
            self._wadfile.load_level_info(level)
            self.level = self._wadfile.build_level(level)
        except AttributeError as whoops:
            print("_loadLevel_: is of a {} type".format(self.level))
            print(whoops)

    def world_to_screen(self):
        """ Translate our line end-points to screen-space"""
        # TODO: Iterate over ...lines[x]["line-segment"] to get
        #         the max/min of the map
        x = []
        y = []
        screen_range_x = (self.screen_x_max - self.screen_x_min)
        screen_range_y = (self.screen_y_max - self.screen_y_min)
        # So I guess we need to 'unzip' the X and Y values in a single list for min() and max() to traverse?
        for p in self.level.lines.lines:
            x.append(p['line-segment'].start.x)
            x.append(p['line-segment'].end.x)
            y.append(p['line-segment'].start.y)
            y.append(p['line-segment'].end.y)

        self.map_x_max = min(x)
        self.map_x_min = max(x)
        self.map_y_max = min(y)
        self.map_y_min = max(y)

        map_range_x = (self.map_x_max - self.map_x_min)
        map_range_y = (self.map_y_max - self.map_y_min)

        # Now we need to convert the points to screen

        # NOTE: Vectors (that I'm using) are immutable so need another instance...
        for p in self.level.lines.lines:
            # Translate the X coordinate
            cx = p['line-segment'].start.x
            start_sx = (((cx - self.map_x_min) * screen_range_x) / map_range_x) + self.screen_x_min
            cx = p['line-segment'].end.x
            end_sx = (((cx - self.map_x_min) * screen_range_x) / map_range_x) + self.screen_x_min
            # Translate the Y coordinate
            cy = p['line-segment'].start.y
            start_sy = (((cy - self.map_y_min) * screen_range_y) / map_range_y) + self.screen_y_min
            cy = p['line-segment'].end.y
            end_sy = (((cy - self.map_y_min) * screen_range_y) / map_range_y) + self.screen_y_min
            # Now we need to replace the current line-segment with a new instance...
            # We also need -start_sy and -end_sy to FLIP the map right-side UP!
            start = start_sx, start_sy
            end = end_sx, end_sy
            p['line-segment'] = planar.LineSegment.from_points((start, end))

    def plot(self):
        """ Plot the level"""
        self.t_turtle.reset()
        self.t_turtle.speed(0)
        # Start the progress bar
        #self.progress_bar.set_value(30)
        #self.screen.bgcolor(self.BACKGROUND_COLOR)
        #self.screen.delay(1)

        # 2nd turtle for concurrent plotting?
        self.t_turtle2.circle(100)

        # Level stats
        if self.vnum:
            self.vnum.destroy()
            self.vnum = ttk.Label(text="Lines: {}".format(len(self.level.lines.lines)))
            self.vnum.pack(side="right", padx=5)
        if not self.vnum:
            self.vnum = ttk.Label(text="Lines: {}".format(len(self.level.lines.lines)))
            self.vnum.pack(side="right", padx=5)

        # Check for animate check button - Fix me
        if self.cb == 1:
            self.screen.tracer(1)
        if self.cb == 0:
            self.screen.tracer(0)
        self.world_to_screen()
        #self.screen.tracer(0)

        # Determines if we are plotting in a highly-detailed area of the level
        x_point_history = list()

        def zoom_in():
            #ZOOM!
            self.screen.tracer(0)
            self.screen.delay(0)
            self.t_turtle.hideturtle()
            #gotta zoom back out too....
            pass

        lines_drawn = 0
        doZOOM = False

        root.title("Plotting {}...".format(self.level.map))
        for p in self.level.lines.lines:
            # If we're plotting in a highly detailed, small area,
            # then let's zoom in so we can get a closer look.
            if -1 in p.values():
                self.t_turtle.pencolor(self.ONE_SIDED_COLOR)
            else:
                self.t_turtle.pencolor(self.TWO_SIDED_COLOR)
            self.t_turtle.penup()
            self.t_turtle.goto(p['line-segment'].start)
            self.t_turtle.pendown()
            self.t_turtle.goto(p['line-segment'].end)
            lines_drawn += 1

            # Line label shown in GUI that we are drawing on...
            if self.onLine:
                self.onLine.destroy()
                self.onLine = ttk.Label(text="Drawing Line: {} ".format(self.level.lines.lines.index(p)+1))
                self.onLine.configure(background="green", foreground="black", relief="solid")
                self.onLine.pack(side="right", padx=5)
            if not self.onLine:
                self.onLine = ttk.Label(text="Drawing Line: {} ".format(self.level.lines.lines.index(p)+1))
                self.onLine.configure(background="green", foreground="black", relief="solid")
                self.onLine.pack(side="right", padx=5)
            # Needed for updates when click the next buttons. Removes overlap bug but adds a new one....
            # TODO: Add a checkbutton to turn 'updates' on or off...
            self.screen.update()
            if lines_drawn > 4:
                x_point_history.append(p['line-segment'].start.x)
                # Let's see if we are in a highly-detailed area of the level...
                if not isclose(x_point_history[-1], p['line-segment'].start.x, rel_tol=0.05):
                    if doZOOM:
                        zoom_in()
        self.onLine.destroy()
        self.onLine = ttk.Label(text="Finished plotting {}".format(self.level.map))
        self.onLine.configure(background="red", foreground="black", relief="groove")
        self.onLine.pack(side="right", padx=5)
        #Set title of main window
        root.title("{} from:  {}        [WADdle Plot - v0.9]".format(self.level.map, self._wadfile.wadfile.name))



if __name__ == "__main__":
    root = tk.Tk()
    plotter = MapViewer(root)
    plotter.pack(side="top", fill="both", expand=True)
    #root.resizable(width=False, height=False)

    # Menu won't show up?!
    #menubar = Menu(plotter)
    #filemenu = Menu(root, tearoff=0)
    #filemenu.add_command(label="Open")
    root.config(menu=plotter.menubar)

    root.mainloop()

