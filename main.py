import plotly.graph_objects as go
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout,
                             QLabel, QTextEdit)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
import sys
import os


def main():
    # без этих команд графическое ядро работать не будет
    os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
    os.environ["QT_QUICK_BACKEND"] = "software"

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)

    window = QWidget()
    window.setWindowTitle("График с отображением ховера")
    window.resize(800, 600)

    x = []
    y = []
    indexes = dict()
    for i in range(0, 30, 3):
        indexes[i] = i + 2
        indexes[i + 2] = i
        x.append(i)
        x.append(i + 2)
        y.append(0)
        y.append(0)
    x.sort()
    names = []
    for i in x:
        if indexes[i] > i:
            names.append(f'index={i}, start:{i}, end{indexes[i]}')
        else:
            names.append(f'index={i}, start:{indexes[i]}, end{i}')

    fig = go.Figure()
    fig.add_shape(type="line", x0=0, y0=0, x1=40, y1=0, line=dict(color="black", width=2))

    # отрезки только между точками
    added_pairs = set()
    for point in x:
        connected_point = indexes[point]
        if (point, connected_point) not in added_pairs and (connected_point, point) not in added_pairs:
            fig.add_shape(type="line",
                          x0=point, y0=0, x1=connected_point, y1=0,
                          line=dict(color="rgba(0, 255, 255, 0.75)", width=4))
            added_pairs.add((point, connected_point))
    print(x)
    fig.add_scatter(
        x=x, y=y, mode="markers",
        marker=dict(size=10, color="red"),
        hoverinfo="text",
        hovertext=names
    )

    browser = QWebEngineView()
    info_label = QLabel("Последний ховер: ")
    text_display = QTextEdit()
    text_display.setReadOnly(True)
    text_display.setMaximumHeight(60)

    html = fig.to_html(include_plotlyjs='cdn')
    js_code = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var plot = document.querySelector('.plotly-graph-div');
        plot.on('plotly_hover', function(data) {
            if(data.points && data.points.length > 0) {
                var text = data.points[0].hovertext;
                document.title = 'HOVER_TEXT:' + text;
            }
        });
    });
    </script>
    """
    full_html = html + js_code
    browser.setHtml(full_html)

    def update_title(title):
        if title.startswith('HOVER_TEXT:'):
            text = title[11:]  # Убираем префикс
            text_display.setPlainText(text)
            text_display.selectAll()  # Автоматически выделяем текст

    browser.titleChanged.connect(update_title)

    layout = QVBoxLayout()
    layout.addWidget(browser)
    layout.addWidget(info_label)
    layout.addWidget(text_display)
    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()