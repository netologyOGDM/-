import configparser
import requests
import json
import os
from tqdm import tqdm

def read_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')
    vk_token = config['VK']['token']
    yandex_token = config['Yandex']['token']
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
        url = f'{self.base_url}?path={folder_name}'
        headers = {'Authorization': f'OAuth {self.token}'}
        response = requests.put(url, headers=headers)
        return response.status_code == 201

    def upload_file(self, file_path, file_name):
        upload_url = f'{self.base_url}?path=%2F{file_name}&overwrite=true'
        headers = {'Authorization': f'OAuth {self.token}'}
        response = requests.get(upload_url, headers=headers)
        if response.status_code == 200:
            with open(file_path, 'rb') as file:
                requests.put(response.json()['href'], files={'file': file})
        else:
            print(f"Ошибка при получении URL загрузки: {response.json()}")


def main():
  
    user_id = input("Введите id пользователя VK: ")

    vk_token, yandex_token = read_config()

    vk = VK(vk_token)
    yandex_disk = YandexDisk(yandex_token)

    photos = vk.get_photos(user_id, 10)

    if 'response' in photos:
        results = []
        folder_name = f'VK_{user_id}_photos'
       
        if not yandex_disk.create_folder(folder_name):
            print(f"Не удалось создать папку {folder_name} на Яндекс.Диске")
            return

        for item in tqdm(photos['response']['items'][:5], desc="Загрузка фотографий"):
            likes_count = item['likes']['count']
            sizes = sorted(item['sizes'], key=lambda size: size['width'] * size['height'], reverse=True)
            photo_url = sizes[0]['url']

            file_name = f"{likes_count}.jpg"

            response = requests.get(photo_url)
            if response.status_code == 200:
                with open(file_name, 'wb') as file:
                    file.write(response.content)
      
                yandex_disk.upload_file(file_name, file_name)
                
                results.append({
                    "file_name": file_name,
                    "size": sizes[0]['type'] 
                })
                
                os.remove(file_name)
        
        with open('results.json', 'w', encoding='utf-8') as file:
            json.dump(results, file, ensure_ascii=False, indent=4)
        print("Загрузка завершена, информация сохранена в photos.json.")
    else:
        print("Ошибка:", photos)

if __name__ == "__main__":
    main()

