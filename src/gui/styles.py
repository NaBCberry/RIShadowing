# 明日方舟 (Arknights) UI 风格配色方案
# 设计语言：暗色科幻工业风，锐利棱角，六边形/菱形装饰，青橙双色点缀

C = {
    # 基础色
    "bg_dark": "#08080f",
    "bg_panel": "#10101a",
    "bg_card": "#16162a",
    "bg_input": "#1a1a30",
    "bg_hover": "#202040",

    # 文字
    "fg_primary": "#e8e8f4",
    "fg_secondary": "#8888a8",
    "fg_dim": "#555572",

    # 明日方舟标志色
    "cyan": "#00d4ff",
    "cyan_dim": "#0088aa",
    "cyan_glow": "#00d4ff33",
    "orange": "#ff6b35",
    "orange_dim": "#aa4500",
    "gold": "#c9a96e",
    "gold_dim": "#7a653e",

    # 状态色
    "green": "#4dff91",
    "green_dim": "#2a8850",
    "yellow": "#ffd740",
    "yellow_dim": "#aa8f00",
    "red": "#ff4455",
    "red_dim": "#aa2a33",

    # 按钮色
    "button_primary": "#ff6b35",
    "button_hover": "#ff8855",
    "button_text": "#08080f",
    "button_secondary": "#202038",
    "button_stop": "#aa3344",
    "button_stop_hover": "#cc4455",
    "button_dim": "#2a2a40",
}

FONT_FAMILY = "Microsoft YaHei"


def draw_panel_border(canvas, width, height, color=C["cyan_dim"], line_width=1):
    """绘制方舟风格的锐角边框（4个角标）"""
    l = 16
    g = 4
    w, h = width, height

    canvas.create_line(g, l, g, g, l, g, fill=color, width=line_width)
    canvas.create_line(w - g, l, w - g, g, w - l, g, fill=color, width=line_width)
    canvas.create_line(g, h - l, g, h - g, l, h - g, fill=color, width=line_width)
    canvas.create_line(w - g, h - l, w - g, h - g, w - l, h - g, fill=color, width=line_width)


def draw_hex_indicator(canvas, x, y, size=6, color=C["cyan"], filled=True):
    """绘制六边形指示器"""
    import math
    pts = []
    for i in range(6):
        angle = math.pi / 6 + i * math.pi / 3
        px = x + size * math.cos(angle)
        py = y + size * math.sin(angle)
        pts.extend([px, py])
    if filled:
        canvas.create_polygon(pts, fill=color, outline="")
    else:
        canvas.create_polygon(pts, outline=color, fill="", width=1)


def draw_section_divider(canvas, y, width, color=C["cyan_dim"]):
    """绘制分段分割线（中间菱形装饰）"""
    hw = width // 2
    canvas.create_line(10, y, hw - 8, y, fill=color, width=1)
    canvas.create_line(hw + 8, y, width - 10, y, fill=color, width=1)
    draw_hex_indicator(canvas, hw, y, size=4, color=color)


def ark_button_style():
    """返回方舟风格按钮通用配置"""
    return {
        "font": (FONT_FAMILY, 11, "bold"),
        "fg_color": C["button_primary"],
        "hover_color": C["button_hover"],
        "text_color": C["button_text"],
        "corner_radius": 2,
        "border_width": 1,
        "border_color": C["orange_dim"],
    }
