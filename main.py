import plotly.graph_objects as go
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QTextEdit, QPushButton, QFileDialog, QHBoxLayout)
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
                sqlen = parts[13]
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
    full_target = full_target[::-1]

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


def create_alignment_heatmap(query_seq, target_seq, start_pos):
    """Создает посимвольное отображение выравнивания"""
    symbols = []
    colors = []
    positions = []
    sequences = []

    # цвет для кажд символа
    for i, (q_char, t_char) in enumerate(zip(query_seq, target_seq)):
        pos = start_pos + i
        positions.append(pos)

        if q_char == t_char:
            # совпадение-зел
            symbols.append(f'{q_char}={t_char}')
            colors.append('#2ecc71')  # зеленый
            sequences.append(f'Match: {q_char} = {t_char}')
        elif q_char == '-' or t_char == '-':
            # gap-оранж
            symbols.append(f'{q_char}|{t_char}')
            colors.append('#e67e22')  # оранжевый
            sequences.append(f'Gap: {q_char} vs {t_char}')
        else:
            # несовпадение-красный
            symbols.append(f'{q_char}!{t_char}')
            colors.append('#e74c3c')  # красный
            sequences.append(f'Mismatch: {q_char} ≠ {t_char}')

    return positions, symbols, colors, sequences


def main():
    # без этих команд графическое ядро работать не будет
    os.environ["QTWEBENGINE_DISABLE_GPU"] = "1"
    os.environ["QT_QUICK_BACKEND"] = "software"

    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)

    window = QWidget()
    window.setWindowTitle("результат локального выравнивания с посимвольным отображением")
    window.resize(1200, 800)

    browser = QWebEngineView()
    info_label = QLabel("INFO: ")
    text_display = QTextEdit()
    text_display.setReadOnly(True)
    text_display.setMaximumHeight(150)
    file_button = QPushButton("Выбрать файл выравнивания")
    file_path_label = QLabel("Файл не выбран")

    # переключение между видами
    view_button = QPushButton("Переключить на общий вид")
    current_view = "detailed"  # "detailed" или "overview"

    # обработка hover-событий
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

        plot.on('plotly_click', function(data) {
            if(data.points && data.points.length > 0) {
                var text = 'CLICK:' + data.points[0].x;
                document.title = text;
            }
        });
    });
    </script>
    """

    def create_detailed_view(data):
        """Создает детальное посимвольное отображение"""
        full_target = data['target_sequence']
        full_query = data['query_sequence']
        start = data['target_start']
        end = data['target_end']
        sqlen = int(data['sqlen'])

        # heatmap для посимвольного отображения
        positions, symbols, colors, hover_texts = create_alignment_heatmap(
            full_query, full_target, start
        )

        fig = go.Figure()

        # посимвольное отображение
        for i, (pos, symbol, color, hover_text) in enumerate(zip(positions, symbols, colors, hover_texts)):
            fig.add_trace(go.Scatter(
                x=[pos],
                y=[0],
                mode='markers+text',
                marker=dict(
                    size=20,
                    color=color,
                    opacity=0.8,
                    line=dict(width=1, color='black')
                ),
                text=[symbol],
                textposition="middle center",
                textfont=dict(size=10, color='white'),
                hovertext=hover_text,
                hoverinfo='text',
                name=f'pos_{pos}'
            ))

        # линии для последовательностей
        fig.add_trace(go.Scatter(
            x=positions,
            y=[0.2] * len(positions),
            mode='lines+markers',
            line=dict(color='blue', width=2),
            marker=dict(size=6, color='blue'),
            name='Query Sequence',
            hovertext=[f'Query: {full_query[i]}' for i in range(len(positions))],
            hoverinfo='text'
        ))

        fig.add_trace(go.Scatter(
            x=positions,
            y=[-0.2] * len(positions),
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(size=6, color='red'),
            name='Target Sequence',
            hovertext=[f'Target: {full_target[i]}' for i in range(len(positions))],
            hoverinfo='text'
        ))

        # layout
        fig.update_layout(
            title="Посимвольное выравнивание (Зеленый=совпадение, Красный=несовпадение, Оранжевый=gap)",
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(
                title="Позиция",
                showgrid=True,
                gridcolor="lightgray",
                range=[start - 1, end + 1]
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                range=[-0.5, 0.5],
                fixedrange=True,
                showticklabels=False
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=600,
            showlegend=True
        )

        return fig

    def create_overview_view(data):
        """Создает общий вид выравнивания"""
        full_target = data['target_sequence']
        full_query = data['query_sequence']
        start = data['target_start']
        end = data['target_end']
        sqlen = int(data['sqlen'])

        padding = max(100, (end - start) * 0.2)
        x_min = max(0, min(start, end) - padding)
        x_max = min(sqlen, max(start, end) + padding)

        fig = go.Figure()

        fig.add_shape(type="line",
                      x0=0, y0=0, x1=sqlen, y1=0,
                      line=dict(color="black", width=2))

        fig.add_shape(type="line", x0=start, x1=start, y0=-1, y1=1,
                      line=dict(color="red", width=1, dash="dash"))
        fig.add_shape(type="line", x0=end, x1=end, y0=-1, y1=1,
                      line=dict(color="red", width=1, dash="dash"))

        fig.add_shape(type="line", x0=start, y0=0, x1=end, y1=0,
                      line=dict(color="blue", width=4))
        fig.add_shape(type="line", x0=start, y0=-0.5, x1=end, y1=-0.5,
                      line=dict(color="blue", width=4))

        fig.add_scatter(x=[start, end], y=[-0.5, -0.5],
                        mode="markers",
                        marker=dict(size=15, color="purple", opacity=0.7),
                        hovertext=[
                            f'full_query={full_query}, start={start}, end={end}',
                            f'full_query={full_query}, start={start}, end={end}'
                        ],
                        hoverinfo="text",
                        name="query_points")

        fig.add_scatter(
            x=[start, end],
            y=[0, 0],
            mode="markers",
            marker=dict(size=15, color="red", opacity=0.7),
            hovertext=[
                f'full_target={full_target}, start={start}, end={end}',
                f'full_target={full_target}, start={start}, end={end}'
            ],
            hoverinfo="text",
        )

        fig.update_layout(
            title="Общий вид выравнивания",
            margin=dict(l=20, r=20, t=50, b=20),
            xaxis=dict(title="Position", showgrid=True, gridcolor="lightgray", range=[x_min, x_max]),
            yaxis=dict(showgrid=False, zeroline=False, range=[-1, 1], fixedrange=True),
            plot_bgcolor="white", paper_bgcolor="white", height=600, showlegend=False
        )

        return fig

    def update_visualization():
        if not hasattr(update_visualization, 'current_data'):
            return

        data = update_visualization.current_data
        if current_view == "detailed":
            fig = create_detailed_view(data)
            view_button.setText("Переключить на общий вид")
        else:
            fig = create_overview_view(data)
            view_button.setText("Переключить на детальный вид")

        html = fig.to_html(include_plotlyjs='cdn') + js_code
        browser.setHtml(html)

    def toggle_view():
        nonlocal current_view
        current_view = "overview" if current_view == "detailed" else "detailed"
        update_visualization()

    def select_file():
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            window,
            "Выберите файл выравнивания",
            "",
            "Text Files (*.exn *.txt);;All Files (*)"
        )

        if file_path:
            file_path_label.setText(file_path)
            try:
                data = hmmr_parser(file_path)
                update_visualization.current_data = data
                update_visualization()

                # статистика выравнивания
                matches = sum(1 for q, t in zip(data['query_sequence'], data['target_sequence']) if q == t)
                gaps = sum(1 for q, t in zip(data['query_sequence'], data['target_sequence']) if q == '-' or t == '-')
                identity = (matches / len(data['query_sequence'])) * 100

                stats_text = f"""
                Статистика выравнивания:
                Длина выравнивания: {data['alignment_length']}
                Совпадений: {matches} ({identity:.1f}%)
                Gaps: {gaps}
                Query: {data['query_start']}-{data['query_end']}
                Target: {data['target_start'] - data['target_end']}
                """
                text_display.setPlainText(stats_text)

            except Exception as e:
                text_display.setPlainText(f"Ошибка загрузки файла: {str(e)}")

    def update_title(title):
        if title.startswith('HOVER_TEXT:'):
            text = title[11:]
            text_display.setPlainText(text)
            text_display.selectAll()
        elif title.startswith('CLICK:'):
            pos = title[6:]
            text_display.append(f"\nКлик на позиции: {pos}")

    # кнопки
    file_button.clicked.connect(select_file)
    view_button.clicked.connect(toggle_view)
    browser.titleChanged.connect(update_title)

    main_layout = QVBoxLayout()

    top_layout = QHBoxLayout()
    top_layout.addWidget(file_button)
    top_layout.addWidget(view_button)
    top_layout.addWidget(file_path_label)

    main_layout.addLayout(top_layout)
    main_layout.addWidget(browser)
    main_layout.addWidget(info_label)
    main_layout.addWidget(text_display)

    window.setLayout(main_layout)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
