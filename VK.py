import configparser
import requests
import json
import os
from tqdm import tqdm
from urllib.parse import quote
from datetime import datetime

def read_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')
    vk_token = config['Tokens']['vk_token']
    yandex_token = config['Tokens']['yandex_token']
    return vk_token, yandex_token
class VK:
    def __init__(self, token, version='5.131'):
        self.params = {
            'access_token': token,
            'v': version
        }
        self.base = 'https://api.vk.com/method/'

    def get_photos(self, user_id, count):
        url = f'{self.base}photos.get'
        params = {
            'owner_id': user_id,
            'count': count,
            'album_id': 'profile',
            'extended': '1'
        }
        params.update(self.params)
        response = requests.get(url, params=params)
        return response.json()

class YandexDisk:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def create_folder(self, folder_name):
        url = f'https://cloud-api.yandex.net/v1/disk/resources?path={quote(folder_name)}'
        headers = {'Authorization': f'OAuth {self.token}'}
        response = requests.put(url, headers=headers)
        return response.status_code in (201, 409)  # 409 - папка уже существует

    def upload_file(self, file_path, folder_name, file_name):
        upload_url = f'{self.base_url}?path={quote(f"{folder_name}/{file_name}")}&overwrite=true'
        headers = {'Authorization': f'OAuth {self.token}'}

        response = requests.post(upload_url, headers=headers)
        if response.status_code == 201:
            upload_link = response.json()['href']
            with open(file_path, 'rb') as file:
                response = requests.post(upload_link, files={'file': file})
            if response.status_code == 201:
                print("Файл успешно загружен.")
            else:
                print(f"Ошибка при загрузке файла: {response.json()}")
        else:
            print(f"Ошибка при получении URL загрузки: {response.json()}")

class FileUploader:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token

    def post_request(self, url, headers, files=None):
        response = requests.post(url, headers=headers, files=files)
        if response.status_code != 201:
            raise Exception(f"Ошибка: {response.json()}")
        return response.json()

    def upload_file(self, folder_name, file_name):
        upload_url = f'{self.base_url}?path={quote(f"{folder_name}/{file_name}")}&overwrite=true'
        headers = {'Authorization': f'OAuth {self.token}'}
        try:
            upload_info = self.post_request(upload_url, headers)
            upload_link = upload_info['href']
            with open(file_name, 'rb') as file:
                self.post_request(upload_link, headers, files={'file': file})
            print("Файл успешно загружен.")
        except Exception as e:
            print(e)

def process_photos(photos):
    results = {}
    for item in tqdm(photos['response']['items'][:5], desc="Загрузка фотографий"):
        likes_count = item['likes']['count']
        sizes = sorted(item['sizes'], key=lambda size: size['width'] * size['height'], reverse=True)
        photo_url = sizes[0]['url']
        if likes_count not in results:
            results[likes_count] = {
                "size": sizes[0]['type'],
                "url": photo_url, "count": 1
            }
        else:
            results[likes_count]["count"] += 1
            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{likes_count}_{date_str}.jpg"
            results[likes_count]["url"] = photo_url
    return results

def main():
    user_id = input("Введите id пользователя VK: ")
    vk_token, yandex_token = read_config()
    vk = VK(vk_token)
    yandex_disk = YandexDisk(yandex_token)
    photos = vk.get_photos(user_id, 5)
    if 'response' in photos:
        folder_name = f'VK_{user_id}_photos'
        if not yandex_disk.create_folder(folder_name):
            print(f"Не удалось создать папку {folder_name} на Яндекс.Диске")
            return
        results = process_photos(photos)

    uploader = FileUploader(yandex_disk.base_url, yandex_token)
    for likes_count, data in results.items():
        file_name = f"{likes_count}.jpg"
        response = requests.post(data['url'])
        if response.status_code == 200:
            with open(file_name, 'wb') as file:
                file.write(response.content)
            uploader.upload_file(folder_name, file_name)
            os.remove(file_name)
        with open('results.json', 'w', encoding='utf-8') as file:
            json.dump(results, file, ensure_ascii=False, indent=4)
        print("Загрузка завершена, информация сохранена в results.json.")
    else:
        print("Ошибка:", photos)

if __name__ == "__main__":
    main()
