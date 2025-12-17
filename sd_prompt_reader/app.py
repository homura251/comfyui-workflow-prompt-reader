__author__ = "receyuki"
__filename__ = "app.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

import platform
import sys
import os
import threading
from collections import OrderedDict
import xml.etree.ElementTree as ET
from tkinter import PhotoImage, Menu

import pyperclip as pyperclip
from CTkToolTip import *
from PIL import Image, ImageDraw
from customtkinter import (
    ScalingTracker,
    CTkButton,
    CTkFrame,
    ThemeManager,
    filedialog,
    CTkOptionMenu,
    set_default_color_theme,
)
from tkinterdnd2 import DND_FILES

from .button import *
from .constants import *
from .ctkdnd import Tk
from .image_data_reader import ImageDataReader
from .parameter_viewer import ParameterViewer
from .prompt_viewer import PromptViewer
from .status_bar import StatusBar
from .textbox import STkTextbox
from .update_checker import UpdateChecker
from .__version__ import VERSION
from .logger import Logger


class App(Tk):
    def __init__(self):
        super().__init__()

        logger = Logger("SD_Prompt_Reader.App")
        Logger.configure_global_logger("INFO")
        # window = TkinterDnD.Tk()
        # window = Tk()
        self.title("SD Prompt Reader")
        self.geometry("1280x600")
        # set_appearance_mode("Light")
        # deactivate_automatic_dpi_awareness()
        # set_widget_scaling(1)
        # set_window_scaling(0.8)
        # info_font = CTkFont(size=20)
        self.info_font = CTkFont()
        self.scaling = ScalingTracker.get_window_dpi_scaling(self)
        set_default_color_theme(COLOR_THEME)

        # remove menubar on macos
        empty_menubar = Menu(self)
        self.config(menu=empty_menubar)

        # load icon images
        self.drop_image = CTkImage(Image.open(DROP_FILE), size=(48, 48))
        self.clipboard_image = self.load_icon(COPY_FILE_L, (24, 24))
        self.clipboard_image_s = self.load_icon(COPY_FILE_S, (20, 20))
        self.clear_image = self.load_icon(CLEAR_FILE, (24, 24))
        self.document_image = self.load_icon(DOCUMENT_FILE, (24, 24))
        self.edit_image = self.load_icon(EDIT_FILE, (24, 24))
        self.edit_off_image = self.load_icon(EDIT_OFF_FILE, (24, 24))
        self.save_image = self.load_icon(SAVE_FILE, (24, 24))
        self.expand_image = self.load_icon(EXPAND_FILE, (12, 24))
        self.sort_image = self.load_icon(SORT_FILE, (20, 20))
        self.view_image = self.load_icon(LIGHTBULB_FILE, (20, 20))
        self.icon_image = CTkImage(Image.open(ICON_FILE), size=(100, 100))
        self.icon_cube_image = CTkImage(Image.open(ICON_CUBE_FILE), size=(100, 100))

        self.icon_image_pi = PhotoImage(file=ICON_FILE)
        self.iconphoto(False, self.icon_image_pi)
        if platform.system() == "Windows":
            self.iconbitmap(ICO_FILE)

        # configure layout
        self.rowconfigure(tuple(range(4)), weight=1)
        self.columnconfigure(tuple(range(7)), weight=1)
        self.columnconfigure(0, weight=6)
        # self.rowconfigure(0, weight=2)
        # self.rowconfigure(1, weight=2)
        # self.rowconfigure(2, weight=1)
        # self.rowconfigure(3, weight=1)

        # image display
        self.image_frame = CTkFrame(self)
        self.image_frame.grid(
            row=0, column=0, rowspan=4, sticky="news", padx=20, pady=20
        )

        self.image_label = CTkLabel(
            self.image_frame,
            width=560,
            text="\n" + VERSION + "\n\n" + MESSAGE["drop"][0],
            image=self.icon_cube_image,
            compound="top",
            text_color=ACCESSIBLE_GRAY,
        )
        self.image_label.pack(fill="both", expand=True)
        self.image_label.bind("<Button-1>", self.on_image_click)
        self.image_label.bind("<Motion>", self.on_image_motion)
        self.image_label.bind("<Leave>", self.on_image_leave)

        # image navigation (previous/next)
        self._image_sequence = []
        self._image_sequence_index = None
        self._image_sequence_index_by_key = {}
        self._image_sequence_dir_key = None
        self._image_sequence_scan_id = 0
        self._image_sequence_scanning = False

        self._image_cache = OrderedDict()
        self._image_cache_max = 6

        self._image_load_lock = threading.Lock()
        self._image_load_event = threading.Event()
        self._image_load_requested_path = None
        self._image_load_requested_max_dim = None
        self._image_load_request_id = 0

        # navigation icons are rendered onto the displayed image (no widget background)
        self._nav_prev_svg = Path(RESOURCE_DIR, "nav_prev.svg")
        self._nav_next_svg = Path(RESOURCE_DIR, "nav_next.svg")
        self._nav_prev_enabled = False
        self._nav_next_enabled = False
        self._nav_prev_bbox = None
        self._nav_next_bbox = None
        self._nav_icon_cache = {}
        self._metadata_after_id = None

        self.image = None
        self.image_tk = None
        self.image_data = None
        self.textbox_fg_color = ThemeManager.theme["CTkTextbox"]["fg_color"]
        self.readable = False

        # status bar
        self.status_bar = StatusBar(self)
        self.status_bar.status_frame.grid(
            row=3,
            column=6,
            sticky="ew",
            padx=20,
            pady=(0, 20),
            ipadx=STATUS_BAR_IPAD,
            ipady=STATUS_BAR_IPAD,
        )

        # textbox
        self.positive_box = PromptViewer(self, self.status_bar, "Prompt")
        self.positive_box.viewer_frame.grid(
            row=0, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(20, 20)
        )

        self.negative_box = PromptViewer(self, self.status_bar, "Negative Prompt")
        self.negative_box.viewer_frame.grid(
            row=1, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(0, 20)
        )

        self.setting_box = STkTextbox(self, wrap="word", height=80)
        self.setting_box.grid(
            row=2, column=1, columnspan=6, sticky="news", padx=(0, 20), pady=(1, 21)
        )
        self.setting_box.text = "Setting"

        # setting box simple mode
        self.setting_box_simple = CTkFrame(
            self, height=80, fg_color=self.textbox_fg_color
        )
        self.setting_box_parameter = CTkFrame(
            self.setting_box_simple, fg_color="transparent"
        )
        self.setting_box_parameter = ParameterViewer(
            self.setting_box_simple, self.status_bar
        )
        self.setting_box_parameter.setting_box_parameter.pack(side="left", padx=5)

        # setting box
        self.button_setting_frame = CTkFrame(self.setting_box, fg_color="transparent")
        self.button_setting_frame.grid(row=0, column=1, padx=(20, 10), pady=(5, 0))
        self.button_copy_setting = STkButton(
            self.button_setting_frame,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.clipboard_image_s,
            text="",
            command=lambda: self.copy_to_clipboard(self.setting_box.ctext),
        )
        self.button_copy_setting.pack(side="top", pady=(0, 10))
        self.button_copy_setting_tooltip = CTkToolTip(
            self.button_copy_setting,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["copy_setting"],
        )
        self.button_view_setting = STkButton(
            self.button_setting_frame,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.view_image,
            text="",
            command=lambda: self.setting_mode_switch(),
            mode=SettingMode.NORMAL,
        )
        self.button_view_setting.pack(side="top")
        self.button_view_setting_tooltip = CTkToolTip(
            self.button_view_setting,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["view_setting"],
        )

        # setting box simple mode
        self.button_setting_frame_simple = CTkFrame(
            self.setting_box_simple, fg_color="transparent"
        )
        self.button_setting_frame_simple.pack(side="right", padx=(20, 10), pady=5)
        self.button_copy_setting_simple = STkButton(
            self.button_setting_frame_simple,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.clipboard_image_s,
            text="",
            command=lambda: self.copy_to_clipboard(self.image_data.setting),
        )
        self.button_copy_setting_simple.pack(side="top", pady=(0, 10))
        self.button_copy_setting_simple_tooltip = CTkToolTip(
            self.button_copy_setting_simple,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["copy_setting"],
        )
        self.button_view_setting_simple = STkButton(
            self.button_setting_frame_simple,
            width=BUTTON_WIDTH_S,
            height=BUTTON_HEIGHT_S,
            image=self.view_image,
            text="",
            command=lambda: self.setting_mode_switch(),
        )
        self.button_view_setting_simple.switch_on()
        self.button_view_setting_simple.pack(side="top")
        self.button_view_setting_simple_tooltip = CTkToolTip(
            self.button_view_setting_simple,
            delay=TOOLTIP_DELAY,
            message=TOOLTIP["view_setting"],
        )

        # function buttons
        # edit
        self.button_edit_frame = CTkFrame(self, fg_color="transparent")
        self.button_edit_frame.grid(
            row=3, column=1, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_edit = STkButton(
            self.button_edit_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.edit_image,
            text="",
            font=self.info_font,
            command=lambda: self.edit_mode_switch(),
            mode=EditMode.OFF,
        )
        self.button_edit.pack(side="top")
        self.button_edit_label = CTkLabel(
            self.button_edit_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Edit",
            font=self.info_font,
        )
        self.button_edit_label.pack(side="bottom")
        self.button_edit.label = self.button_edit_label
        self.button_edit_tooltip = CTkToolTip(
            self.button_edit, delay=TOOLTIP_DELAY, message=TOOLTIP["edit"]
        )

        # save
        self.button_save_frame = CTkFrame(self, fg_color="transparent")
        self.button_save_frame.grid(
            row=3, column=2, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_save = STkButton(
            self.button_save_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.save_image,
            text="",
            font=self.info_font,
            command=lambda: self.save_data(),
        )
        self.button_save.grid(row=0, column=0)
        self.button_save_option = CTkOptionMenu(
            self.button_save_frame,
            font=self.info_font,
            dynamic_resizing=False,
            values=["select directory", "overwrite the original image"],
            command=self.save_data,
        )
        self.button_save_option_arrow = STkButton(
            self.button_save_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(self.button_save, self.button_save_option),
        )
        self.button_save_option_arrow.grid(row=0, column=1)
        self.button_save_label = CTkLabel(
            self.button_save_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Save",
            font=self.info_font,
        )
        self.button_save_label.grid(row=1, column=0, rowspan=2)
        self.button_save.label = self.button_save_label
        self.button_save.arrow = self.button_save_option_arrow
        self.button_save_tooltip = CTkToolTip(
            self.button_save, delay=TOOLTIP_DELAY, message=TOOLTIP["save"]
        )

        # remove
        self.button_remove_frame = CTkFrame(self, fg_color="transparent")
        self.button_remove_frame.grid(
            row=3, column=3, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_remove = STkButton(
            self.button_remove_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.clear_image,
            text="",
            font=self.info_font,
            command=lambda: self.remove_data(),
        )
        self.button_remove.grid(row=0, column=0)
        self.button_remove_option = CTkOptionMenu(
            self.button_remove_frame,
            font=self.info_font,
            dynamic_resizing=False,
            values=["select directory", "overwrite the original image"],
            command=self.remove_data,
        )
        self.button_remove_option_arrow = STkButton(
            self.button_remove_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(
                self.button_remove, self.button_remove_option
            ),
        )
        self.button_remove_option_arrow.grid(row=0, column=1)
        self.button_remove_label = CTkLabel(
            self.button_remove_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Clear",
            font=self.info_font,
        )
        self.button_remove_label.grid(row=1, column=0, rowspan=2)
        self.button_remove.label = self.button_remove_label
        self.button_remove.arrow = self.button_remove_option_arrow
        self.button_remove_tooltip = CTkToolTip(
            self.button_remove, delay=TOOLTIP_DELAY, message=TOOLTIP["clear"]
        )

        # export
        self.button_export_frame = CTkFrame(self, fg_color="transparent")
        self.button_export_frame.grid(
            row=3, column=4, pady=(0, 20), padx=(0, 20), sticky="w"
        )
        self.button_export = STkButton(
            self.button_export_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.document_image,
            text="",
            font=self.info_font,
            command=lambda: self.export_txt(),
        )
        self.button_export.grid(row=0, column=0)
        self.button_export_option = CTkOptionMenu(
            self,
            font=self.info_font,
            dynamic_resizing=False,
            values=["select directory"],
            command=self.export_txt,
        )
        self.button_export_option_arrow = STkButton(
            self.button_export_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(
                self.button_export, self.button_export_option
            ),
        )
        self.button_export_option_arrow.grid(row=0, column=1)
        self.button_export_label = CTkLabel(
            self.button_export_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Export",
            font=self.info_font,
        )
        self.button_export_label.grid(row=1, column=0, rowspan=2)
        self.button_export.label = self.button_export_label
        self.button_export.arrow = self.button_export_option_arrow
        self.button_export_tooltip = CTkToolTip(
            self.button_export, delay=TOOLTIP_DELAY, message=TOOLTIP["export"]
        )

        # copy
        self.button_copy_raw_frame = CTkFrame(self, fg_color="transparent")
        self.button_copy_raw_frame.grid(row=3, column=5, pady=(0, 20), sticky="w")
        self.button_raw = STkButton(
            self.button_copy_raw_frame,
            width=BUTTON_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            image=self.clipboard_image,
            text="",
            font=self.info_font,
            command=lambda: self.copy_to_clipboard(self.image_data.raw),
        )
        self.button_raw.grid(row=0, column=0)
        self.button_raw_option = CTkOptionMenu(
            self,
            font=self.info_font,
            dynamic_resizing=False,
            values=["single line prompt"],
            command=self.copy_raw,
        )
        self.button_raw_option_arrow = STkButton(
            self.button_copy_raw_frame,
            width=ARROW_WIDTH_L,
            height=BUTTON_HEIGHT_L,
            text="",
            image=self.expand_image,
            command=lambda: self.option_open(self.button_raw, self.button_raw_option),
        )
        self.button_raw_option_arrow.grid(row=0, column=1)
        self.button_raw_label = CTkLabel(
            self.button_copy_raw_frame,
            width=BUTTON_WIDTH_L,
            height=LABEL_HEIGHT,
            text="Copy",
            font=self.info_font,
        )
        self.button_raw_label.grid(row=1, column=0, rowspan=2)
        self.button_raw.label = self.button_raw_label
        self.button_raw.arrow = self.button_raw_option_arrow
        self.button_raw_tooltip = CTkToolTip(
            self.button_raw, delay=TOOLTIP_DELAY, message=TOOLTIP["copy_raw"]
        )

        # text boxes and buttons
        self.boxes = [self.positive_box, self.negative_box, self.setting_box]

        # general button list
        self.function_buttons = [
            self.button_copy_setting,
            self.button_view_setting,
            self.button_copy_setting_simple,
            self.button_raw,
            self.button_remove,
            self.button_export,
            self.button_remove,
        ]

        # button list for edit mode
        self.non_edit_buttons = [
            self.button_view_setting,
            self.button_export,
            self.button_raw,
        ]

        self.edit_buttons = [
            self.button_copy_setting,
            self.button_remove,
            self.button_edit,
        ]

        for button in self.function_buttons:
            button.disable()
        self.positive_box.all_off()
        self.negative_box.all_off()
        self.button_save.disable()
        self.button_edit.disable()
        self.file_path = None

        # bind dnd and resize
        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self.display_info)
        self.bind("<Configure>", self.resize_image)
        self.bind_all("<Left>", self.on_prev_image_key, add="+")
        self.bind_all("<Right>", self.on_next_image_key, add="+")
        self.update_image_navigation_state()
        self._start_image_loader()

        # update checker
        self.update_checker = UpdateChecker(self.status_bar)

        # open with in windows
        if len(sys.argv) > 1:
            self.display_info(sys.argv[1], is_selected=True)
        # open with in macOS
        self.createcommand("::tk::mac::OpenDocument", self.open_document_handler)

    def open_document_handler(self, *args):
        self.display_info(args[0], is_selected=True)

    def display_info(self, event, is_selected=False):
        self.status_bar.unbind()
        # stop update thread when reading first image
        self.update_checker.close_thread()
        # selected or drag and drop
        if is_selected:
            if event == "":
                return
            new_path = Path(event)
        else:
            new_path = Path(event.data.replace("}", "").replace("{", ""))

        # detect suffix and read
        if new_path.suffix.lower() in SUPPORTED_FORMATS:
            self.file_path = new_path
            self.refresh_image_sequence(self.file_path)
            self._prepare_loading_state()
            self._request_image_load(self.file_path)
            return

        # txt importing
        elif new_path.suffix == ".txt":
            if self.button_edit.mode == EditMode.ON:
                with open(new_path, "r") as f:
                    txt_data = ImageDataReader(f, is_txt=True)
                    if txt_data.raw:
                        self.positive_box.text = txt_data.positive
                        self.negative_box.text = txt_data.negative
                        self.setting_box.text = txt_data.setting
                        self.edit_mode_update()
                        self.status_bar.warning(MESSAGE["txt_imported"][0])
                    else:
                        self.status_bar.warning(MESSAGE["txt_error"][-1])
            else:
                self.status_bar.warning(MESSAGE["txt_error"][0])

        else:
            self.unsupported_format(MESSAGE["suffix_error"], True)
            if self.button_edit.mode == EditMode.ON:
                for box in self.boxes:
                    box.edit_off()
            self.button_edit.disable()

    def unsupported_format(self, message, reset_image=False, url="", raw=False):
        self.readable = False
        self.setting_box.text = ""
        self.positive_box.display("")
        self.negative_box.display("")
        self.setting_box_parameter.reset_text()
        for button in self.function_buttons:
            button.disable()
        self.positive_box.all_off()
        self.negative_box.all_off()
        if reset_image:
            self.image_label.configure(image=self.drop_image, text=MESSAGE["drop"][0])
            self.image = None
            self.clear_image_sequence()
        else:
            self.button_edit.enable()
        self.status_bar.warning(message[-1])
        if url:
            self.status_bar.link(url)
        if raw:
            self.button_raw.enable()
            self.button_export.enable()

    def resize_image(self, event=None):
        # resize image to window size
        if self.image:
            aspect_ratio = self.image.size[0] / self.image.size[1]
            # fix windows huge image problem under hidpi
            self.scaling = ScalingTracker.get_window_dpi_scaling(self)

            label_w_px = (
                self.image_label.winfo_width() if self.image_label.winfo_width() > 2 else 560
            )
            label_h_px = (
                self.image_label.winfo_height() if self.image_label.winfo_height() > 2 else 560
            )
            available_w_px = max(1, label_w_px - 5)
            available_h_px = max(1, label_h_px)

            if available_w_px / available_h_px > aspect_ratio:
                target_h_px = available_h_px
                target_w_px = int(target_h_px * aspect_ratio)
            else:
                target_w_px = available_w_px
                target_h_px = int(target_w_px / aspect_ratio)

            target_w = max(1, int(target_w_px / self.scaling))
            target_h = max(1, int(target_h_px / self.scaling))
            target_w_px = max(1, int(target_w * self.scaling))
            target_h_px = max(1, int(target_h * self.scaling))

            resized = self.image.resize(
                (target_w_px, target_h_px), Image.Resampling.LANCZOS
            ).convert("RGBA")
            self._draw_nav_overlay(resized, label_w_px, label_h_px, target_w_px, target_h_px)

            self.image_tk = CTkImage(resized, size=(target_w, target_h))
            self.image_label.configure(image=self.image_tk, text="")
        else:
            self._nav_prev_bbox = None
            self._nav_next_bbox = None

    def _prepare_loading_state(self):
        self.readable = False
        if self._metadata_after_id is not None:
            try:
                self.after_cancel(self._metadata_after_id)
            except Exception:
                pass
            self._metadata_after_id = None
        for button in self.function_buttons:
            button.disable()
        self.positive_box.all_off()
        self.negative_box.all_off()
        self.button_save.disable()
        self.button_edit.disable()
        self.status_bar.info("Loading...")

    @staticmethod
    def _normalize_path_key(path: Path):
        return os.path.normcase(os.path.abspath(str(path)))

    def refresh_image_sequence(self, current_path: Path):
        directory = current_path.parent
        directory_key = self._normalize_path_key(directory)
        current_key = self._normalize_path_key(current_path)

        if directory_key != self._image_sequence_dir_key:
            self._image_sequence_dir_key = directory_key
            self._image_sequence = []
            self._image_sequence_index_by_key = {}
            self._image_sequence_index = None
            self.update_image_navigation_state()
            self._start_image_sequence_scan(directory)
            return

        # Do not refresh/re-scan the folder list while paging; just update the index if known.
        self._image_sequence_index = self._image_sequence_index_by_key.get(current_key)
        self.update_image_navigation_state()

    def _start_image_sequence_scan(self, directory: Path):
        self._image_sequence_scan_id += 1
        scan_id = self._image_sequence_scan_id
        self._image_sequence_scanning = True

        def worker():
            candidates = []
            index_by_key = {}
            try:
                for entry in os.scandir(directory):
                    if not entry.is_file():
                        continue
                    suffix = os.path.splitext(entry.name)[1].lower()
                    if suffix in SUPPORTED_FORMATS:
                        candidates.append(Path(entry.path))
                candidates.sort(key=lambda p: p.name.casefold())
                index_by_key = {
                    self._normalize_path_key(p): i for i, p in enumerate(candidates)
                }
            except Exception:
                candidates = []
                index_by_key = {}

            self.after(
                0,
                lambda: self._finish_image_sequence_scan(
                    scan_id, directory, candidates, index_by_key
                ),
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_image_sequence_scan(
        self, scan_id: int, directory: Path, candidates: list, index_by_key: dict
    ):
        if scan_id != self._image_sequence_scan_id:
            return

        self._image_sequence_scanning = False
        if self._normalize_path_key(directory) != self._image_sequence_dir_key:
            return

        self._image_sequence = candidates
        self._image_sequence_index_by_key = index_by_key
        if self.file_path is not None:
            current_key = self._normalize_path_key(self.file_path)
            self._image_sequence_index = self._image_sequence_index_by_key.get(
                current_key
            )
        else:
            self._image_sequence_index = None
        self.update_image_navigation_state()

    def clear_image_sequence(self):
        self._image_sequence = []
        self._image_sequence_index = None
        self._image_sequence_index_by_key = {}
        self._image_sequence_dir_key = None
        self._image_sequence_scanning = False
        self.update_image_navigation_state()

    def _invalidate_image_cache(self, path: Path):
        key = self._normalize_path_key(path)
        self._image_cache.pop(key, None)

    def _cache_put(self, path: Path, pil_image: Image.Image, image_data: ImageDataReader):
        key = self._normalize_path_key(path)
        self._image_cache[key] = (pil_image, image_data)
        self._image_cache.move_to_end(key)
        while len(self._image_cache) > self._image_cache_max:
            self._image_cache.popitem(last=False)

    def _cache_get(self, path: Path):
        key = self._normalize_path_key(path)
        if key not in self._image_cache:
            return None
        value = self._image_cache[key]
        self._image_cache.move_to_end(key)
        return value

    def _start_image_loader(self):
        def loader_loop():
            while True:
                self._image_load_event.wait()
                self._image_load_event.clear()
                with self._image_load_lock:
                    requested_path = self._image_load_requested_path
                    requested_max_dim = self._image_load_requested_max_dim
                    request_id = self._image_load_request_id

                if requested_path is None:
                    continue

                cached = self._cache_get(requested_path)
                if cached is not None:
                    pil_image, image_data = cached
                    self.after(
                        0,
                        lambda: self._apply_loaded_image(
                            request_id, requested_path, pil_image, image_data
                        ),
                    )
                    continue

                pil_image = None
                image_data = None
                load_error = None

                try:
                    image_data = ImageDataReader(str(requested_path))
                    with Image.open(requested_path) as img:
                        if requested_max_dim is not None:
                            try:
                                img.draft("RGB", (requested_max_dim, requested_max_dim))
                            except Exception:
                                pass
                        img.load()
                        if requested_max_dim is not None:
                            img.thumbnail(
                                (requested_max_dim, requested_max_dim),
                                Image.Resampling.LANCZOS,
                            )
                        pil_image = img.copy()
                except Exception as e:
                    load_error = e

                self.after(
                    0,
                    lambda: self._apply_loaded_image(
                        request_id,
                        requested_path,
                        pil_image,
                        image_data,
                        load_error=load_error,
                    ),
                )

        threading.Thread(target=loader_loop, daemon=True).start()

    def _request_image_load(self, image_path: Path):
        max_dim = max(self.image_label.winfo_width(), self.image_frame.winfo_height())
        if max_dim <= 2:
            max_dim = 1200
        else:
            max_dim = max(800, int(max_dim * 2))
        with self._image_load_lock:
            self._image_load_request_id += 1
            self._image_load_requested_path = image_path
            self._image_load_requested_max_dim = max_dim
            request_id = self._image_load_request_id
        self._image_load_event.set()
        return request_id

    def _apply_loaded_image(
        self,
        request_id: int,
        image_path: Path,
        pil_image: Image.Image,
        image_data: ImageDataReader,
        load_error=None,
    ):
        with self._image_load_lock:
            if request_id != self._image_load_request_id:
                return

        if self.file_path is None or self._normalize_path_key(self.file_path) != self._normalize_path_key(image_path):
            return

        if load_error is not None or pil_image is None or image_data is None:
            self.unsupported_format([None, "Failed to load image"], reset_image=True)
            return

        self.image = pil_image
        self.resize_image()

        self.image_data = image_data
        self._cache_put(image_path, pil_image, image_data)

        self.update_image_navigation_state()
        self._schedule_metadata_apply(request_id, image_path)

        # Best-effort prefetch neighbors to make next/prev smoother.
        self._prefetch_neighbors(image_path)

    def _schedule_metadata_apply(self, request_id: int, image_path: Path):
        if self._metadata_after_id is not None:
            try:
                self.after_cancel(self._metadata_after_id)
            except Exception:
                pass
            self._metadata_after_id = None

        # Avoid stutter when rapidly paging; apply metadata only after a short pause.
        self._metadata_after_id = self.after(
            180, lambda: self._apply_loaded_metadata(request_id, image_path)
        )

    def _apply_loaded_metadata(self, request_id: int, image_path: Path):
        self._metadata_after_id = None
        with self._image_load_lock:
            if request_id != self._image_load_request_id:
                return

        if self.file_path is None or self._normalize_path_key(self.file_path) != self._normalize_path_key(image_path):
            return

        if not self.image_data or not self.image_data.tool or self.image_data.status.name == "FORMAT_ERROR":
            self.unsupported_format(MESSAGE["format_error"])
            return

        if self.image_data.status.name == "COMFYUI_ERROR":
            self.unsupported_format(MESSAGE["comfyui_error"], url=URL["comfyui"], raw=True)
            return

        self.readable = True
        if not self.image_data.is_sdxl:
            self.positive_box.display(self.image_data.positive)
            self.negative_box.display(self.image_data.negative)
        else:
            self.positive_box.display(self.image_data.positive_sdxl)
            self.negative_box.display(self.image_data.negative_sdxl)

        self.setting_box.text = self.image_data.setting
        self.setting_box_parameter.update_text(self.image_data.parameter)
        self.positive_box.mode_update()
        self.negative_box.mode_update()

        if self.button_edit.mode == EditMode.OFF:
            for button in self.function_buttons:
                button.enable()
            self.positive_box.all_on()
            self.negative_box.all_on()

        for button in self.edit_buttons:
            button.enable()
        self.positive_box.copy_on()
        self.negative_box.copy_on()

        if self.image_data.tool != "A1111 webUI":
            self.button_raw_option_arrow.disable()
        if self.image_data.is_sdxl:
            self.button_edit.disable()

        self.status_bar.success(self.image_data.tool)

        if self.button_edit.mode == EditMode.ON:
            self.edit_mode_update()

    def _prefetch_neighbors(self, image_path: Path):
        if self._image_sequence_index is None or not self._image_sequence:
            return

        indices = [
            self._image_sequence_index - 1,
            self._image_sequence_index + 1,
        ]
        paths = [
            self._image_sequence[i]
            for i in indices
            if 0 <= i < len(self._image_sequence)
        ]
        if not paths:
            return

        max_dim = self._image_load_requested_max_dim
        if max_dim is None:
            max_dim = 1200

        def worker():
            for p in paths:
                if self._cache_get(p) is not None:
                    continue
                try:
                    data = ImageDataReader(str(p))
                    with Image.open(p) as img:
                        try:
                            img.draft("RGB", (max_dim, max_dim))
                        except Exception:
                            pass
                        img.load()
                        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                        pil = img.copy()
                except Exception:
                    continue

                self.after(0, lambda _p=p, _pil=pil, _data=data: self._cache_put(_p, _pil, _data))

        threading.Thread(target=worker, daemon=True).start()

    def update_image_navigation_state(self):
        has_prev = bool(self._image_sequence_index is not None and self._image_sequence_index > 0)
        has_next = bool(
            self._image_sequence_index is not None
            and self._image_sequence_index < len(self._image_sequence) - 1
        )
        if has_prev != self._nav_prev_enabled or has_next != self._nav_next_enabled:
            self._nav_prev_enabled = has_prev
            self._nav_next_enabled = has_next
            if self.image:
                self.resize_image()

    def _navigation_key_should_trigger(self):
        focused = self.focus_get()
        if self.button_edit.mode == EditMode.ON and focused is not None:
            try:
                widget_class = focused.winfo_class()
            except Exception:
                widget_class = ""
            if widget_class in ("Text", "Entry", "TEntry", "Spinbox"):
                return False
        return True

    def on_prev_image_key(self, event=None):
        if self._navigation_key_should_trigger():
            self.navigate_image(-1)

    def on_next_image_key(self, event=None):
        if self._navigation_key_should_trigger():
            self.navigate_image(1)

    def navigate_image(self, delta: int):
        if self._image_sequence_index is None:
            return
        new_index = self._image_sequence_index + delta
        if new_index < 0 or new_index >= len(self._image_sequence):
            return
        self.display_info(str(self._image_sequence[new_index]), is_selected=True)

    def on_image_click(self, event):
        if self.image is None:
            self.display_info(self.select_image(), is_selected=True)
            return

        if (
            self._nav_prev_enabled
            and self._nav_prev_bbox
            and self._point_in_bbox(event.x, event.y, self._nav_prev_bbox)
        ):
            self.navigate_image(-1)
            return

        if (
            self._nav_next_enabled
            and self._nav_next_bbox
            and self._point_in_bbox(event.x, event.y, self._nav_next_bbox)
        ):
            self.navigate_image(1)
            return

        self.display_info(self.select_image(), is_selected=True)

    def on_image_motion(self, event):
        is_nav = False
        if (
            self._nav_prev_enabled
            and self._nav_prev_bbox
            and self._point_in_bbox(event.x, event.y, self._nav_prev_bbox)
        ):
            is_nav = True
        elif (
            self._nav_next_enabled
            and self._nav_next_bbox
            and self._point_in_bbox(event.x, event.y, self._nav_next_bbox)
        ):
            is_nav = True
        self.image_label.configure(cursor="hand2" if is_nav else "")

    def on_image_leave(self, event):
        self.image_label.configure(cursor="")

    @staticmethod
    def _point_in_bbox(x: int, y: int, bbox):
        x0, y0, x1, y1 = bbox
        return x0 <= x <= x1 and y0 <= y <= y1

    def _draw_nav_overlay(
        self,
        image_rgba: Image.Image,
        label_w_px: int,
        label_h_px: int,
        image_w_px: int,
        image_h_px: int,
    ):
        self._nav_prev_bbox = None
        self._nav_next_bbox = None

        icon_size_px = min(60, max(34, int(min(image_w_px, image_h_px) * 0.085)))
        margin_px = min(32, max(14, int(icon_size_px * 0.35)))

        offset_x = int((label_w_px - image_w_px) / 2)
        offset_y = int((label_h_px - image_h_px) / 2)
        y = offset_y + int((image_h_px - icon_size_px) / 2)

        x_prev = offset_x + margin_px
        x_next = offset_x + image_w_px - margin_px - icon_size_px

        y_img = max(0, int((image_h_px - icon_size_px) / 2))
        x_prev_img = max(0, margin_px)
        x_next_img = max(0, image_w_px - margin_px - icon_size_px)

        prev_icon = self._render_svg_nav_icon(
            "prev", icon_size_px, enabled=self._nav_prev_enabled
        )
        next_icon = self._render_svg_nav_icon(
            "next", icon_size_px, enabled=self._nav_next_enabled
        )

        image_rgba.alpha_composite(prev_icon, dest=(x_prev_img, y_img))
        image_rgba.alpha_composite(next_icon, dest=(x_next_img, y_img))

        self._nav_prev_bbox = (
            x_prev,
            y,
            x_prev + icon_size_px,
            y + icon_size_px,
        )
        self._nav_next_bbox = (
            x_next,
            y,
            x_next + icon_size_px,
            y + icon_size_px,
        )

    def _render_svg_nav_icon(self, direction: str, size_px: int, enabled: bool):
        key = (direction, size_px, enabled)
        cached = self._nav_icon_cache.get(key)
        if cached is not None:
            return cached

        svg_path = self._nav_prev_svg if direction == "prev" else self._nav_next_svg
        render_scale = 4
        render_size = max(24, size_px * render_scale)

        try:
            root = ET.parse(svg_path).getroot()
        except Exception:
            img = Image.new("RGBA", (size_px, size_px), (0, 0, 0, 0))
            self._nav_icon_cache[key] = img
            return img

        view_box = root.attrib.get("viewBox", "0 0 24 24").strip().split()
        vb_w = float(view_box[2]) if len(view_box) == 4 else 24.0
        vb_h = float(view_box[3]) if len(view_box) == 4 else 24.0
        scale = render_size / max(vb_w, vb_h)

        img = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        alpha = 235 if enabled else 90
        shadow_alpha = 150 if enabled else 55
        stroke = (255, 255, 255, alpha)
        shadow = (0, 0, 0, shadow_alpha)
        stroke_width = max(2, int(2.2 * render_scale))
        shadow_offset = max(1, int(1.2 * render_scale))

        circles = []
        polygons = []
        for el in root.iter():
            tag = el.tag.split("}")[-1]
            if tag == "circle":
                try:
                    circles.append(
                        (
                            float(el.attrib.get("cx")),
                            float(el.attrib.get("cy")),
                            float(el.attrib.get("r")),
                        )
                    )
                except Exception:
                    continue
            elif tag == "polygon":
                pts_raw = el.attrib.get("points", "").strip()
                if not pts_raw:
                    continue
                parts = pts_raw.replace(",", " ").split()
                if len(parts) % 2 != 0:
                    continue
                coords = []
                try:
                    for i in range(0, len(parts), 2):
                        coords.append((float(parts[i]), float(parts[i + 1])))
                    polygons.append(coords)
                except Exception:
                    continue

        def draw_circle(cx, cy, r, color, offset=0):
            x0 = (cx - r) * scale + offset
            y0 = (cy - r) * scale + offset
            x1 = (cx + r) * scale + offset
            y1 = (cy + r) * scale + offset
            draw.ellipse((x0, y0, x1, y1), outline=color, width=stroke_width)

        def draw_polygon(points, color, offset=0):
            pts = [(x * scale + offset, y * scale + offset) for x, y in points]
            draw.polygon(pts, fill=color)

        for cx, cy, r in circles:
            draw_circle(cx, cy, r, shadow, offset=shadow_offset)
        for pts in polygons:
            draw_polygon(pts, shadow, offset=shadow_offset)
        for cx, cy, r in circles:
            draw_circle(cx, cy, r, stroke, offset=0)
        for pts in polygons:
            draw_polygon(pts, stroke, offset=0)

        img = img.resize((size_px, size_px), Image.Resampling.LANCZOS)
        self._nav_icon_cache[key] = img
        return img

    def copy_to_clipboard(self, content):
        try:
            pyperclip.copy(content)
        except:
            print("Copy error")
        else:
            self.status_bar.clipboard()

    # alt option menu button trigger for CTkOptionMenu
    @staticmethod
    def option_open(button: CTkButton, option_menu: CTkOptionMenu):
        option_menu._dropdown_menu.open(
            button.winfo_rootx(),
            button.winfo_rooty()
            + button._apply_widget_scaling(button._current_height + 0),
        )

    def export_txt(self, export_mode: str = None):
        if not export_mode:
            with open(self.file_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
                f.write(self.image_data.raw)
                self.status_bar.success(MESSAGE["alongside"][0])
        else:
            match export_mode:
                case "select directory":
                    path = filedialog.asksaveasfilename(
                        title="Select directory",
                        initialdir=self.file_path.parent,
                        initialfile=self.file_path.stem,
                        filetypes=(("text file", "*.txt"),),
                    )
                    if path:
                        with open(
                            Path(path).with_suffix(".txt"), "w", encoding="utf-8"
                        ) as f:
                            f.write(self.image_data.raw)
                            self.status_bar.success(MESSAGE["txt_select"][0])

    def remove_data(self, remove_mode: str = None):
        image_without_exif = self.image_data.remove_data(self.file_path)
        new_stem = self.file_path.stem + "_data_removed"
        new_path = self.file_path.with_stem(new_stem)
        if not remove_mode:
            try:
                self.image_data.save_image(
                    self.file_path, new_path, self.image_data.format
                )
            except:
                print("Remove error")
            else:
                self.status_bar.success(MESSAGE["suffix"][0])
        else:
            match remove_mode:
                # case "add suffix":
                #
                case "overwrite the original image":
                    try:
                        self.image_data.save_image(
                            self.file_path, self.file_path, self.image_data.format
                        )
                    except:
                        print("Remove error")
                    else:
                        self.status_bar.success(MESSAGE["overwrite"][0])
                case "select directory":
                    path = filedialog.asksaveasfilename(
                        title="Select directory",
                        initialdir=self.file_path.parent,
                        initialfile=new_path.name,
                    )
                    if path:
                        try:
                            self.image_data.save_image(
                                self.file_path, path, self.image_data.format
                            )
                        except:
                            print("Remove error")
                        else:
                            self.status_bar.success(MESSAGE["remove_select"][0])

    def save_data(self, save_mode: str = None):
        with Image.open(self.file_path) as image:
            new_stem = self.file_path.stem + "_edited"
            new_path = self.file_path.with_stem(new_stem)
            data = (
                self.positive_box.text
                + "Negative prompt: "
                + self.negative_box.text
                + self.setting_box.ctext
            )
            if not save_mode:
                try:
                    self.image_data.save_image(
                        self.file_path, new_path, self.image_data.format, data
                    )
                except:
                    print("Save error")
                else:
                    self.status_bar.success(MESSAGE["suffix"][0])
            else:
                match save_mode:
                    case "overwrite the original image":
                        try:
                            self.image_data.save_image(
                                self.file_path,
                                self.file_path,
                                self.image_data.format,
                                data,
                            )
                        except:
                            print("Save error")
                        else:
                            self.status_bar.success(MESSAGE["overwrite"][0])
                    case "select directory":
                        path = filedialog.asksaveasfilename(
                            title="Select directory",
                            initialdir=self.file_path.parent,
                            initialfile=new_path.name,
                        )
                        if path:
                            try:
                                self.image_data.save_image(
                                    self.file_path, path, self.image_data.format, data
                                )
                            except:
                                print("Save error")
                            else:
                                self.status_bar.success(MESSAGE["remove_select"][0])

    def copy_raw(self, copy_mode: str = None):
        match copy_mode:
            case "single line prompt":
                self.copy_to_clipboard(self.image_data.prompt_to_line())

    def edit_mode_switch(self):
        match self.button_edit.mode:
            case EditMode.OFF:
                self.button_edit.mode = EditMode.ON
                self.button_edit.image = self.edit_off_image
                self.button_edit.switch_on()
                self.positive_box.edit_on()
                self.negative_box.edit_on()
                self.setting_box.edit_on()
                if self.button_view_setting.mode == SettingMode.SIMPLE:
                    self.setting_mode_switch()
                for button in self.non_edit_buttons:
                    button.disable()
                self.button_save.enable()
                self.status_bar.info(MESSAGE["edit"][0])
            case EditMode.ON:
                self.button_edit.mode = EditMode.OFF
                self.button_edit.image = self.edit_image
                self.button_edit.switch_off()
                self.positive_box.edit_off()
                self.negative_box.edit_off()
                self.setting_box.edit_off()
                if self.readable:
                    for button in self.non_edit_buttons:
                        button.enable()
                self.button_save.disable()
                self.status_bar.info(MESSAGE["edit"][-1])

    def edit_mode_update(self):
        match self.button_edit.mode:
            case EditMode.OFF:
                self.positive_box.edit_off()
                self.negative_box.edit_off()
                self.setting_box.edit_off()
                if self.readable:
                    for button in self.non_edit_buttons:
                        button.enable()
                self.button_save.disable()
            case EditMode.ON:
                self.positive_box.edit_on()
                self.negative_box.edit_on()
                self.setting_box.edit_on()
                for button in self.non_edit_buttons:
                    button.disable()
                self.button_save.enable()

    def setting_mode_switch(self):
        match self.button_view_setting.mode:
            case SettingMode.NORMAL:
                self.button_view_setting.mode = SettingMode.SIMPLE
                self.setting_box_simple.grid(
                    row=2,
                    column=1,
                    columnspan=6,
                    sticky="news",
                    padx=(0, 20),
                    pady=(1, 21),
                )
                self.setting_box.grid_forget()
                self.status_bar.info(MESSAGE["view_setting"][0])
            case SettingMode.SIMPLE:
                self.button_view_setting.mode = SettingMode.NORMAL
                self.setting_box.grid(
                    row=2,
                    column=1,
                    columnspan=6,
                    sticky="news",
                    padx=(0, 20),
                    pady=(1, 21),
                )
                self.setting_box_simple.grid_forget()
                self.status_bar.info(MESSAGE["view_setting"][-1])

    @staticmethod
    def mode_update(button: STkButton, textbox: STkTextbox, sort_button: STkButton):
        match button.mode:
            case ViewMode.NORMAL:
                match sort_button.mode:
                    case SortMode.ASC:
                        textbox.sort_asc()
                    case SortMode.DES:
                        textbox.sort_des()
            case ViewMode.VERTICAL:
                textbox.view_vertical()
                match sort_button.mode:
                    case SortMode.ASC:
                        textbox.sort_asc()
                    case SortMode.DES:
                        textbox.sort_des()

    def select_image(self):
        initialdir = self.file_path.parent if self.file_path else "/"
        return filedialog.askopenfilename(
            title="Select your image file",
            initialdir=initialdir,
            filetypes=(("image files", "*.png *.jpg *jpeg *.webp"),),
        )

    @staticmethod
    def load_icon(icon_file, size):
        return (
            CTkImage(Image.open(icon_file[0]), size=size),
            CTkImage(Image.open(icon_file[1]), size=size),
        )


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
