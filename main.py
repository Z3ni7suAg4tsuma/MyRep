import plotly.graph_objects as go
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QTextEdit, QPushButton, QFileDialog)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
import sys
import os
import re


def parse_alignment_file(file_path):
    full_target = ''
    full_query = ''
    segments = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.rstrip()  # удаляем только правые пробелы
            if not line:
                continue

            if line.startswith('Aligned:'):
                parts = line[8:].strip().split(' and ')
                if len(parts) == 2:
                    full_target = parts[0].strip()
                    full_query = parts[1].strip()
                continue

            if line.startswith('target'):
                # строка с учетом табов
                parts = re.split(r'\s+', line.strip(), maxsplit=3)
                if len(parts) >= 4:
                    try:
                        start = int(parts[1])
                        end = int(parts[3])
                        seq = parts[2]
                        segments.append({
                            'seq': seq,
                            'start': start,
                            'end': end
                        })
                    except (ValueError, IndexError):
                        continue

    return {
        'full_target': full_target,
        'full_query': full_query,
        'segments': segments
    }


def main():
    # без этих команд графическое ядро работать не будет
    os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
    os.environ["QT_QUICK_BACKEND"] = "software"

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)

    window = QWidget()
    window.setWindowTitle("результат локального выравнивания")
    window.resize(800, 600)

    # Создаем элементы интерфейса
    browser = QWebEngineView()
    info_label = QLabel("INFO: ")
    text_display = QTextEdit()
    text_display.setReadOnly(True)
    text_display.setMaximumHeight(60)

    # Создаем кнопку для выбора файла
    file_button = QPushButton("Выбрать файл выравнивания")
    file_path_label = QLabel("Файл не выбран")

    # JavaScript код для обработки hover-событий
    js_code = """
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var plot = document.querySelector('.plotly-graph-div');

        function extractCoords(text) {
            var coords = {};
            var startMatch = text.match(/start=(\\d+)/);
            var endMatch = text.match(/end=(\\d+)/);
            if (startMatch) coords.start = parseInt(startMatch[1]);
            if (endMatch) coords.end = parseInt(endMatch[1]);
            return coords;
        }

        plot.on('plotly_hover', function(data) {
            if(data.points && data.points.length > 0) {
                var text = data.points[0].hovertext;
                document.title = 'HOVER_TEXT:' + text;

                var coords = extractCoords(text);
                if (coords.start !== undefined && coords.end !== undefined) {
                    var segmentId = 'segment_' + Math.min(coords.start, coords.end) + '_' + 
                                          Math.max(coords.start, coords.end);

                    var update = {'shapes': []};
                    for (var i = 0; i < plot.layout.shapes.length; i++) {
                        var shape = plot.layout.shapes[i];
                        if (shape.name === segmentId) {
                            shape.line.color = 'rgba(0, 255, 255, 0.75)';
                            shape.line.width = 4;
                        }
                        update.shapes.push(shape);
                    }
                    Plotly.relayout(plot, update);
                }
            }
        });

        plot.on('plotly_unhover', function() {
            var update = {'shapes': []};
            for (var i = 0; i < plot.layout.shapes.length; i++) {
                var shape = plot.layout.shapes[i];
                if (shape.type === 'line') {
                    shape.line.color = 'rgba(0, 0, 0, 0)';
                    shape.line.width = 0;
                }
                update.shapes.push(shape);
            }
            Plotly.relayout(plot, update);
        });
    });
    </script>
    """

    def update_visualization(data):
        full_target = data['full_target']
        full_query = data['full_query']
        x = []
        y = []
        indexes = dict()

        for i in data['segments']:
            start = int(i['start'])
            end = int(i['end'])
            indexes[start] = [end, i['seq']]
            indexes[end] = [start, i['seq']]
            x.append(start)
            x.append(end)
            y.append(0)
            y.append(0)

        x = sorted(list(set(x)))
        names = []
        for i in x:
            if indexes[i][0] > i:
                names.append(
                    f'full_target={full_target}, full_query={full_query}, seq={indexes[i][1]}, start={i}, end={indexes[i][0]}')
            else:
                names.append(
                    f'full_target={full_target}, full_query={full_query}, seq={indexes[i][1]}, start={indexes[i][0]}, end={i}')

        fig = go.Figure()

        # Добавляем основную линию
        fig.add_shape(type="line", x0=0, y0=0, x1=max(x) + 1, y1=0,
                      line=dict(color="black", width=2))

        connections = set()
        for point in x:
            connected_point = indexes[point][0]
            pair = tuple(sorted((point, connected_point)))
            if pair not in connections:
                fig.add_shape(
                    type="line",
                    x0=pair[0], y0=0, x1=pair[1], y1=0,
                    line=dict(color="rgba(0, 0, 0, 0)", width=0),
                    opacity=1,
                    name=f"segment_{pair[0]}_{pair[1]}"
                )
                connections.add(pair)

        fig.add_scatter(
            x=x, y=y, mode="markers",
            marker=dict(size=10, color="red"),
            hoverinfo="text",
            hovertext=names
        )

        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                range=[min(x) - 1, max(x) + 1]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                range=[-0.1, 0.1],
                fixedrange=True
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=400
        )

        html = fig.to_html(include_plotlyjs='cdn')
        full_html = html + js_code
        browser.setHtml(full_html)

    #обработка выбора файла
    def select_file():
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            window,
            "Выберите файл выравнивания",
            "",  # начальная директория (пустая = последняя использованная)
            "Text Files (*.exn *.txt);;All Files (*)"
        )

        if file_path:
            file_path_label.setText(file_path)
            try:
                data = parse_alignment_file(file_path)
                update_visualization(data)
            except Exception as e:
                text_display.setPlainText(f"Ошибка загрузки файла: {str(e)}")

    def update_title(title):
        if title.startswith('HOVER_TEXT:'):
            text = title[11:]  # убираем префикс
            text_display.setPlainText(text)
            text_display.selectAll()  # выделяем текст

    # подключаем кнопку
    file_button.clicked.connect(select_file)
    browser.titleChanged.connect(update_title)

    # обновляем layout
    layout = QVBoxLayout()
    layout.addWidget(file_button)
    layout.addWidget(file_path_label)
    layout.addWidget(browser)
    layout.addWidget(info_label)
    layout.addWidget(text_display)
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

