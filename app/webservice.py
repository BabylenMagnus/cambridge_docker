from fastapi import FastAPI, Query

import logging
import requests
from bs4 import BeautifulSoup

app = FastAPI()
logging.getLogger().setLevel(logging.INFO)

BASE_URL = "https://dictionary.cambridge.org/ru/словарь/англо-русский"


def get_cambridge_english_russian(word):
    url = f"{BASE_URL}/{word}"

    headers = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/87.0.4280.88 Safari/537.36"),
               "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7", "Referer": "https://dictionary.cambridge.org/"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка при получении данных: {e}"}

    soup = BeautifulSoup(response.text, 'html.parser')

    entries = soup.find_all("div", class_="entry-body__el")
    if not entries:
        return {"error": f"Слово '{word}' не найдено в словаре."}

    data = []

    for entry in entries:
        entry_data = {}

        # Получение заголовка
        headword_div = entry.find("div", class_="di-title")
        if headword_div:
            entry_data['headword'] = headword_div.text.strip()
        else:
            entry_data['headword'] = word  # Если заголовок не найден

        # Часть речи
        pos_span = entry.find("span", class_="pos dpos")
        if pos_span:
            entry_data['part_of_speech'] = pos_span.text.strip()
        else:
            entry_data['part_of_speech'] = None  # Если часть речи не найдена

        # Произношение
        pron_span = entry.find("span", class_="pron dpron")
        if pron_span:
            entry_data['pronunciation'] = pron_span.text.strip()
        else:
            entry_data['pronunciation'] = None  # Если произношение не найдено

        # Значения и примеры
        def_blocks = entry.find_all("div", class_="def-block ddef_block")
        meanings = []
        for def_block in def_blocks:
            sense_data = {}

            # Уровень (CEFR)
            level_span = def_block.find("span", class_="def-info ddef-info")
            if level_span:
                cefer_span = level_span.find("span", class_=lambda x: x and 'dxref' in x)
                if cefer_span:
                    sense_data['level'] = cefer_span.text.strip()
                else:
                    sense_data['level'] = None
            else:
                sense_data['level'] = None

            # Определение
            def_div = def_block.find("div", class_="def ddef_d db")
            if def_div:
                sense_data['definition'] = def_div.text.strip()
            else:
                sense_data['definition'] = None

            # Перевод
            trans_span = def_block.find("span", class_=lambda x: x and 'trans' in x)
            if trans_span:
                sense_data['translation'] = trans_span.text.strip()
            else:
                sense_data['translation'] = None
                print(f"Перевод не найден для определения: '{sense_data.get('definition')}'")

            # Метки (например, грамматические)
            labels = []
            label_spans = def_block.find_all("span", class_="gram dgram")
            for label_span in label_spans:
                labels.append(label_span.text.strip())
            if labels:
                sense_data['labels'] = labels
            else:
                sense_data['labels'] = None

            # Примеры
            examples = []
            example_divs = def_block.find_all("div", class_="examp dexamp")
            for ex_div in example_divs:
                ex_span = ex_div.find("span", class_="eg deg")
                if ex_span:
                    example_text = ex_span.text.strip()
                    examples.append(example_text)
            if examples:
                sense_data['examples'] = examples
            else:
                sense_data['examples'] = None  # Если примеры не найдены

            if sense_data:
                meanings.append(sense_data)

        if meanings:
            entry_data['meanings'] = meanings

        # Основной перевод слова (если есть)
        main_translation_span = entry.find("span", class_=lambda x: x and 'trans' in x and 'dtrans' in x)
        if main_translation_span:
            entry_data['main_translation'] = main_translation_span.text.strip()
        else:
            entry_data['main_translation'] = None

        data.append(entry_data)

    return data


@app.post("/translate")
def repeat_card(
        word: str = Query(..., description="Слово для перевода."),
):
    return get_cambridge_english_russian(word)
