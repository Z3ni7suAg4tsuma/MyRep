import plotly.graph_objects as go
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QTextEdit, QPushButton, QFileDialog)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import Qt
import sys
import os
import re


def hmmr_parser(hmmer_file):
    starget = 0
    etarget = 0
    squery = 0
    equery = 0
    full_query = []
    full_target = []
    in_alignment = False


    with open(hmmer_file, 'r') as f:
        for line in f:
            line = line.strip()


            if line.startswith('!'):
                parts = line.split()
                squery = int(parts[4])
                equery = int(parts[5])
                starget = int(parts[8])
                etarget = int(parts[7])
                sqlen=parts[13]
                continue


            if line.startswith('Alignment:'):
                in_alignment = True
                continue


            if line.startswith('Internal pipeline'):
                in_alignment = False
                continue


            if in_alignment:
                parts = line.split()
                if len(parts) < 3:
                    continue


                if line.startswith('ENSG'):
                    seq_part = parts[2]
                    full_query.append(seq_part.replace('.', '-'))


                elif re.match(r'^\d+', line.lstrip()):
                    seq_part = parts[2]
                    full_target.append(seq_part.replace('.', '-'))

    full_query = ''.join(full_query).upper()
    full_target = ''.join(full_target).upper()
    full_target=full_target[::-1]

    return {
        'target_start': starget,
        'target_end': etarget,
        'query_start': squery,
        'query_end': equery,
        'query_sequence': full_query,
        'target_sequence': full_target,
        'alignment_length': len(full_query),
        'sqlen': sqlen
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

    browser = QWebEngineView()
    info_label = QLabel("INFO: ")
    text_display = QTextEdit()
    text_display.setReadOnly(True)
    text_display.setMaximumHeight(150)
    file_button = QPushButton("Выбрать файл выравнивания")
    file_path_label = QLabel("Файл не выбран")

    # JavaScript код для обработки hover-событий
    js_code = """
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        var plot = document.querySelector('.plotly-graph-div');

        plot.on('plotly_hover', function(data) {
            if(data.points && data.points.length > 0) {
                var text = data.points[0].hovertext;
                // Передаем текст в PyQt через document.title
                document.title = 'HOVER_TEXT:' + text;
            }
        });
    });
    </script>
    """

    def update_visualization(data):
        full_target = data['target_sequence']
        full_query = data['query_sequence']
        start = data['target_start']
        end = data['target_end']
        sqlen = int(data['sqlen'])


        padding = max(100, (end - start) * 0.2)
        x_min = max(0, min(start, end) - padding)
        x_max = min(sqlen, max(start, end) + padding)


        hovertext = [
            f'full_target={full_target}, start={start}, end={end}',
            f'full_target={full_target}, start={start}, end={end}'
        ]

        fig = go.Figure()


        fig.add_shape(type="line",
                      x0=0, y0=0, x1=sqlen, y1=0,
                      line=dict(color="black", width=2))

        fig.add_shape(
            type="line",
            x0=start, x1=start,  # вертикальная линия на x=start
            y0=-1, y1=1,  # высота линии
            line=dict(color="red", width=1, dash="dash"),
        )

        fig.add_shape(
            type="line",
            x0=end, x1=end,  # вертикальная линия на x=start
            y0=-1, y1=1,  # высота линии
            line=dict(color="red", width=1, dash="dash"),
        )

        fig.add_shape(type="line",
                      x0=start, y0=0, x1=end, y1=0,
                      line=dict(color="blue", width=4),
                      name=f"segment_{start}_{end}")

        fig.add_shape(type="line",
                      x0=start, y0=-0.5, x1=end, y1=-0.5,
                      line=dict(color="blue", width=4),
                      name=f"segment_{start}_{end}")
        fig.add_scatter(x=[start, end], y=[-0.5, -0.5],
                        mode="markers+text",
                        marker=dict(size=12, color="purple"),
                        text=[f"Query"],
                        textposition='top center',
                        hoverinfo="none",
                        hovertext=[
                            f'full_query={full_query}, start={start}, end={end}',
                            f'full_query={full_query}, start={start}, end={end}'
                        ],
                        name="query_points")

        fig.add_scatter(
            x=[start, end],
            y=[0, 0],
            mode="markers+text",
            marker=dict(size=12, color="red"),
            text=[f"Start: {start}\nTarget", f"End: {end}"],
            textposition="top center",
            hoverinfo="none",
            hovertext=hovertext,
        )


        fig.update_layout(
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis=dict(
                title="Position",
                showgrid=True,
                gridcolor="lightgray",
                range=[x_min, x_max]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                range=[-1, 1],
                fixedrange=True
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=700,
            showlegend=False
        )

        html = fig.to_html(include_plotlyjs='cdn') + js_code
        browser.setHtml(html)


        text_display.setPlainText(
            f"наведитесь верхние(target) или нижние(query) точки, чтобы увидеть последовательность"
        )

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
                data = hmmr_parser(file_path)
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