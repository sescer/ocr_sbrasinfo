# ocr_sbrasinfo
Обработка документов с сайта sbras.info (распознавание старых документов с 1961 по 2009 года)

## Installation
- Установить python3 (>=3.10)
- Установить все зависимости командой:
`pip install -r reqs.txt`
- Установить руссикй пакет для распознования текста (https://github.com/tesseract-ocr/tessdata/blob/main/rus.traineddata)


## Run
`python3 main.py`

## Results
- pdfs/ - папка с обработанными документами
- res.txt - промежуточный результат найденных ключевых слов в документах
- res.csv - таблица с подсчетом частоты
- keyword_frequency_chart.png - график частоты

Результаты - https://nsuru-my.sharepoint.com/:f:/g/personal/b_patrushev_ms_nsu_ru/Er3FJF2422hOuB1eAhdTRF0B40Q40EI-rIEL-K6WigsEaA?e=5dNeWC
