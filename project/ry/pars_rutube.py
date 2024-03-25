import requests
from bs4 import BeautifulSoup
import json
import pymysql
import xml.etree.ElementTree as ET



def count_page(url, data_list):
    while True:
        response = requests.get(url)
        
        if response.status_code == 200:
            html_content = response.text
            root = ET.fromstring(html_content)
            has_next = root.find("has_next").text
            url = root.find("next").text
            
            if has_next == True:
                parse_identifikator(data_list, root)
            else:
                parse_identifikator(data_list, root)
                break
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
    save_json(data_list)

def parse_identifikator(data_list, root):
    results = root.find("results")
    for list_item in results.findall("list-item"):
        
        video_id = list_item.find("id").text # id видео
        thumbnail_url = list_item.find("thumbnail_url").text # картинка видео
        video_url = list_item.find("video_url").text # ссылка на видео
        duration = list_item.find("duration").text # длительность видео

        # у всех один
        author = list_item.find("author")
        author_id = author.find("id").text
        author_name = author.find("name").text
        author_avatar_url = author.find("avatar_url").text

        # возраст
        pg_rating = list_item.find("pg_rating")
        age = pg_rating.find("age").text
        
        product_id = list_item.find("product_id").text # продукт id  видео
        hits = list_item.find("hits").text # посещаемость
        description = list_item.find("description").text # описание
        is_livestream = list_item.find("is_livestream").text # трансляция
        publication_ts = list_item.find("publication_ts").text # дата и время публикации
        title_video = list_item.find("title").text # название видео
        feed_name = list_item.find("feed_name").text # название проекта
        
        #категория видео
        category = list_item.find("category")
        id_category = category.find("id").text
        name_category = category.find("name").text
        
        #тип видео
        type = list_item.find("type")
        id_type = type.find("id").text
        name_type = type.find("name").text
        title_type = type.find("title").text
        
        # Добавляем данные в список
        data_list.append({
            "video_id": video_id, 
            "thumbnail_url": thumbnail_url, 
            "video_url": video_url, 
            "duration": duration, 
            "author_id": author_id, 
            "author_name": author_name, 
            "author_avatar_url": author_avatar_url, 
            "age": age, 
            "product_id": product_id, 
            "hits": hits, 
            "description": description, 
            "is_livestream": is_livestream, 
            "publication_ts": publication_ts, 
            "title_video": title_video, 
            "feed_name": feed_name, 
            "id_category": id_category, 
            "name_category": name_category, 
            "id_type": id_type, 
            "name_type": name_type, 
            "title_type": title_type 
        })


def save_json(data_list):
    with open(f"video_data.json", "a", encoding="utf-8") as json_file:
        json.dump(data_list, json_file, ensure_ascii=False, indent=2)

            
if __name__ == '__main__':
    data_list = []
    # https://rutube.ru/metainfo/tv/14822/ 
    url = "https://rutube.ru/api/metainfo/tv/14822/video/?format=xml&page=1" 
    
    
    # список видео пользователя если есть channel в url 
    # url = "https://rutube.ru/api/video/person/11234072/?format=xml&page=1"
    
    # отдельное видео 
    # https://rutube.ru/video/c81d0edaf4d80eeb757a5509509fe590/
    # url = "https://rutube.ru/api/video/c81d0edaf4d80eeb757a5509509fe590/?format=xml" 
    
    # категории.  Все категории -> любая категория -> категории
    # https://rutube.ru/tags/video/6336/
    # url = "https://rutube.ru/api/tags/video/6336/?format=xml" 
     
    count_page(url,  data_list)

        

