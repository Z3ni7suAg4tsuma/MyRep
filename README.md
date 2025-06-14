# HMMER Alignment Visualizer


## Описание

Графическое приложение для визуализации результатов локального выравнивания из HMMER. Позволяет:

- Загружать текстовые файлы выравнивания HMMER
- Автоматически парсить позиции выравнивания и последовательности
- Визуализировать результаты в интерактивном графике
- Просматривать последовательности при наведении курсора

## Требования

- **ОС**: Windows 10/11 или Linux с графической оболочкой
- **Python**: версия 3.8 или новее
- **Видеокарта**: с поддержкой OpenGL (или программный рендеринг)

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/hmmer-visualizer.git
cd hmmer-visualizer
Установите зависимости:
pip install -r requirements.txt

Запустите приложение:
python main.py


В интерфейсе:
Нажмите "Выбрать файл выравнивания"
Выберите текстовый файл с результатами HMMER
Наведите курсор на маркеры для просмотра последовательностей

Формат входных данных
Приложение ожидает на вход текстовые файлы выравнивания HMMER стандартного формата

Особенности реализации
Использует Plotly для интерактивной визуализации

Реализован парсер специфичного формата HMMER
JavaScript интеграция для обработки hover-событий
Оптимизировано для работы с большими выравниваниями
