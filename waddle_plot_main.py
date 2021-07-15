import pickle
import tkinter as tk
# from tkinter import ttk
import tkinter.colorchooser
import tkinter.ttk as ttk
import turtle
from tkinter.constants import *
import time
import threading
from tkinter import Checkbutton
from tkinter import IntVar
from tkinter import Menu
from tkinter import filedialog as fd
#from tkinter.colorchooser import askcolor

import planar
from planar import Vec2
from waddle_plot import Wad, LineDefs, SideDefs, Vertexes, Level
from pickle import dump, load

from math import isclose
import zipfile


# TODO: Initialize all attributes in __init__ for maintenance sanity and keeping PyCharm happy!                7/13/2021
# ----------------------------------------------------------------------------------------------------------------------
# TODO: Add program quit option to file menu and close the wadfile if it or 'X' is clicked                     7/13/2021
# ----------------------------------------------------------------------------------------------------------------------
# TODO: Add loading/plotting wadfiles from zipfiles and disabled widgets accordingly                           7/13/2021
# ----------------------------------------------------------------------------------------------------------------------
# TODO: Add Menu>View>Options for changing levels while plotting. Just have the gui option                     7/13/2021
#       enable the associated widgets for level switching
# ----------------------------------------------------------------------------------------------------------------------
# TODO: Add color changing of background, foreground and lines                                                 7/13/2021
# ----------------------------------------------------------------------------------------------------------------------
# TODO: Correctly set the Canvas size to match the aspect-ratio of the level. Computed from the map.           7/13/2021
#       Some levels are "squashed" or stretched in either the X or Y dimension.
# ----------------------------------------------------------------------------------------------------------------------

