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

import planar
from planar import Vec2
from waddle_plot import Wad, LineDefs, SideDefs, Vertexes, Level
from pickle import dump, load




class MapViewer(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        # Canvas
        self.canvas = tk.Canvas(master=root, width=1285, height=725)
        self.canvas.pack(side="top", fill="both", expand=True)
        # self.canvas.configure(scrollregion=(-640, -360, 640, 360))
        # turtle opts
        self.t_turtle = turtle.RawTurtle(self.canvas)
        self.screen = self.t_turtle.getscreen()
        self.ONE_SIDED_COLOR = "GREEN"
        self.TWO_SIDED_COLOR = "RED"
        self.BACKGROUND_COLOR = "BLACK"
        self.screen.bgcolor(self.BACKGROUND_COLOR)
        # buttons
        nextmap_btn = tk.Button(self, text="Next MAP", command=self.next_map)
        nextmap_btn.pack(side="left", padx=5, pady=5)
        prevmap_btn = tk.Button(self, text="Prev MAP", command=self.prev_map)
        prevmap_btn.pack(side="left", padx=5, pady=5)

        #self.anim_check_btn = Checkbutton(self, text="Animate", variable=self.isChecked, onvalue=1, offvalue=0)
        #self.anim_check_btn = Checkbutton(self, text="Animate")
        #self.anim_check_btn.pack(side="left", padx=5, pady=5)



        # Map Select Box Widget
        map_select_label = ttk.Label(text="MAP:")
        map_select_label.pack(side="left", padx=5, pady=5)

        self.selected_map_var = tk.StringVar()
        self.selected_map_box = ttk.Combobox(textvariable=self.selected_map_var)
        self.selected_map_box.bind('<<ComboboxSelected>>', self.cb_change_map)

        # Progress Bar (on draw) - can't get working
        self.progress_bar = ttk.Progressbar(orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(side="right", padx=5, pady=5)
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
        self.loadWad("C:\Pydevel\WOS.wad")    # |
        self.loadLevel("MAP01")      # |
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
        self.selected_map_box.pack(side='left', padx=5, pady=5)
        # This tracks the current drawn level
        # BUG: list index out of range when going past the end...
        self.map_ptr = self.doom2_maps.index(self.level.map)
        # print("__init__: map pointer is :  {}".format(self.map_ptr))

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
        self.screen_y_max = -360 + 10
        self.screen_y_min = 360 - 10
        # =======================
        # self.world_to_screen()  <--- plot() calls this
        self.plot()
        # Set initial value of the combo-box
        self.selected_map_box.current(newindex=self.map_ptr)
        #print('hi')

    def progress_begin(self):
            time.sleep(5)
            self.progress_bar.start()

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
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        print("\nprev_map: Current map is: {}".format(self.level.map))
        print("prev_map: Map pointer is @ {}".format(self.map_ptr))
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")

    def next_map(self):
        self.level = None

        if self.map_ptr is 31:
            self.loadLevel(self.doom2_maps[0])
            self.map_ptr = self.doom2_maps.index(self.level.map)
            self.plot()
            # Update...
            self.selected_map_box.current(newindex=self.map_ptr)
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print("\nnext_map: Current map is: {}".format(self.level.map))
            print("next_map: Map Pointer is @ {}".format(self.map_ptr))
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            return

        self.loadLevel(self.doom2_maps[self.map_ptr + 1])
        self.map_ptr = self.doom2_maps.index(self.level.map)
        self.plot()
        # Update the combo box to reflect the change
        self.selected_map_box.current(newindex=self.map_ptr)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("\nnext_map: Current map is: {}".format(self.level.map))
        print("next_map: Map pointer is @ {}".format(self.map_ptr))
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

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
        Write points data to a FILE. This should NOT be called apart
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
        if self.level is not None:
            print("CAUTION: Loaded level has CHANGED!")

        self._wadfile.load_level_info(level)
        self.level = self._wadfile.build_level(level)

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
            start = start_sx, -start_sy
            end = end_sx, -end_sy
            p['line-segment'] = planar.LineSegment.from_points((start, end))

    def plot(self):
        """ Plot the level"""
        self.t_turtle.reset()
        # Start the progress bar
        #self.progress_bar.set_value(30)
        #self.screen.bgcolor(self.BACKGROUND_COLOR)
        #self.screen.delay(1)

        # Check for animate check button - Fix me
        """if self.is() == 1:
            self.screen.tracer(1)
        else:
            self.screen.tracer(0)"""
        self.world_to_screen()
        self.screen.tracer(0)

        for p in self.level.lines.lines:
            if -1 in p.values():
                self.t_turtle.pencolor(self.ONE_SIDED_COLOR)
            else:
                self.t_turtle.pencolor(self.TWO_SIDED_COLOR)
            self.t_turtle.penup()
            self.t_turtle.goto(p['line-segment'].start)
            self.t_turtle.pendown()
            self.t_turtle.goto(p['line-segment'].end)
            # self.progress_bar.stop()


if __name__ == "__main__":
    root = tk.Tk()
    # MapViewer(root).pack(side="top", fill="both", expand=True)
    MapViewer().pack(side="top", fill="both", expand=True)
    root.resizable(width=False, height=False)
    root.mainloop()
    # MapViewer().mainloop()
