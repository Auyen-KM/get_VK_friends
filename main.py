from datetime import datetime
from time import sleep

try:
    import requests
except ModuleNotFoundError:
    print('Для работы программы установите библиотеку "requests"')
    sleep(5)
    quit()


def csv_or_tsv(data, full_path, delimiter):
    import csv
    batch_size = 100
    for i in range(0, len(data), batch_size):
        try:
            with open(full_path, 'a', newline='', errors='ignore') as csvfile:
                row_writer = csv.writer(csvfile, delimiter=delimiter)
                for row in data[i:i+batch_size]:
                    try:
                        row_writer.writerow(row)
                    except UnicodeEncodeError:
                        row_writer.writerow([cell.encode('latin-1', errors='ignore').decode('latin-1') for cell in row])
                print(f"В файл записано {i + batch_size} строк")
        except FileNotFoundError:
            print("Ошибка, неверный путь, попробуйте снова\n")
            full_path, delimiter = path()
            return csv_or_tsv(data, full_path, delimiter)
    print("Внимание в отчёте не будут отображатся некоторые специфичные символы, например японские символы.")


def file_json(data, full_path):
    import json
    keys = data[0]
    json_data = {"Друзья": [{keys[j]: i[j] for j, _ in enumerate(i)} for i in data[1:]]}
    try:
        with open(full_path, 'w', encoding="utf-8") as jsonfile:
            json.dump(json_data, jsonfile, ensure_ascii=False, indent=4)
    except FileNotFoundError:
        print("Ошибка, неверный путь, попробуйте снова\n")
        full_path, delimiter = path()
        file_json(data, full_path)


def path():
    full_path = input('Введите путь к отчёту с его названием и форматом, т.е. "*название папки*/*название '
                      'отчёта*.*формат*"\nПример: "folder/file_report.tsv"\n'
                      'Нажмите Enter чтобы по умолчанию сохранить отчёт в файл report.csv в текущей директории.\n> ')
    if full_path == '':
        return "report.csv", ","
    elif full_path[:full_path.index(".", -5, -3)] == '':  # если ввели .tsv, .csv, .json
        print("Некорректное имя, попробуйте снова.\n")
        return path()
    elif full_path[-4:] == '.tsv':
        return full_path, "\t"
    elif full_path[-4:] == '.csv':
        return full_path, ','
    elif full_path[-5:] == '.json':
        return full_path, ''
    else:
        print("Некорректный ввод или неверный формат, попробуйте снова.\n")
        return path()


def collect_data(src):
    data = [("Имя", "Фамилия", "Страна", "Город", "Дата рождения", "Пол")]
    for i in src:
        if "country" not in i:  # если не указана страна
            country = "-"
            city = "-"
        else:
            country = i.get("country").get("title")
            if "city" not in i:  # если не указан город
                city = "-"
            else:
                city = i.get("city").get("title")

        if (date := i.get("bdate")) is None:  # если не указана дата рождения
            date = "-"
        else:
            date = date.split('.')
            if len(date) == 3:  # приведение даты рождения в ISO формат
                date = datetime(int(date[2]), int(date[1]), int(date[0])).strftime('%Y-%m-%d')
            else:
                try:  # если не указан год рождения
                    date = 'XXXX-' + datetime(1000, int(date[1]), int(date[0])).strftime('%m-%d')
                except ValueError:  # если год не указан, но при этом стоит дата 29 февраля(високосный год)
                    date = 'XXXX-' + datetime(1000, int(date[1]), int(date[0]) - 1).strftime('%m-%d')

        data.append((i.get("first_name"), i.get("last_name"), country, city, date, ["Жен.", "Муж."][i.get("sex") - 1]))
    return data


def get_user_data(token, id_input):
    req = requests.get(
        f"https://api.vk.com/method/friends.get?user_id={id_input}&order=name&fields=country,city,bdate,"
        f"sex&name_case=nom&access_token={token}&v=5.131").json()
    if 'error' in req:
        if req['error']['error_code'] == 100:
            print("Ошибка, пользователь c таким ID не найден.\n")
            sleep(5)
            quit()
        elif req['error']['error_code'] == 18:
            print("Ошибка, пользователь забанен.")
            sleep(5)
            quit()
    return req["response"]["items"]


def id_check(token):
    id_input = input("Введите псевдоним пользователя или его числовой ID.\n"
                     "Пример псевдонима: rules_of_war. Пример ID: 123456789.\n> ")
    req = requests.get(f"https://api.vk.com/method/utils.resolveScreenName?"
                       f"screen_name={id_input}&access_token={token}&v=5.131").json()
    if 'error' in req:
        if req['error']['error_code'] in (1114, 1116, 1117, 1118):
            print("Ошибка, не валидный токен, попробуйте заменить токен.")
            sleep(5)
            quit()
    if req["response"]:  # если существует псевдоним
        if req["response"]["type"] != 'user':
            print("Этот псевдоним принадлежит сообществу/приложению, попробуйте снова.\n")
            id_check(token)
        return req["response"]["object_id"]
    return id_input


def get_token():
    try:
        with open('access_token.txt', 'r') as file:
            token = file.read()
        if token == '':
            print("Ошибка, файл 'access_token.txt' пустой. Этот файл должен содержать в себе токен.")
            sleep(5)
            quit()
    except FileNotFoundError:
        print("Отсуствует файл 'access_token.txt' в директории с программой. Перенесите этот файл в текущию "
              "директорию с программой.\n")
        sleep(5)
        quit()
    return token


def main():
    print("Добро пожаловать в программу для получения списка друзей из ВКонтакте.")
    token = get_token()
    id_input = id_check(token)
    src = get_user_data(token, id_input)
    data = collect_data(src)
    full_path, delimiter = path()
    if delimiter == '':
        file_json(data, full_path)
    else:
        csv_or_tsv(data, full_path, delimiter)
    print('В некоторых полях могут стоять "-", если пользователь не указал некоторые данные.\n' 
          '"XXXX" в дате означает что пользователь не указал год рождения.')
    print("Файл успешно сохранён. До свидания.")
    sleep(10)


if __name__ == '__main__':
    main()
