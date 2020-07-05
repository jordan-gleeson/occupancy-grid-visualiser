import time
import operator
import random
import numpy as np
import pygame
import pygame_gui as pygui
import utils
import copy


class Game():
    """Main game class.

    Creates the game screen. Contains the main game loop which handles the order of execution of
    robot and SLAM functionality.
    """

    def __init__(self):
        # pygame setup
        pygame.init()
        pygame.key.set_repeat(300, 30)
        self.screen = pygame.display.set_mode((1280, 720), pygame.SRCALPHA)
        self.screen.fill((255, 255, 255))
        self.clock = pygame.time.Clock()

        # Create a white background
        self.background = pygame.Surface(self.screen.get_size(),
                                         pygame.SRCALPHA)
        self.background = self.background.convert()
        self.background.fill((255, 255, 255))
        self.menu_background = copy.copy(self.background)
        self.menu_background.fill((57, 65, 101))

        pygame.display.flip()

        # Setup classes
        self.world = World(self.screen)
        self.robot = RobotControl(self.screen, self.world)
        self.robot.update()
        self.slam = SLAM(self.screen, self.robot)
        self.gui = GUI(self.screen, self.world, self.robot, self.slam)

        self.font = pygame.font.Font(None, 30)

        self.state = 0
        self.main()

    def main(self):
        """Main game loop."""
        _playing_game = True
        _world_edited = False
        while _playing_game:
            _time_delta = self.clock.tick(30) / 1000.0
            self.screen.blit(self.background, (0, 0))
            for _event in pygame.event.get():
                if _event.type == pygame.QUIT:
                    _playing_game = False
                    break
                if _event.type == pygame.USEREVENT:
                    self.gui.input(_event)
                if _event.type == pygame.MOUSEBUTTONUP:
                    self.gui.last_mouse_pos = None
                if _event.type == pygame.KEYDOWN:
                    if _event.key == pygame.K_r:
                        self.gui.reset()
                self.gui.manager.process_events(_event)

            # Main Menu
            if self.state == 0:
                if self.gui.main_menu_state == 0:
                    self.state += 1
                    self.gui.play_game(_world_edited)
                elif self.gui.main_menu_state == 2:
                    self.state = 2
                    _world_edited = True
                    self.gui.kill_main_menu()
                    self.gui.world_editor_setup()

            # Simulation
            elif self.state == 1:
                self.robot.change_velocity(pygame.key.get_pressed())
                self.world.draw()
                self.slam.update()
                self.robot.update()
                self.slam.odometry(self.robot.odo_velocity)
                if self.robot.robot.new_sample:
                    self.slam.occupancy_grid()
                    self.robot.robot.new_sample = False

            # World Editor
            elif self.state == 2:
                if self.gui.main_menu_state == 1:
                    self.state = 0
                    self.gui.main_menu()
                    self.gui.kill_world_editor()
                self.gui.world_editor(pygame.mouse.get_pressed()[0],
                                      pygame.mouse.get_pos())

            _fps = self.font.render(str(int(self.clock.get_fps())),
                                    True,
                                    pygame.Color('green'))
            self.screen.blit(_fps, (3, 3))
            self.gui.update(_time_delta)
            pygame.display.update()

        pygame.quit()


