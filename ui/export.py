"""Рисование таблицы истинности в изображение для экспорта в PNG."""
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen

CELL_W = 72
CELL_H = 36
MARGIN = 24
TITLE_H = 44
MIN_WIDTH = 480


def render_table_image(table, expression):
    """Возвращает QImage с заголовком «F = ...» и таблицей истинности."""
    columns = table.variables + ["F"]
    table_w = CELL_W * len(columns)
    width = max(table_w + 2 * MARGIN, MIN_WIDTH)
    height = MARGIN * 2 + TITLE_H + CELL_H * (len(table.rows) + 1)
    x0 = (width - table_w) // 2
    y0 = MARGIN + TITLE_H

    image = QImage(width, height, QImage.Format.Format_RGB32)
    image.fill(QColor("white"))
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # заголовок с выражением (длинный текст обрезается многоточием)
    font = QFont()
    font.setPointSize(13)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#222222"))
    title = painter.fontMetrics().elidedText(
        f"F = {expression}", Qt.TextElideMode.ElideRight, width - 2 * MARGIN)
    painter.drawText(QRect(MARGIN, MARGIN, width - 2 * MARGIN, TITLE_H),
                     Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)

    grid_pen = QPen(QColor("#888888"), 1)
    font.setPointSize(12)
    for r in range(len(table.rows) + 1):
        for c, name in enumerate(columns):
            x = x0 + c * CELL_W
            y = y0 + r * CELL_H
            if r == 0:
                painter.fillRect(x, y, CELL_W, CELL_H, QColor("#d9e2f3"))
                text = name
                font.setBold(True)
            else:
                row = table.rows[r - 1]
                value = table.results[r - 1] if c == len(row) else row[c]
                if c == len(row) and value == 1:
                    painter.fillRect(x, y, CELL_W, CELL_H, QColor("#e2f0d9"))
                text = str(value)
                font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#222222"))
            painter.drawText(QRect(x, y, CELL_W, CELL_H), Qt.AlignmentFlag.AlignCenter, text)
            painter.setPen(grid_pen)
            painter.drawRect(x, y, CELL_W, CELL_H)

    painter.end()
    return image
