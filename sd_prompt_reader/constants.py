__author__ = "receyuki"
__filename__ = "constants.py"
__copyright__ = "Copyright 2023"
__email__ = "receyuki@gmail.com"

from importlib import resources
from pathlib import Path
from . import resources as res

RESOURCE_DIR = str(resources.files(res))
SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".webp"]
COLOR_THEME = Path(RESOURCE_DIR, "gray.json")
INFO_FILE = Path(RESOURCE_DIR, "info_24.png")
ERROR_FILE = Path(RESOURCE_DIR, "error_24.png")
WARNING_FILE = Path(RESOURCE_DIR, "warning_24.png")
OK_FILE = Path(RESOURCE_DIR, "check_circle_24.png")
UPDATE_FILE = Path(RESOURCE_DIR, "update_24.png")
DROP_FILE = Path(RESOURCE_DIR, "place_item_48.png")
REVEAL_FILE = (
    Path(RESOURCE_DIR, "place_item_48.png"),
    Path(RESOURCE_DIR, "place_item_48_alpha.png"),
)
COPY_FILE_L = (
    Path(RESOURCE_DIR, "content_copy_24.png"),
    Path(RESOURCE_DIR, "content_copy_24_alpha.png"),
)
COPY_FILE_S = (
    Path(RESOURCE_DIR, "content_copy_20.png"),
    Path(RESOURCE_DIR, "content_copy_20_alpha.png"),
)
CLEAR_FILE = (Path(RESOURCE_DIR, "mop_24.png"), Path(RESOURCE_DIR, "mop_24_alpha.png"))
DOCUMENT_FILE = (
    Path(RESOURCE_DIR, "description_24.png"),
    Path(RESOURCE_DIR, "description_24_alpha.png"),
)
EXPAND_FILE = (
    Path(RESOURCE_DIR, "expand_more_24.png"),
    Path(RESOURCE_DIR, "expand_more_24_alpha.png"),
)
EDIT_FILE = (Path(RESOURCE_DIR, "edit_24.png"), Path(RESOURCE_DIR, "edit_24_alpha.png"))
EDIT_OFF_FILE = (
    Path(RESOURCE_DIR, "edit_off_24.png"),
    Path(RESOURCE_DIR, "edit_off_24_alpha.png"),
)
LIGHTBULB_FILE = (
    Path(RESOURCE_DIR, "lightbulb_20.png"),
    Path(RESOURCE_DIR, "lightbulb_20_alpha.png"),
)
SAVE_FILE = (Path(RESOURCE_DIR, "save_24.png"), Path(RESOURCE_DIR, "save_24_alpha.png"))
SORT_FILE = (
    Path(RESOURCE_DIR, "sort_by_alpha_20.png"),
    Path(RESOURCE_DIR, "sort_by_alpha_20_alpha.png"),
)
VIEW_SEPARATE_FILE = (
    Path(RESOURCE_DIR, "view_week_20.png"),
    Path(RESOURCE_DIR, "view_week_20_alpha.png"),
)
VIEW_TAB_FILE = (
    Path(RESOURCE_DIR, "view_sidebar_20.png"),
    Path(RESOURCE_DIR, "view_sidebar_20_alpha.png"),
)
ICON_FILE = Path(RESOURCE_DIR, "icon.png")
ICON_CUBE_FILE = Path(RESOURCE_DIR, "icon-cube.png")
ICO_FILE = Path(RESOURCE_DIR, "icon-gui.ico")
MESSAGE = {
    "drop": ["把图片拖到这里，或点击选择"],
    "default": ["将图片文件拖入窗口"],
    "success": ["完成"],
    "format_error": ["", "未检测到数据或格式不支持"],
    "suffix_error": ["不支持的格式"],
    "clipboard": ["已复制到剪贴板"],
    "update": ["发现新版本，点击这里下载"],
    "export": ["已生成 TXT 文件"],
    "alongside": ["TXT 已生成并保存在图片同目录"],
    "txt_select": ["TXT 已生成到所选位置"],
    "workflow_select": ["工作流 JSON 已导出到所选位置"],
    "prompt_select": ["Prompt JSON 已导出到所选位置"],
    "workflow_missing": ["图片中未包含工作流元数据"],
    "prompt_missing": ["图片中未包含 prompt 元数据"],
    "reveal": ["已在文件管理器中打开"],
    "reveal_error": ["打开失败"],
    "remove": ["已生成新图片文件"],
    "suffix": ["已生成带后缀的新图片文件"],
    "overwrite": ["已覆盖原始图片文件"],
    "no_overwrite": ["为保护原图：禁止覆盖，请另存为到新文件"],
    "remove_select": ["已在所选位置生成新图片文件"],
    "txt_error": [
        "仅在编辑模式下允许导入 TXT 文件",
        "不支持的 TXT 格式",
    ],
    "txt_imported": ["TXT 导入成功"],
    "edit": ["编辑模式", "查看模式"],
    "sort": ["升序", "降序", "原始顺序"],
    "img_sort": ["图片排序：按文件名", "图片排序：按修改时间（最新优先）"],
    "img_sort_btn": ["图片：文件名", "图片：时间"],
    "view_prompt": ["竖排显示", "横排显示"],
    "view_setting": ["简洁模式", "普通模式"],
    "comfyui_error": [
        "ComfyUI 工作流过于复杂，或使用了不支持的自定义节点",
        "解析 ComfyUI 数据失败，点击查看详情",
    ],
}
TOOLTIP = {
    "edit": "编辑图片元数据",
    "save": "保存编辑后的图片",
    "clear": "清除图片中的元数据",
    "export": "导出元数据到 TXT 文件",
    "reveal": "在资源管理器/Finder 中显示图片",
    "copy_raw": "复制原始元数据到剪贴板",
    "copy_prompt": "复制提示词到剪贴板",
    "copy_setting": "复制参数到剪贴板",
    "sort": "按字母对提示词行排序（升序/降序）",
    "img_sort": "切换图片浏览顺序（文件名/修改时间，最新优先）",
    "view_prompt": "切换提示词竖排显示",
    "view_setting": "切换参数简洁/普通显示",
    "view_separate": "将 Clip G / Clip L / Refiner 分开显示",
    "view_tab": "将 Clip G / Clip L / Refiner 合并显示",
}
URL = {
    "release": "https://api.github.com/repos/receyuki/stable-diffusion-prompt-reader/releases/latest",
    "format": (
        "https://github.com/receyuki/stable-diffusion-prompt-reader#supported-formats"
    ),
    "comfyui": "https://github.com/receyuki/stable-diffusion-prompt-reader#comfyui",
}
DEFAULT_GRAY = "#8E8E93"
ACCESSIBLE_GRAY = ("#6C6C70", "#AEAEB2")
INACCESSIBLE_GRAY = ("gray60", "gray45")
EDITABLE = ("gray10", "#DCE4EE")
BUTTON_HOVER = ("gray86", "gray17")
TOOLTIP_DELAY = 1.5
BUTTON_WIDTH_L = 40
BUTTON_HEIGHT_L = 40
BUTTON_WIDTH_S = 36
BUTTON_HEIGHT_S = 36
LABEL_HEIGHT = 20
ARROW_WIDTH_L = 28
STATUS_BAR_IPAD = 5
PARAMETER_WIDTH = 280
STATUS_BAR_HEIGHT = BUTTON_HEIGHT_L + LABEL_HEIGHT - STATUS_BAR_IPAD * 2
PARAMETER_PLACEHOLDER = "                    "
