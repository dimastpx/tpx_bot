# 5922075139:AAGPdc4mijSUmm2S6XSfcH1v67UMhMU-sOs

import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import json
import re

# Замените "YOUR_BOT_TOKEN" на ваш токен бота
BOT_TOKEN = "5922075139:AAGPdc4mijSUmm2S6XSfcH1v67UMhMU-sOs"
OFFSET = 0


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
    response = requests.get(url, params=params)
    return response.json()


def send_photo(chat_id, photo_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {"document": open(photo_path, "rb")}
    data = {"chat_id": chat_id}
    response = requests.post(url, data=data, files=files)
    return response.json()


def get_file_info(file_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
    params = {"file_id": file_id}
    response = requests.get(url, params=params)
    return response.json().get("result")


def process_image(file_id, chat_id, caption):
    file_info = get_file_info(file_id)
    if not file_info:
        send_message(chat_id, "Произошла ошибка при получении файла.")
        return

    file_path = file_info["file_path"]
    image_response = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")

    image = Image.open(BytesIO(image_response.content))

    # Конвертируем изображение в RGBA формат и изменяем размер
    image = image.convert("RGBA")
    image = image.resize((512, 512), Image.ANTIALIAS)

    # Обработка комментариев
    caption_text, caption_color = parse_caption(caption)
    if len(caption_text) > 15:
        caption_text = caption_text[:15]
        send_message(chat_id, "Текст сокращен до 15 символов.")

    if caption_color and caption_color in COLORS:
        draw_text_with_color(image, caption_text, caption_color, chat_id)
    elif len(caption_text) > 0:
        draw_text(image, caption_text)

    # Создаем временное файловое имя для PNG изображения
    temp_filename = "temp_image.png"

    # Сохраняем PNG изображение
    image.save(temp_filename, "PNG")

    # Отправляем конвертированное изображение пользователю
    send_photo(chat_id, temp_filename)

    # Обновляем кнопки
    reply_markup = {
        "keyboard": [["Помощь"]],
        "resize_keyboard": True
    }
    send_message(chat_id, "Кнопки обновлены.", json.dumps(reply_markup))

    # Удаляем временный файл
    os.remove(temp_filename)

def parse_caption(caption):
    match = re.search(r'\((#[0-9A-Fa-f]{6}|\w+)\)', caption)
    if match:
        color_or_text = match.group(1)
        text = caption.replace(match.group(), "").strip()
        return text, color_or_text
    else:
        return caption[:15], None


def draw_text(image, text):
    draw = ImageDraw.Draw(image)
    font_size = 60  # Измените размер шрифта на желаемое значение
    font = ImageFont.truetype("arial.ttf", font_size)  # Выберите подходящий шрифт
    text_size = draw.textsize(text, font=font)
    x = (image.width - text_size[0]) // 2
    y = (image.height - text_size[1]) // 2
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

def draw_text_with_color(image, text, color_or_text, chat_id):
    draw = ImageDraw.Draw(image)
    font_size = 60  # Измените размер шрифта на желаемое значение
    font = ImageFont.truetype("arial.ttf", font_size)  # Выберите подходящий шрифт
    text_size = draw.textsize(text, font=font)
    x = (image.width - text_size[0]) // 2
    y = (image.height - text_size[1]) // 2

    if color_or_text in COLORS:
        fill_color = COLORS[color_or_text]
    else:
        send_message(chat_id, "Цвет неизвестен. Текст будет написан белым цветом.")
        fill_color = (255, 255, 255, 255)

    draw.text((x, y), text, font=font, fill=fill_color)

COLORS = {
    "red": (255, 0, 0, 255),
    "black": (0, 0, 0, 255),
    "orange": (255, 165, 0, 255),
    "yellow": (255, 255, 0, 255),
    "green": (0, 128, 0, 255),
    "blue": (0, 0, 255, 255),
    "purple": (128, 0, 128, 255),
    "pink": (255, 192, 203, 255),
    # Добавьте другие цвета по аналогии
}


def main():
    global OFFSET
    while True:
        updates = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={OFFSET}").json()
        for update in updates.get("result", []):
            OFFSET = update["update_id"] + 1
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]

                if "text" in update["message"]:
                    text = update["message"]["text"].lower()
                    if text == "/start":
                        reply_markup = {
                            "keyboard": [["Помощь"]],
                            "resize_keyboard": True
                        }
                        send_message(chat_id, "Бот был перезагружен. Отправьте /start, чтобы начать.",
                                     json.dumps(reply_markup))
                    elif text == "помощь":
                        help_message = "Этот бот для конвертации изображений в PNG размером 512x512 пикселей. Просто отправьте изображение, и бот его обработать. Для указания цвета текста используйте комментарий вида: Текст (цвет), где цвет может быть названием (например, 'red', 'black') или шестнадцатеричным кодом (например, '#FF0000'). Максимальная длина комментария 15 символов."
                        send_message(chat_id, help_message, reply_markup=json.dumps({"remove_keyboard": True}))

                if "photo" in update["message"]:
                    file_id = update["message"]["photo"][-1]["file_id"]
                    caption = update["message"].get("caption", "")  # Заголовок фото
                    process_image(file_id, chat_id, caption)
                elif "document" in update["message"]:
                    file_id = update["message"]["document"]["file_id"]
                    caption = update["message"].get("caption", "")  # Заголовок документа
                    process_image(file_id, chat_id, caption)


if __name__ == '__main__':
    main()