class GUI():
    """Contains all aspects of the GUI.

    Handles setup of GUI elements and the handling of input events.

    Attributes:
        _p_screen: The main pygame screen surface.
        _p_world: The world map object.
        _p_robot: The robot object.
        _p_slam: The slam algorithm object.
    """

    def __init__(self, _p_screen, _p_world, _p_robot, _p_slam):
        self.screen = _p_screen
        self.world = _p_world
        self.robot = _p_robot
        self.slam = _p_slam
        self.manager = pygui.UIManager(self.screen.get_size(), 'theme.json')
        self.manager.set_visual_debug_mode(False)

        self.settings_window = None

        # Main Menu Setup
        self.main_menu_state = True
        # self.main_menu_pnl = None
        # self.start_btn = None
        # self.world_edit_btn = None
        # self.slam_type_drp = None
        # self.lidar_chk = None
        # self.grid_chk = None
        # self.pos_chk = None
        # self.title = None
        # self.title_pnl = None
        # self.setup_pnl = None
        # self.setup_lbl_pnl = None
        # self.setup_ttl = None
        # self.preview_pnl = None
        # self.instructions_pnl = None
        # self.preview_ttl = None
        # self.preview_lbl_pnl = None
        # self.instructions_lbl_pnl = None
        # self.instructions_ttl = None
        self.main_menu()

        # Settings Button Setup
        self.toggle_lidar_btn = None
        self.toggle_occupancy_grid_btn = None
        self.toggle_positions_btn = None
        self.done_btn = None
        self.settings_button = None
        self.reset_btn = None

        # Position Visualisation Setup
        self.draw_positions = True

        # World Editor Setup
        self.last_mouse_pos = None
        self.we_done_btn = None
        self.we_clear_btn = None
        self.we_mode_btn = None
        self.we_draw_mode = True

    def main_menu(self):
        """Setup the main menu."""
        _button_width = 110
        _button_height = 40
        _vert_out_padding = 60
        _hor_out_padding = 60
        _vert_in_padding = 30
        _hor_in_padding = 30
        _vert_inner_padding = 20
        _hor_inner_padding = 20
        _start_button_height = 80

        _main_menu_pnl_rect = pygame.Rect((0, 0),
                                          (self.screen.get_width(), self.screen.get_height()))
        self.main_menu_pnl = pygui.elements.UIPanel(_main_menu_pnl_rect, 0,
                                                    self.manager,
                                                    object_id="background_panel")

        _title_panel_pos = (_hor_out_padding, _vert_out_padding)
        _title_panel_size = (self.screen.get_width() -
                             _hor_out_padding * 2, 100)
        _title_panel_rect = pygame.Rect(_title_panel_pos, _title_panel_size)
        self.title_pnl = pygui.elements.UIPanel(_title_panel_rect, 0,
                                                manager=self.manager,
                                                object_id="title_panel")

        _title_size = (354, 45)
        _title_pos = (_title_panel_pos[0] + _hor_inner_padding,
                      _title_panel_pos[1] + _title_panel_size[1] / 2 - _title_size[1] / 2 + 5)
        _title_rect = pygame.Rect(_title_pos, _title_size)
        self.title = pygui.elements.UILabel(_title_rect,
                                            "SLAM Visualiser",
                                            self.manager,
                                            object_id="title_label")

        _setup_panel_pos = (_hor_out_padding,
                            _title_panel_pos[1] + _title_panel_size[1] + _vert_in_padding)
        _setup_panel_size = ((self.screen.get_width() - _hor_out_padding * 2) / 3 - _hor_in_padding / 2,
                             self.screen.get_height() - _hor_out_padding * 2 - _hor_in_padding * 2 - _title_panel_size[1] - _start_button_height)
        _setup_panel_rect = pygame.Rect(_setup_panel_pos, _setup_panel_size)
        self.setup_pnl = pygui.elements.UIPanel(_setup_panel_rect, 0,
                                                manager=self.manager,
                                                object_id="menu_panel")

        _setup_label_panel_pos = (_setup_panel_pos[0] + _hor_inner_padding,
                                  _setup_panel_pos[1] + _vert_inner_padding)
        _setup_label_panel_size = (_setup_panel_size[0] - _hor_inner_padding * 2,
                                   70)
        _setup_label_panel_rect = pygame.Rect(_setup_label_panel_pos,
                                              _setup_label_panel_size)
        self.setup_lbl_pnl = pygui.elements.UIPanel(_setup_label_panel_rect, 0,
                                                    manager=self.manager,
                                                    object_id="title_panel")

        _setup_title_size = (98, 35)
        _setup_title_pos = (_setup_label_panel_pos[0] + _hor_inner_padding,
                            _setup_label_panel_pos[1] + _setup_label_panel_size[1] / 2 - _setup_title_size[1] / 2 + 3)
        _setup_title_rect = pygame.Rect(_setup_title_pos, _setup_title_size)
        self.setup_ttl = pygui.elements.UILabel(_setup_title_rect,
                                                "Setup",
                                                self.manager,
                                                object_id="panel_title_label")

        _world_edit_size = (_button_width, _button_height)
        _world_edit_pos = (_setup_label_panel_pos[0], _setup_label_panel_pos[1] + _setup_label_panel_size[1] + _vert_inner_padding)
        _world_edit_rect = pygame.Rect(_world_edit_pos, _world_edit_size)
        self.world_edit_btn = pygui.elements.UIButton(relative_rect=_world_edit_rect,
                                                      text="Edit World",
                                                      manager=self.manager,
                                                      object_id="setup_button")

        _start_button_pos = (_hor_out_padding,
                             _setup_panel_pos[1] + _setup_panel_size[1] + _vert_in_padding)
        _start_button_size = (_setup_panel_size[0], _start_button_height)
        _start_button_rect = pygame.Rect(_start_button_pos, _start_button_size)
        self.start_btn = pygui.elements.UIButton(relative_rect=_start_button_rect,
                                                 text="Start",
                                                 manager=self.manager,
                                                 object_id="start_button")

        _preview_panel_pos = (_setup_panel_pos[0] + _setup_panel_size[0] + _hor_in_padding,
                              _setup_panel_pos[1])
        _preview_panel_size = (_setup_panel_size[0] * 2 + _hor_in_padding / 2,
                               (_start_button_pos[1] + _start_button_height - _setup_panel_pos[1]) / 2 - _hor_in_padding / 2)
        _preview_panel_rect = pygame.Rect(_preview_panel_pos, _preview_panel_size)
        self.preview_pnl = pygui.elements.UIPanel(_preview_panel_rect, 0,
                                                  manager=self.manager,
                                                  object_id="menu_panel")

        _instructions_panel_pos = (_preview_panel_pos[0], 
                                   _preview_panel_pos[1] + _preview_panel_size[1] + _hor_in_padding)
        _instructions_panel_size = _preview_panel_size
        _instructions_panel_rect = pygame.Rect(_instructions_panel_pos, _instructions_panel_size)
        self.instructions_pnl = pygui.elements.UIPanel(_instructions_panel_rect, 0,
                                                       manager=self.manager,
                                                       object_id="menu_panel")

        _preview_label_panel_pos = (_preview_panel_pos[0] + _hor_inner_padding,
                                  _preview_panel_pos[1] + _vert_inner_padding)
        _preview_label_panel_size = (_preview_panel_size[0] - _hor_inner_padding * 2,
                                   50)
        _preview_label_panel_rect = pygame.Rect(_preview_label_panel_pos,
                                              _preview_label_panel_size)
        self.preview_lbl_pnl = pygui.elements.UIPanel(_preview_label_panel_rect, 0,
                                                    manager=self.manager,
                                                    object_id="title_panel")

        _preview_title_size = (138, 35)
        _preview_title_pos = (_preview_label_panel_pos[0] + _hor_inner_padding,
                            _preview_label_panel_pos[1] + _preview_label_panel_size[1] / 2 - _preview_title_size[1] / 2 + 3)
        _preview_title_rect = pygame.Rect(_preview_title_pos, _preview_title_size)
        self.preview_ttl = pygui.elements.UILabel(_preview_title_rect,
                                                "Preview",
                                                self.manager,
                                                object_id="panel_title_label")

        _instructions_label_panel_pos = (_instructions_panel_pos[0] + _hor_inner_padding,
                                  _instructions_panel_pos[1] + _vert_inner_padding)
        _instructions_label_panel_size = (_instructions_panel_size[0] - _hor_inner_padding * 2,
                                   50)
        _instructions_label_panel_rect = pygame.Rect(_instructions_label_panel_pos,
                                              _instructions_label_panel_size)
        self.instructions_lbl_pnl = pygui.elements.UIPanel(_instructions_label_panel_rect, 0,
                                                    manager=self.manager,
                                                    object_id="title_panel")

        _instructions_title_size = (202, 35)
        _instructions_title_pos = (_instructions_label_panel_pos[0] + _hor_inner_padding,
                            _instructions_label_panel_pos[1] + _instructions_label_panel_size[1] / 2 - _instructions_title_size[1] / 2 + 3)
        _instructions_title_rect = pygame.Rect(_instructions_title_pos, _instructions_title_size)
        self.instructions_ttl = pygui.elements.UILabel(_instructions_title_rect,
                                                "Instructions",
                                                self.manager,
                                                object_id="panel_title_label")


    def play_game(self, _world_edited):
        """Add game buttons. Write the world map to sprites."""
        _settings_rect = pygame.Rect(
            (self.screen.get_size()[0] - 100, 20), (80, 30))
        self.settings_button = pygui.elements.UIButton(relative_rect=_settings_rect,
                                                       text="Settings",
                                                       manager=self.manager,
                                                       container=self.settings_window)

        self.kill_main_menu()

        if not _world_edited:
            self.world.write_map()
        self.world.create_sprites()

    def kill_main_menu(self):
        """Removes main menu buttons."""
        try:
            self.main_menu_pnl.kill()
            self.world_edit_btn.kill()
            self.start_btn.kill()
            self.title.kill()
            self.title_pnl.kill()
            self.setup_pnl.kill()
            self.setup_lbl_pnl.kill()
            self.setup_ttl.kill()
            self.preview_pnl.kill()
            self.instructions_pnl.kill()
            self.preview_ttl.kill()
            self.preview_lbl_pnl.kill()
            self.instructions_lbl_pnl.kill()
            self.instructions_ttl.kill()
        except:
            pass

    def kill_world_editor(self):
        """Removes world editor buttons."""
        try:
            self.we_done_btn.kill()
            self.we_clear_btn.kill()
            self.we_mode_btn.kill()
        except:
            pass

    def update(self, _time_delta):
        """Draws the GUI."""
        self.position_draw()
        self.manager.update(_time_delta)
        self.manager.draw_ui(self.screen)

    def input(self, _event):
        """Handles pygame_gui input events."""
        if _event.user_type == pygui.UI_BUTTON_PRESSED:
            if _event.ui_element == self.toggle_lidar_btn:
                self.robot.robot.toggle_lidar()
            if _event.ui_element == self.toggle_occupancy_grid_btn:
                self.slam.toggle_occupancy_grid()
            if _event.ui_element == self.settings_button:
                self.settings()
            if _event.ui_element == self.toggle_positions_btn:
                self.toggle_positions()
            if _event.ui_element == self.done_btn:
                self.settings_window.kill()
            if _event.ui_element == self.start_btn:
                self.main_menu_state = 0
            if _event.ui_element == self.world_edit_btn:
                self.main_menu_state = 2
            if _event.ui_element == self.we_done_btn:
                self.main_menu_state = 1
            if _event.ui_element == self.we_clear_btn:
                self.world.clear_map()
            if _event.ui_element == self.we_mode_btn:
                self.world_editor_mode_button()
            if _event.ui_element == self.reset_btn:
                self.reset()

    def settings(self):
        """Settings window setup."""
        _button_width = 110
        _button_height = 40
        _vert_padding = 15
        _hor_padding = 20
        _window_width = _button_width + (_hor_padding * 4)
        _window_height = (_button_height * 3) + (_vert_padding * 4)

        # TODO: Fix window sizing to use above calculations
        _settings_window_rect = pygame.Rect(((self.screen.get_size()[0] / 2) - (180 / 2),
                                             self.screen.get_size()[1] / 4 - 300 / 2),
                                            (180, 350))
        self.settings_window = pygui.elements.UIWindow(rect=_settings_window_rect,
                                                       manager=self.manager)

        # Button Setup
        _lidar_rect = pygame.Rect((_hor_padding, _vert_padding),
                                  (_button_width, _button_height))
        self.toggle_lidar_btn = pygui.elements.UIButton(relative_rect=_lidar_rect,
                                                        text="Toggle Lidar",
                                                        manager=self.manager,
                                                        container=self.settings_window)
        _occupancy_rect = pygame.Rect((_hor_padding, _vert_padding * 2 + _button_height),
                                      (_button_width, _button_height))
        self.toggle_occupancy_grid_btn = pygui.elements.UIButton(relative_rect=_occupancy_rect,
                                                                 text="Toggle Grid",
                                                                 manager=self.manager,
                                                                 container=self.settings_window)
        _positions_rect = pygame.Rect((_hor_padding, _vert_padding * 3 + _button_height * 2),
                                      (_button_width, _button_height))
        self.toggle_positions_btn = pygui.elements.UIButton(relative_rect=_positions_rect,
                                                            text="Toggle Pos",
                                                            manager=self.manager,
                                                            container=self.settings_window)
        _reset_rect = pygame.Rect((_hor_padding, _vert_padding * 4 + _button_height * 3),
                                  (_button_width, _button_height))
        self.reset_btn = pygui.elements.UIButton(relative_rect=_reset_rect,
                                                 text="Reset",
                                                 manager=self.manager,
                                                 container=self.settings_window)
        _done_rect = pygame.Rect((_hor_padding, _vert_padding * 5 + _button_height * 4),
                                 (_button_width, _button_height))
        self.done_btn = pygui.elements.UIButton(relative_rect=_done_rect,
                                                text="Done",
                                                manager=self.manager,
                                                container=self.settings_window)

    def position_draw(self):
        """Draw the lines that depict the robot's path historically."""
        if self.draw_positions:
            try:
                pygame.draw.lines(self.screen, (255, 0, 0),
                                  False, self.robot.truth_pos)
                pygame.draw.lines(self.screen, (0, 0, 255),
                                  False, self.slam.odo_pos)
            except ValueError:
                pass

    def toggle_positions(self):
        """Toggle whether or not the robot's historical path is visualised."""
        if self.draw_positions:
            self.draw_positions = False
        else:
            self.draw_positions = True

    def world_editor_setup(self):
        """Setup the world editor screen."""
        _button_width = 110
        _button_height = 40
        _vert_padding = 20
        _hor_padding = 20

        _done_rect = pygame.Rect((self.screen.get_width() - _button_width - _hor_padding,
                                  self.screen.get_height() - _button_height - _vert_padding),
                                 (_button_width, _button_height))
        self.we_done_btn = pygui.elements.UIButton(relative_rect=_done_rect,
                                                   text="Done",
                                                   manager=self.manager)

        _clear_rect = pygame.Rect((self.screen.get_width() - _button_width - _hor_padding,
                                   _vert_padding),
                                  (_button_width, _button_height))
        self.we_clear_btn = pygui.elements.UIButton(relative_rect=_clear_rect,
                                                    text="Clear",
                                                    manager=self.manager)

        _mode_rect = pygame.Rect((self.screen.get_width() - _button_width - _hor_padding,
                                  _vert_padding * 2 + _button_height),
                                 (_button_width, _button_height))
        self.we_mode_btn = pygui.elements.UIButton(relative_rect=_mode_rect,
                                                   text="Erase",
                                                   manager=self.manager)

    def world_editor_mode_button(self):
        """Toggle between draw/erase modes of the world editor."""
        if self.we_draw_mode:
            self.we_mode_btn.set_text("Draw")
            self.we_draw_mode = False
        else:
            self.we_mode_btn.set_text("Erase")
            self.we_draw_mode = True

    def world_editor(self, _mouse_click, _pos):
        """Draw onto the world grid if mouse is down and draw the current world grid."""

        def world_editor_button_hover(_pos):
            """Return true if the position is within any of the world editor buttons."""
            _return = np.array([self.we_clear_btn.hover_point(_pos[0], _pos[1]),
                                self.we_done_btn.hover_point(_pos[0], _pos[1]),
                                self.we_mode_btn.hover_point(_pos[0], _pos[1])])
            return _return.any()

        def world_editor_centre_hover(_pos):
            """Return true if the position is within where the robot will spawn."""
            _hor_cen = self.screen.get_width() / 2
            _vert_cen = self.screen.get_height() / 2
            _robot_size = self.robot.robot.robot_size
            _return = np.array([_pos[0] > _hor_cen - _robot_size,
                                _pos[0] < _hor_cen + _robot_size,
                                _pos[1] < _vert_cen + _robot_size,
                                _pos[1] > _vert_cen - _robot_size])
            return _return.all()

        if _mouse_click:
            # Find the distance between the last known mouse position and find the
            # points in a line between them
            if self.last_mouse_pos != None:
                _last_point_dis = utils.point_distance(self.last_mouse_pos[0], _pos[0],
                                                       _pos[1], self.last_mouse_pos[1])
            else:
                _last_point_dis = 0
            # If clicking on a button don't draw anything
            if (_last_point_dis < 8 and world_editor_button_hover(_pos)) or _last_point_dis == 0:
                _line = []
            else:
                _line = utils.line_between(self.last_mouse_pos[0],
                                           self.last_mouse_pos[1],
                                           _pos[0], _pos[1])
            # Write to the grid map all the points on the line if not in the robot's spawn space
            for _point in _line:
                if not world_editor_centre_hover(_point):
                    _grid_x = int(_point[0] / self.world.size)
                    _grid_y = int(_point[1] / self.world.size)
                    self.world.write_to_map(self.we_draw_mode,
                                            _grid_x,
                                            _grid_y)
            self.last_mouse_pos = _pos

        for i in range(len(self.world.grid)):
            for j in range(len(self.world.grid[0])):
                if self.world.grid[i][j]:
                    pygame.draw.rect(self.screen,
                                     (0, 0, 0),
                                     pygame.Rect((j * self.world.size, i * self.world.size),
                                                 (self.world.size, self.world.size)))

    def reset(self):
        """Reset the game state."""
        self.robot.reset()
        self.slam.reset()


