import os
import glob
from dotenv import load_dotenv
from openai import AsyncOpenAI
from typing import List, Union


from common_lib.prompt.system_prompts import PROMPTS

load_dotenv()


def get_py_files(directory: str, current_script: str) -> List[str]:
    """
    Получает список всех .py файлов в указанной директории и её поддиректориях,
    исключая папки venv и .venv.

    :param directory: Путь к директории
    :param current_script: Имя текущего скрипта
    :return: Список путей к .py файлам
    """
    all_files = glob.glob(os.path.join(directory, '**', '*.py'), recursive=True)
    excluded_dirs = {'venv', '.venv', 'prompt', 'exclude'}
    return [
        f for f in all_files
        if not any(excluded_dir in f.split(os.sep) for excluded_dir in excluded_dirs)
           and os.path.basename(f) != current_script
           and os.path.basename(f) != '__init__.py'

    ]




def ask_user(prompt: str) -> bool:
    """
    Спрашивает пользователя, нужно ли продолжать обработку файла.

    :param prompt: Вопрос пользователю
    :return: True если пользователь соглашается, иначе False
    """
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in {'y', 'n'}:
            return response == 'y'


def review_code(openai_client: OpenAI, code: str) -> Union[tuple[str, int], str]:
    """
    Отправляет код файла на ревью в ChatGPT и получает результат.

    :param openai_client: OpenAI client
    :param code: Код для ревью
    :return: Результат ревью и количество использованных токенов
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": PROMPTS['code_review']},
                {"role": "user", "content": f"Выполни подробное code review для:\n\n{code}"}
            ]
        )

        # print(response.choices[0].message)
        # print(f'{response}')
        # print(f'{response.model_dump_json()}')
        print(f'{response.usage.total_tokens}')

        return response.choices[0].message.content.strip(), response.usage.total_tokens
    except Exception as e:
        return f"Ошибка при обработке кода: {str(e)}"


def save_review(file_path: str, review: str):
    """
    Сохраняет результат ревью в текстовый файл с одноименным названием.
    :param file_path: Путь к .py файлу
    :param review: Результат ревью
    """
    try:
        review_file_path = f"{os.path.splitext(file_path)[0]}_review.txt"
        with open(review_file_path, 'w', encoding='utf-8') as review_file:
            review_file.write(review)
    except Exception as e:
        print(f"Ошибка при сохранении ревью для файла {file_path}: {str(e)}")


def process_file(openai_client: OpenAI, file_path: str):
    """
    Обрабатывает отдельный .py файл: считает токены, отправляет на ревью, если токенов меньше 1000,
    либо спрашивает пользователя, если токенов больше 1000.

    :param openai_client: OpenAI client
    :param file_path: Путь к .py файлу
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            code = file.read()

        token_count = count_tokens(code)
        print(f"Количество токенов в файле {file_path}: {token_count}")

        if token_count > 1000:
            if not ask_user(f"Файл {file_path} содержит {token_count} токенов. Обработать его дальше?"):
                print(f"Файл {file_path} пропущен.")
                return

        review, _ = review_code(openai_client, code)
        save_review(file_path, review)
        print(f"Результат ревью сохранен в: {os.path.splitext(file_path)[0]}_review.txt")

    except Exception as e:
        print(f"Ошибка при обработке файла {file_path}: {str(e)}")


def main(openai_client: OpenAI, directory: str, current_script: str):
    """
    Основная функция для проведения кодревью всех .py файлов в указанной директории и её поддиректориях,
    исключая папки venv, .venv и файлы __init__.py.

    :param openai_client: OpenAI client
    :param directory: Путь к директории
    :param current_script: Имя текущего скрипта
    """
    py_files = get_py_files(directory, current_script)
    for py_file in py_files:
        process_file(openai_client, py_file)


if __name__ == "__main__":
    client = AsyncOpenAI()
    # defaults to getting the key using os.environ.get("OPENAI_API_KEY")
    # if you saved the key under a different environment variable name, you can do something like:
    # client = OpenAI(
    #   api_key=os.environ.get("CUSTOM_ENV_NAME"),
    # )
    main(client, 'C:\\Users\\Genesis\\PycharmProjects\\play_scraper', os.path.basename(__file__))