class MapViewer(tk.Frame):
    def __init__(self):
        tk.Frame.__init__(self)
        self.pack(expand=YES, fill=BOTH)
        self.menubar = Menu(self.master)
        self.master.config(menu=self.menubar)
        file = Menu(self.menubar, tearoff=0)
        file.add_command(label="Open a wadfile/zip archive of wadfiles...", command=self.openFile_dialog)
        self.menubar.add_cascade(label="File", menu=file)
        # add a "Edit" menu option
        edit = Menu(self.menubar, tearoff=0)
        #edit.add_command(label="auto-plot", command=self.autoplot)
        #self.menubar.add_cascade(label="Edit", menu=edit)

        def noupdates(self):
            pass

        # Canvas
        self.canvas = tk.Canvas(width=1280, height=960)
        self.canvas.pack(side="bottom")
        #self.canvas.configure(scrollregion=(-640, -800, 640, 800))

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
        self.screen = self.t_turtle.getscreen()
        self.ONE_SIDED_COLOR = "#00a6a6"
        self.TWO_SIDED_COLOR = "#933000"
        self.BACKGROUND_COLOR = "BLACK"
        self.screen.bgcolor(self.BACKGROUND_COLOR)

        # wadfile level navigation buttons (previous, next)
        self.prevmap_btn = tk.Button(self, text="Prev MAP", command=self.prev_map)
        self.prevmap_btn.configure(background="white", foreground="grey", relief="solid", state="disabled")
        self.prevmap_btn.pack(side="left", padx=5, pady=5)
        self.nextmap_btn = tk.Button(self, text="Next MAP", command=self.next_map)
        self.nextmap_btn.configure(background="white", foreground="grey", relief="solid", state="disabled")
        self.nextmap_btn.pack(side="left", padx=5, pady=5)
        # Map Select Box Widget
        map_select_label = ttk.Label(text="MAP:")
        map_select_label.pack(side="left")

        self.selected_map_var = tk.StringVar()
        self.selected_map_box = ttk.Combobox(textvariable=self.selected_map_var)
        self.selected_map_box.configure(state="disabled")
        self.selected_map_box.bind('<<ComboboxSelected>>', self.cb_change_map)
        # var for Checkbutton state
        self.cb = IntVar()
        # Animate Checkbutton
        self.anim_check_btn = Checkbutton(self, text="Live-Plot(slow)", variable=self.cb, onvalue=1,
                                          offvalue=0, command=self.isChecked)
        self.anim_check_btn.configure(state="disabled")
        self.anim_check_btn.pack(side="left", padx=5, pady=5)

        # Progress Bar (on draw) - can't get working
        # self.progress_bar = ttk.Progressbar(orient=tk.HORIZONTAL, mode='determinate')
        # self.progress_bar.pack(side="right", padx=5, pady=5)
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
        #self.selected_map_box['state'] = 'readonly'
        self.selected_map_box.pack(side='left')
        # This tracks the current drawn level
        self.map_ptr = self.doom2_maps.index("MAP01")
        # print("__init__: map pointer is :  {}".format(self.map_ptr))

        self.master.title("WADdle Plot - v0.9")
        self.master.resizable(width=False, height=False)


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
        self.screen_x_max = -640 + 10
        self.screen_x_min = 640 - 10
        self.screen_y_max = -480 + 10
        self.screen_y_min = 480 - 10
        # Set initial value of the combo-box
        self.selected_map_box.current(newindex=self.map_ptr)
        self.screen.tracer(0)

        # color choosing buttons for setting line colors
        self.solidline_color_btn = tk.Button(self, text="1-Sided line color",
                                   command=self.setSolid_linecolor)
        self.solidline_color_btn.pack(side="left")
        self.solidline_color_btn.configure(background=self.ONE_SIDED_COLOR)

        self.transline_color_btn = tk.Button(self, text="2-Sided line color",
                                             command=self.setTrans_linecolor)
        self.transline_color_btn.configure(background=self.TWO_SIDED_COLOR)
        self.transline_color_btn.pack(side="left")
        # redraw level button
        self.redraw_btn = ttk.Button(self, text="redraw", command=self.plot)
        self.redraw_btn.configure(state='disabled')
        self.redraw_btn.pack(side="left")
        # autplot check button
        self.autoplot_cb = IntVar()
        self.autoplot_btn = ttk.Checkbutton(self, text="autoplot", variable=self.autoplot_cb,
                                            onvalue=1, offvalue=0, state=NORMAL,
                                            command=self.autoplot)
        self.autoplot_btn.configure(state='disabled')
        self.autoplot_btn.pack(side='left', anchor='sw', padx=5, pady=5)

    def autoplot(self):
        """ called by autoplot """
        self.plotall = 1
        if self.autoplot_cb.get() == 1:
            while self.level and self.plotall:
                self.next_map()
        if self.autoplot_cb.get() == 0:
            print("implement plot stop!")

    def setTrans_linecolor(self):
        """ Called when '2-Sided...' is clicked """
        color = tkinter.colorchooser.askcolor(title="Set 2-Sided LINE color", initialcolor=self.TWO_SIDED_COLOR)
        print(color[1])
        if color[1]:
            self.TWO_SIDED_COLOR = color[1]
            #update button color to reflect change
            self.transline_color_btn.configure(background=self.TWO_SIDED_COLOR)
            print("solid color set to {}".format(color[1]))

    def setSolid_linecolor(self):
        """ Called when '1-Sided..' is clicked """
        color = tkinter.colorchooser.askcolor(title="Set 1-Sided LINE color", initialcolor=self.ONE_SIDED_COLOR)
        print(color[1])
        if color[1]:
            self.ONE_SIDED_COLOR = color[1]
            self.solidline_color_btn.configure(background=self.ONE_SIDED_COLOR)
            print("solid color set to {}".format(color[1]))


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
            # close the wadfile so we're not leaking memory
            if self._wadfile:
                self._wadfile.wadfile.close()

            self.loadWad(filename)
            self.loadLevel(self.doom2_maps[self.doom2_maps.index("MAP01")])
            self.map_ptr = self.doom2_maps.index(self.level.map)

            # activate 'animate' checkbutton
            self.anim_check_btn.configure(state="active")
            # Update combo-box...
            self.selected_map_box.current(newindex=self.map_ptr)

            self.plot()

            # 'enable' level navigation buttons
            self.prevmap_btn.configure(foreground="black", relief="raised",
                                       overrelief="solid", state="active")
            self.nextmap_btn.configure(foreground="black", relief="raised",
                                       overrelief="solid", state="active")
            # enable the level-list selection box
            self.selected_map_box.configure(state="readonly")
            # enable redraw gui button
            self.redraw_btn.configure(state="active")
            # enable autoplot check btn
            self.autoplot_btn.configure(state='active')

        elif filename.endswith('.zip'):
            # close the wadfile so we're not leaking memory
            if self._wadfile:
                self._wadfile.wadfile.close()

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
            if not filename:
                return
            print("{} is an INVALID wadfile!".format(filename))

    def cb_change_archive_wadfile(self, evt):
        print('hi from cb change archive fuck')

    def progress_begin(self):
            time.sleep(5)
            #self.progress_bar.start()

            # Checkbutton state func

    def isChecked(self):
        """ Called by the 'animate' checkbutton, on click"""
        if self.cb.get() == 1:
            self.screen.tracer(1)
        if self.cb.get() == 0:
            self.screen.tracer(0)

    def cb_change_map(self, evt):
        """Changes to the selected level in the combo box"""
        if self.level:
            self.level = None
            self.loadLevel(self.doom2_maps[self.doom2_maps.index(self.selected_map_box.get())])
            self.map_ptr = self.doom2_maps.index(self.level.map)
            self.plot()
            return
        # Code below is not needed because the level-selection box is set to "disabled" on creation
        """if not self.level and not self._wadfile:
            # TODO: raise a popup dialogbox with the following before removing print statement! - 7/13/2021
            print('Load a wadfile/archive first!')
            return"""
        self.loadLevel(self.doom2_maps[self.doom2_maps.index(self.selected_map_box.get())])
        self.map_ptr = self.doom2_maps.index(self.level.map)
        self.plot()

    def prev_map(self):
        """ Called when 'prev map' tk.Button is clicked """
        self.level = None

        # is a wadfile loaded
        if self._wadfile:
            self.loadLevel(self.doom2_maps[self.map_ptr - 1])
            self.map_ptr = self.doom2_maps.index(self.level.map)
            self.plot()
            # Update the combo box to reflect the level change
            self.selected_map_box.current(newindex=self.map_ptr)

    def next_map(self):
        """ Called when the 'next map' tk.Button is clicked """

        self.level = None

        # is a wadfile loaded?
        if self._wadfile:
            # support going from the last map to the first map with a NEXT click...
            if self.map_ptr == 31:
                self.loadLevel(self.doom2_maps[0])
                self.map_ptr = self.doom2_maps.index(self.level.map)
                self.plot()
                # Update...
                self.selected_map_box.current(newindex=self.map_ptr)
                return

            self.loadLevel(self.doom2_maps[self.map_ptr + 1])
            self.map_ptr = self.doom2_maps.index(self.level.map)
            self.plot()
            # Update the combo box to reflect the change
            self.selected_map_box.current(newindex=self.map_ptr)
            return

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
        """
        Write points data to a FILE. This is an instance method!
        This should NOT be called apart
        from __init__, due to the assumption that the level data has already
        been assembled by: self.loadlevel()

        PARAM: points_file = Name of written file
        """

        # TODO: Define a file format for storing points data. Put multiple points on a single line to
        #       conserve file space!

        # TODO: Add a menu option for loading and saving points data.

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
            i = 0
            while i < len(self.doom2_maps):
                # TODO: We're not loading a new level so this is writing the SAME (level x len(self.doom2_maps)
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

        self.master.title("Plotting {}...".format(self.level.map))

        # disable level nav buttons while plotting so we don't corrupt tkinter internal state...
        self.prevmap_btn.configure(state="disabled")
        self.nextmap_btn.configure(state="disabled")
        # disable level-selection box
        self.selected_map_box.configure(state="disabled")

        # Clicking this button during a map plot is BAD...
        self.redraw_btn.configure(state="disabled")

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
        # plot complete, re-enabled level nav buttons
        self.prevmap_btn.configure(state="active")
        self.nextmap_btn.configure(state="active")
        # re-enable level-selection box
        self.selected_map_box.configure(state="readonly")
        # re-enable redraw
        self.redraw_btn.configure(state='active')

        self.onLine.destroy()
        self.onLine = ttk.Label(text="Finished plotting {}".format(self.level.map))
        self.onLine.configure(background="red", foreground="black", relief="groove")
        self.onLine.pack(side="right", padx=5)
        #Set title of main window
        self.master.title("{} from:  {}        [WADdle Plot - v0.9]".format(self.level.map, self._wadfile.wadfile.name))

        # Check if we should stop autoplotting
        if self.autoplot_cb.get() == 0:
            self.plotall = 0

if __name__ == "__main__":
    # root = tk.Tk() update

    # plotter = MapViewer(root) update
    # plotter.pack(side="top", fill="both", expand=True)update
    #root.resizable(width=False, height=False)

    # Menu won't show up?!
    #menubar = Menu(plotter)
    #filemenu = Menu(root, tearoff=0)
    #filemenu.add_command(label="Open")

    # root.config(menu=plotter.menubar) update

    # root.mainloop() update
    # close opened wadfile(s)

    MapViewer().mainloop()

    if MapViewer()._wadfile:
        MapViewer()._wadfile.close()

    """if plotter._wadfile:
        print("{} is: {}".format(plotter._wadfile.wadfile, "open"))
        w_file = plotter._wadfile.wadfile.name
        plotter._wadfile.wadfile.close()
        print("Closed {}".format(w_file))"""