class Robot(pygame.sprite.Sprite):
    """Sprite  the robot player object.

    Handles the attributes of the robot, including its collision mask. Also handles robot state
    updates including translational and rotational changes. This class also contains the lidar
    sensor calculations.

    Attributes:
        _p_screen: The main pygame screen surface.
        _p_world: The world map as drawn by the World class.
    """

    def __init__(self, _p_screen, _p_world):
        pygame.sprite.Sprite.__init__(self)
        self.screen = _p_screen
        self.world = _p_world
        self.image = pygame.image.load("roomba.png")
        self.robot_size = 50
        self.image = pygame.transform.smoothscale(self.image,
                                                  (self.robot_size, self.robot_size))
        self.image_size = self.image.get_size()
        self.og_image = self.image.copy()
        self.rect = self.image.get_rect()
        self.x_pos = float(self.screen.get_size()[0] / 2)
        self.y_pos = float(self.screen.get_size()[1] / 2)
        self.angle = 0
        self.rect.center = (self.x_pos, self.y_pos)
        self.hitbox = pygame.Rect(self.x_pos - (self.image_size[0] / 2),
                                  self.y_pos - (self.image_size[1] / 2),
                                  self.image_size[0] + 2,
                                  self.image_size[1] + 2)
        self.mask = pygame.mask.from_surface(self.image)
        self.draw_lidar = True

        # Lidar setup
        self.sample_rate = 5  # Hz
        self.lidar_state = 0
        self.sample_count = 32
        self.point_cloud = [[0, 0] for _ in range(self.sample_count)]
        self.angle_ref = []
        self.new_sample = True

        self.lasers = pygame.sprite.Group()
        _lidar = pygame.math.Vector2()
        _lidar.xy = (self.x_pos, self.y_pos)
        self.initial_laser_length = int(np.sqrt(
            np.square(self.screen.get_width()) + np.square(self.screen.get_height())))
        for i in range(self.sample_count):
            _degree_multiplier = 360 / self.sample_count
            _cur_angle = int(i * _degree_multiplier)
            self.angle_ref.append(_cur_angle)
            _laser = pygame.math.Vector2()
            _laser.from_polar((self.initial_laser_length, _cur_angle))
            _laser_sprite = Laser(self.screen, _lidar, _laser)
            self.lasers.add(_laser_sprite)
        self.lasers_draw = pygame.sprite.Group()

    def reset(self):
        """Reset the robots position and sensor data."""
        self.x_pos = float(self.screen.get_size()[0] / 2)
        self.y_pos = float(self.screen.get_size()[1] / 2)
        self.angle = 0
        self.rect.center = (self.x_pos, self.y_pos)
        self.hitbox = pygame.Rect(self.x_pos - (self.image_size[0] / 2),
                                  self.y_pos - (self.image_size[1] / 2),
                                  self.image_size[0] + 2,
                                  self.image_size[1] + 2)
        self.point_cloud = [[0, 0] for _ in range(self.sample_count)]

    def update(self):
        """Updates the position of the robot's rect, hitbox and mask."""
        self.rect.center = (self.x_pos, self.y_pos)
        self.hitbox.center = (self.x_pos, self.y_pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.lidar()
        if self.draw_lidar:
            for _point in self.point_cloud:
                _coords = [int(_point[0] * np.cos(_point[1]) + self.x_pos),
                           int(_point[0] * np.sin(_point[1]) + self.y_pos)]
                pygame.draw.aaline(self.screen,
                                   (255, 0, 0, 255),
                                   (self.x_pos, self.y_pos),
                                   _coords)
                pygame.draw.circle(self.screen,
                                   (0, 0, 255, 255),
                                   _coords,
                                   3)

    def toggle_lidar(self):
        """Toggle whether or not the lidar sensor is visualised."""
        if self.draw_lidar:
            self.draw_lidar = False
        else:
            self.draw_lidar = True

    def rotate(self, _direction):
        """Rotates the robot around it's centre."""
        self.image = pygame.transform.rotate(self.og_image, _direction)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x_pos, self.y_pos)

    def lidar(self):
        """Performs all calculations for laser range finding and handles the drawing of lasers.

        This function uses sprites to determine all of the objects each laser around the robot is
        colliding with, then finds the closest wall. It then finds the closest point on that wall
        to the robot.
        """
        # TODO: Fix flickering on some diagonal lasers
        # TODO: Make lasers that don't find a result return max length instead of previous result
        _iterations_per_frame = int(
            self.sample_count / (30 / self.sample_rate))
        _slice_from = self.lidar_state * _iterations_per_frame
        if self.lidar_state == (30 // self.sample_rate) - 2:
            # Ensure final slice gets the remainder
            _slice_to = self.sample_count
        else:
            _slice_to = _slice_from + _iterations_per_frame
        # Update the position of each of the laser sprites in self.lasers
        _lidar = pygame.math.Vector2()
        _lidar.xy = (self.x_pos, self.y_pos)
        for _sprite in self.lasers.sprites()[_slice_from:_slice_to]:
            _sprite.origin = _lidar
            _sprite.update()

        # Check wall collisions in quadrants
        _quad_list = [[[0, 90], operator.ge, operator.ge],
                      [[90, 181], operator.lt, operator.ge],
                      [[-90, 0], operator.ge, operator.lt],
                      [[-181, -90], operator.lt, operator.lt]]
        _collision_list = {}
        _pixel_buffer = self.world.size * 2
        for _quad in _quad_list:
            _quad_lasers = pygame.sprite.Group()
            _quad_walls = pygame.sprite.Group()
            for _laser in self.lasers.sprites()[_slice_from:_slice_to]:
                _cur_angle = int(_laser.angle.as_polar()[1])
                if _cur_angle >= _quad[0][0] and _cur_angle < _quad[0][1]:
                    _quad_lasers.add(_laser)
            for _wall in self.world.wall_list:
                _cur_pos = _wall.rect.center
                if _quad[1] == operator.ge:
                    _x_buf = self.x_pos - _pixel_buffer
                else:
                    _x_buf = self.x_pos + _pixel_buffer
                if _quad[2] == operator.ge:
                    _y_buf = self.y_pos - _pixel_buffer
                else:
                    _y_buf = self.y_pos + _pixel_buffer
                if _quad[1](_cur_pos[0], _x_buf):
                    if _quad[2](_cur_pos[1], _y_buf):
                        _quad_walls.add(_wall)
            _collision_list.update(pygame.sprite.groupcollide(_quad_lasers,
                                                              _quad_walls,
                                                              False,
                                                              False,
                                                              pygame.sprite.collide_mask))

        if _collision_list:
            for _laser in _collision_list:
                # For each laser, find the closest wall to the robot it is colliding with
                _closest_wall = None
                _closest_distance = self.initial_laser_length
                for _wall in _collision_list[_laser]:
                    cur_distance = utils.point_distance(self.x_pos,
                                                        _wall.rect.center[0],
                                                        self.y_pos,
                                                        _wall.rect.center[1])
                    if cur_distance < _closest_distance:
                        _closest_wall = _wall
                        _closest_distance = cur_distance

                # Find the closest point on the closest wall to the robot
                _current_pos = pygame.math.Vector2()
                _current_pos.update(self.x_pos, self.y_pos)
                _heading = _laser.angle
                _direction = _heading.normalize()
                _closest_point = [self.initial_laser_length,
                                  self.initial_laser_length]
                for _ in range(self.initial_laser_length):
                    _current_pos += _direction
                    if _closest_wall.rect.collidepoint(_current_pos):
                        _r = np.sqrt(np.square(self.x_pos - _current_pos.x)
                                     + np.square(self.y_pos - _current_pos.y))
                        _theta = np.arctan2(-(self.y_pos - _current_pos.y), -
                                            (self.x_pos - _current_pos.x))
                        _closest_point = [_r, _theta]
                        break

                # Write resulting point to the point cloud
                if not _closest_point == [self.initial_laser_length, self.initial_laser_length]:
                    _cur_angle = (round(_heading.as_polar()[1]) + 450) % 360
                    try:
                        self.point_cloud[self.angle_ref.index(
                            _cur_angle)] = _closest_point
                    except ValueError:
                        pass

        if self.lidar_state == (30 // self.sample_rate) - 1:
            self.new_sample = True
            self.lidar_state = 0
        else:
            self.lidar_state += 1


class RobotControl():
    """Controls the robot.

    Handles the robot's translation and rotation based on user input, including collisions,
    acceleration and deceleration.

    Attributes:
        _p_screen: The main pygame screen surface.
        _p_world: The world map as drawn by the World class.
    """

    def __init__(self, _p_screen, _p_world):
        self.screen = _p_screen
        self.robot = Robot(self.screen, _p_world)
        self.world = _p_world
        # (+x velocity, +y velocity, velocity magnitude) pixels/tick
        self.velocity = [0, 0, 0]
        self.odo_velocity = self.velocity
        self.max_velocity = 4
        self.acceleration = 0.5
        self.cur_keys = []
        self.angular_velocity = 6
        self.dummy_screen = pygame.Surface(self.screen.get_size())
        self.collision_list = []
        self.recursion_depth = 0
        self.truth_pos = []

    def reset(self):
        """Reset the robot's attributes, including position and velocities."""
        self.robot.x_pos = self.screen.get_size()[0] / 2
        self.robot.y_pos = self.screen.get_size()[1] / 2
        self.robot.rect.center = (self.robot.x_pos, self.robot.y_pos)
        self.velocity = [0, 0, 0]
        self.odo_velocity = self.velocity
        self.robot.angle = 0
        self.truth_pos = []
        self.robot.reset()
        self.update()

    def update(self):
        """Update all aspects of the robot, including velocities, position and lidar sensor."""
        self.move_velocity()
        self.robot.rotate(self.robot.angle)
        self.robot.update()
        self.screen.blit(self.robot.image, self.robot.rect)

    def move_velocity(self):
        """Controls the robot's position.

        This function takes in the Robot.velocity vector. The collision method returns, what side,
        if any, of the robot is colliding. It then sets the velocity in that direction to zero so
        the robot will maintain it's velocity in the perpendicular axis, but stops moving towards
        the collision. Then update the robot's position. If the robot isn't receiving input to move
        forward, decelerate velocities.
        """
        # Check if a collision has occurred, and zero the velocity axis associated with it.
        _collision_side = self.collision_detector()
        self.collision_list.append(_collision_side)
        if len(self.collision_list) > 3:
            self.collision_list.pop(0)
        if not _collision_side:
            self.collision_list = []
        if "TOP" in self.collision_list:
            if self.velocity[1] < 0:
                self.velocity[1] = 0
        if "BOTTOM" in self.collision_list:
            if self.velocity[1] > 0:
                self.velocity[1] = 0
        if "RIGHT" in self.collision_list:
            if self.velocity[0] > 0:
                self.velocity[0] = 0
        if "LEFT" in self.collision_list:
            if self.velocity[0] < 0:
                self.velocity[0] = 0

        # Update robot position according to the velocity vector.
        self.robot.x_pos += self.velocity[0]
        self.robot.y_pos += self.velocity[1]
        self.robot.rect.center = (self.robot.x_pos, self.robot.y_pos)
        self.odo_velocity = self.velocity
        if len(self.truth_pos) > 1000:
            self.truth_pos.pop(0)
        self.truth_pos.append([self.robot.x_pos, self.robot.y_pos])

        # Decelerate the velocity vector if no forward input is received.
        _deceleration = self.acceleration / 2
        if "UP" not in self.cur_keys:
            if self.velocity[0] > 0:
                self.velocity[0] -= _deceleration
            if self.velocity[0] < 0:
                self.velocity[0] += _deceleration
            if self.velocity[1] > 0:
                self.velocity[1] -= _deceleration
            if self.velocity[1] < 0:
                self.velocity[1] += _deceleration
            if self.velocity[0] < _deceleration and self.velocity[0] > _deceleration * -1:
                self.velocity[0] = 0
            if self.velocity[1] < _deceleration and self.velocity[1] > _deceleration * -1:
                self.velocity[1] = 0

    def change_velocity(self, _keys):
        """Controls the robot's velocity.

        This function receives input from the user and updates the Robot.angular_velocity and
        Robot.velocity vectors accordingly.

        Attributes:
            _keys: An array containing the current state of all keys.
        """
        # Get input and sets the rotation according to the angular velocity.
        _pressed_keys = self.convert_key(_keys)
        if "RIGHT" in _pressed_keys:
            self.robot.angle -= self.angular_velocity
        if "LEFT" in _pressed_keys:
            self.robot.angle += self.angular_velocity

        # Bind the robot.angle to remain < 180 and > -180.
        if self.robot.angle > 180:
            self.robot.angle = -180 + (self.robot.angle - 180)
        elif self.robot.angle < -180:
            self.robot.angle = 180 + (self.robot.angle + 180)

        # Calculate the current magnitude of the velocity vector.
        _speed = self.acceleration * 2
        self.velocity[2] = np.sqrt(
            np.square(self.velocity[0]) + np.square(self.velocity[1]))

        # Calculate the axis velocity components according to the current direction and desired
        # speed.
        _x_vec = np.cos(-1 * np.deg2rad(self.robot.angle + 90)) * _speed
        _y_vec = np.sin(-1 * np.deg2rad(self.robot.angle + 90)) * _speed
        if "UP" in _pressed_keys:
            self.velocity[0] += self.acceleration * _x_vec
            self.velocity[1] += self.acceleration * _y_vec
            self.velocity[2] = np.sqrt(
                np.square(self.velocity[0]) + np.square(self.velocity[1]))
            # Normalise the velocity vectors if the velocity's magnitude is greater than the
            # desired maximum velocity.
            if self.velocity[2] > self.max_velocity:
                _divider = self.max_velocity / \
                    np.sqrt(
                        np.square(self.velocity[0]) + np.square(self.velocity[1]))
                self.velocity[0] = _divider * self.velocity[0]
                self.velocity[1] = _divider * self.velocity[1]

    def convert_key(self, _keys):
        """Converts the pressed key information into a string array.

        This function takes the passed array of pygame keys and converts it to a list of the
        currently pressed keys.

        Attributes:
            keys: An array containing the current state of all keys.
        """
        _action = False
        _keys_to_check = [[pygame.K_LEFT, "LEFT"],
                          [pygame.K_RIGHT, "RIGHT"],
                          [pygame.K_UP, "UP"],
                          [pygame.K_DOWN, "DOWN"],
                          [pygame.K_r, "R"]]
        for _key in _keys_to_check:
            if _keys[_key[0]]:
                if _key[1] not in self.cur_keys:
                    self.cur_keys.append(_key[1])
                _action = True
            else:
                try:
                    self.cur_keys.remove(_key[1])
                except ValueError:
                    pass
        # When a key is added, remove the first keys so that only the last two remain
        if _action:
            self.cur_keys = self.cur_keys[-2:]
        else:
            self.cur_keys = []
        return self.cur_keys

    def collision_detector(self):
        """Finds if the robot is colliding and the associated side.

        This function uses sprites to determine all of the objects the robot is colliding with,
        then finds the closest wall to determine which side of the robot is colliding. To solve for
        cases where the robot is colliding with two walls simultaneously, the function utilises
        recursion to find the second closest wall.
        """
        _collision_list = pygame.sprite.spritecollide(self.robot,
                                                      self.world.wall_list,
                                                      False,
                                                      pygame.sprite.collide_mask)
        if len(_collision_list) > 0:
            # Find the closest colliding wall
            _closest_distance = self.robot.initial_laser_length
            _closest_wall = None
            for _wall in _collision_list:
                cur_distance = utils.point_distance(self.robot.x_pos,
                                                    _wall.rect.center[0],
                                                    self.robot.y_pos,
                                                    _wall.rect.center[1])
                if cur_distance < _closest_distance:
                    s_closest_wall = _closest_wall
                    _closest_wall = _wall
                    _closest_distance = cur_distance
            # If performing recursion, find the second closest wall
            if self.recursion_depth > 0 and not s_closest_wall is None:
                _closest_wall = s_closest_wall
            _wall = _closest_wall

            # Find which side of the robot is closest to the closest wall
            _sides = [self.robot.hitbox.midtop, self.robot.hitbox.midright,
                      self.robot.hitbox.midbottom, self.robot.hitbox.midleft]
            _closest_side = -1
            _closest_side_distance = self.robot.initial_laser_length
            for _i, _side in enumerate(_sides):
                distance = utils.point_distance(_side[0],
                                                _wall.rect.center[0],
                                                _side[1],
                                                _wall.rect.center[1])
                if distance < _closest_side_distance:
                    _closest_side_distance = distance
                    _closest_side = _i
            _to_return = None
            if _closest_side == 0:
                _to_return = "TOP"
            if _closest_side == 1:
                _to_return = "RIGHT"
            if _closest_side == 2:
                _to_return = "BOTTOM"
            if _closest_side == 3:
                _to_return = "LEFT"

            # If the robot is already colliding with a wall, collide the second closest wall
            if len(self.collision_list) > 0:
                if _to_return == self.collision_list[len(self.collision_list) - 1]:
                    if self.recursion_depth <= 1:
                        self.recursion_depth += 1
                        return self.collision_detector()
            self.recursion_depth = 0
            return _to_return
        return None


class Laser(pygame.sprite.Sprite):
    """Sprite for the lidar sensor's laser beams.

    Handles the attributes of each laser. Uses invisible surfaces to calculate positional offsets
    for each laser depending on its given rotation. Also contains the laser's collision mask. It
    also handles the positional updates sent from RobotControl.

    Attributes:
        _p_screen: The main pygame screen surface.
        _origin: A pygame.math.Vector2() object that is the robot's base position.
        _angle: A pygame.math.Vector2() object that contains polar coordinates stating the laser's
            length and direction _angle.
    """

    def __init__(self, _p_screen, _origin, _angle):
        pygame.sprite.Sprite.__init__(self)

        # Use a "dummy" surface to determine the width and height of the rotated laser rect
        _dummy_screen = pygame.Surface(
            (_p_screen.get_height() * 2, _p_screen.get_width() * 2),
            pygame.SRCALPHA)
        _dummy_rect = pygame.draw.line(_dummy_screen,
                                       (0, 255, 0, 255),
                                       _origin + _origin,
                                       _origin + _origin + _angle)

        self.origin = _origin
        self.angle = _angle
        _int_angle = int(_angle.as_polar()[1])
        # Find an offset for the laser's draw position depending on its angle
        if 0 <= _int_angle <= 90:
            self.x_offset = 0
            self.y_offset = 0
        elif _int_angle > 90:
            self.x_offset = -_dummy_rect.width
            self.y_offset = 0
        elif _int_angle < -90:
            self.x_offset = -_dummy_rect.width
            self.y_offset = -_dummy_rect.height
        elif -90 <= _int_angle < 0:
            self.x_offset = 0
            self.y_offset = -_dummy_rect.height

        self.screen = _p_screen
        self.image = pygame.Surface((_dummy_rect.width, _dummy_rect.height),
                                    pygame.SRCALPHA)
        self.new_start = (self.origin.x + self.x_offset,
                          self.origin.y + self.y_offset)
        self.rect = pygame.draw.aaline(self.image,
                                       (255, 0, 0, 255),
                                       (-self.x_offset, - self.y_offset),
                                       (int(_angle.x - self.x_offset),
                                        int(_angle.y - self.y_offset)))
        self.mask = pygame.mask.from_surface(self.image, 50)

    def update(self):
        """Update the laser's position."""
        self.new_start = (self.origin.x + self.x_offset,
                          self.origin.y + self.y_offset)
        self.rect.topleft = self.new_start


class Wall(pygame.sprite.Sprite):
    """Sprite for the lidar sensor's laser beams.

    Handles the attributes of each laser. Uses invisible surfaces to calculate positional offsets
    for each laser depending on its given rotation. Also contains the laser's collision mask.

    Attributes:
        _top: The desired pixel for the top of the wall.
        _left: The desired pixel for the left of the wall.
        _width: The desired width of the wall.
        _height: The desired height of the wall.
    """

    def __init__(self, _left, _top, _width, _height):
        pygame.sprite.Sprite.__init__(self)
        self.rect = pygame.Rect(_left, _top, _width, _height)
        self.color = (0, 0, 0, 255)
        self.image = pygame.Surface((_width, _height), pygame.SRCALPHA)
        self.image.fill(self.color)
        self.mask = pygame.mask.from_threshold(self.image,
                                               pygame.Color('black'),
                                               (1, 1, 1, 255))

    def update(self, _color):
        """Update the wall's colour.

        Used for debugging purposes only at this stage.
        """
        self.image.fill(_color)


class World():
    """Writes and draws the world map.

    Handles the attributes for the world map and draws.

    Attributes:
        _p_screen: The main pygame screen surface.
    """

    def __init__(self, _p_screen):
        self.screen = _p_screen
        self.size = 20
        self.grid = [[0 for _ in range(self.screen.get_size()[0] // self.size)]
                     for __ in range(self.screen.get_size()[1] // self.size)]
        self.wall_list = pygame.sprite.Group()

    def write_map(self):
        """Draws the world map into an array of 1s and 0s."""
        for i, _ in enumerate(self.grid):
            for j, __ in enumerate(self.grid[0]):
                if i == 0 or i == len(self.grid) - 1 or j == 0 or j == len(self.grid[0]) - 1:
                    self.grid[i][j] = 1
                else:
                    self.grid[i][j] = 0
                if 20 < i < 30:
                    if 20 < j < 30:
                        self.grid[i][j] = 1

    def create_sprites(self):
        """Add sprites in the positions indicated by the self.grid array to a sprite group."""
        self.wall_list.empty()
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                if self.grid[i][j]:
                    wall_rect = Wall(j * self.size,
                                     i * self.size,
                                     self.size,
                                     self.size)
                    self.wall_list.add(wall_rect)

    def clear_map(self):
        self.grid = [[0 for _ in range(self.screen.get_size()[0] // self.size)]
                     for __ in range(self.screen.get_size()[1] // self.size)]

    def write_to_map(self, _mode, _x, _y):
        if _mode:
            self.grid[_y][_x] = 1
        else:
            self.grid[_y][_x] = 0

    def draw(self):
        """Draw the world map."""
        self.wall_list.draw(self.screen)


class SLAM():
    """Contains all aspects of the SLAM algorithm (WIP).

    Handles calculations and drawing of the occupancy grid map. Creates fake odometry positioning.

    Attributes:
        _p_screen: The main pygame screen surface.
        _p_robot: The robot object.
    """

    def __init__(self, _p_screen, _p_robot):
        self.screen = _p_screen
        self.robot = _p_robot

        # Occupancy Grid Setup
        self.grid_size = 11
        self.grid = [[0.5 for _ in range(self.screen.get_size()[0] // self.grid_size)]
                     for __ in range(self.screen.get_size()[1] // self.grid_size)]
        self.show_occupancy_grid = False

        # Odometry Setup
        self.odo_x = self.robot.robot.x_pos
        self.odo_y = self.robot.robot.y_pos
        self.odo_error = 0.2
        self.odo_pos = []

    def reset(self):
        """Reset the SLAM state."""
        self.grid = [[0.5 for _ in range(self.screen.get_size()[0] // self.grid_size)]
                     for __ in range(self.screen.get_size()[1] // self.grid_size)]
        self.odo_x = self.robot.robot.x_pos
        self.odo_y = self.robot.robot.y_pos
        self.odo_pos = []

    def update(self):
        """Update SLAM visuals."""
        if self.show_occupancy_grid:
            self.draw_grid()

    def odometry(self, _vel_vector):
        """Adds a random error to the positional data within a percentage tolerance."""
        try:
            self.odo_x += random.uniform(_vel_vector[0] - _vel_vector[0] * self.odo_error,
                                         _vel_vector[0] + _vel_vector[0] * self.odo_error)
            self.odo_y += random.uniform(_vel_vector[1] - _vel_vector[1] * self.odo_error,
                                         _vel_vector[1] + _vel_vector[1] * self.odo_error)
            if len(self.odo_pos) > 1000:
                self.odo_pos.pop(0)
            self.odo_pos.append([self.odo_x, self.odo_y])
        except ValueError:
            pass

    def occupancy_grid(self):
        """Occupance grid algorithm.

        Loops through all points in the point cloud and lowers the probability of a space in the
        grid being occupied if it is found on a line between the robot and a point, and increases
        the probability if it is found at the end-point of the laser.
        """

        _rate_of_change = 0.05  # The rate at which the probability of a point is changed
        _pc = self.robot.robot.point_cloud
        for _point in _pc:
            try:  # Catch instances where the end-point may be out of the game screen
                _coords = [int(_point[0] * np.cos(_point[1]) + self.odo_x),  # Convert to cartesian
                           int(_point[0] * np.sin(_point[1]) + self.odo_y)]
                # Loop through the points in between the robot and the end-point of a laser
                for _clear in utils.line_between(self.robot.robot.x_pos // self.grid_size,
                                                 self.robot.robot.y_pos // self.grid_size,
                                                 _coords[0] // self.grid_size,
                                                 _coords[1] // self.grid_size)[:-1]:
                    # Decrease occupancy probability
                    self.grid[int(_clear[1])][int(
                        _clear[0])] -= _rate_of_change
                    if self.grid[int(_clear[1])][int(_clear[0])] < 0:
                        self.grid[int(_clear[1])][int(_clear[0])] = 0
                _grid_y = int(_coords[1] // self.grid_size)
                _grid_x = int(_coords[0] // self.grid_size)
                # Increase occupancy probability of the end-point
                self.grid[_grid_y][_grid_x] += _rate_of_change
                if self.grid[_grid_y][_grid_x] > 1:
                    self.grid[_grid_y][_grid_x] = 1
            except IndexError:
                pass

    def toggle_occupancy_grid(self):
        """Toggle whether or not the occupancy grid is visualised."""
        if self.show_occupancy_grid:
            self.show_occupancy_grid = False
        else:
            self.show_occupancy_grid = True

    def draw_grid(self):
        """Draw the occupancy grid as a function of its probability as its alpha."""
        for i in range(len(self.grid)):
            for j in range(len(self.grid[0])):
                _alpha = 1 - self.grid[i][j]
                _rect = pygame.Rect(j * self.grid_size,
                                    i * self.grid_size,
                                    self.grid_size,
                                    self.grid_size)
                pygame.draw.rect(self.screen,
                                 (255 * _alpha, 255 * _alpha, 255 * _alpha),
                                 _rect)


if __name__ == '__main__':
    Game()
