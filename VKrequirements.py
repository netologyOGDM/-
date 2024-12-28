import subprocess
import sys

def generate_requirements_txt():
    # Команда для генерации списка зависимостей
    command = [sys.executable, '-m', 'pip', 'freeze']

    # Выполнение команды и получение вывода
    result = subprocess.run(command, capture_output=True, text=True)

    # Проверка на успешность выполнения
    if result.returncode != 0:
        print(f"Ошибка при генерации файла requirements.txt: {result.stderr}")
        return

    # Запись результата в файл
    with open('requirements.txt', 'w') as file:
        file.write(result.stdout)

    print("Файл requirements.txt успешно создан.")


# Вызов функции для генерации файла
generate_requirements_txt()

