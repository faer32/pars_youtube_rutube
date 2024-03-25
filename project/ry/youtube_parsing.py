import json
import selenium
import time
import googleapiclient
import re
import pymysql
import os
import pandas as pd
from googleapiclient.discovery import build
from mysql.connector import connect, Error
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv



class YouTubeParser:
    def __init__(self):
        self.SCROLL_PAUSE_TIME = 5
        # Настройка драйвера
        self.options = Options()
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--ignore-certificate-errors')
        #options.add_argument('--headless')
        self.options.add_argument('--start-maximized')
        self.options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
        self.chromedriver_path = fr'{os.getenv("PATH_DRIVER")}'
        self.webdriver_service = Service(self.chromedriver_path)

        self.driver = webdriver.Chrome(service=self.webdriver_service, options=self.options)
        self.driver.set_page_load_timeout(60)

        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.DEVELOPER_KEY = f"{os.getenv("API_KEY")}"

        self.youtube = googleapiclient.discovery.build(
                self.api_service_name, self.api_version, developerKey = self.DEVELOPER_KEY)

    def pars_selenium(self, name_section, name_channel):
        self.driver = self.true_channel(self.driver, name_channel)
        element = self.driver.find_element(By.ID, 'tabsContainer')
        content = element.text
        for section, engl_section in name_section:
            if section in content:
                print(f'Элемент "{section}" найден в строке.')
                if name_channel[0] == '@':
                    YOUTUBE_URL = 'https://www.youtube.com/'+ name_channel + '/' + engl_section
                else:    
                    YOUTUBE_URL = 'https://www.youtube.com/@'+ name_channel  + '/' + engl_section
                try:    
                    self.driver.get(YOUTUBE_URL)
                    time.sleep(10)
                    self.parse_identifikator(self.driver, section)
                    
                    identifikator = self.regex_indetifikator(section)
                    print(len(identifikator))
                except:
                    print("Не удалось получить доступ к странице")           
            else:
                print(f'Элемент "{section}" не найден в строке.')
        self.driver.quit()
        
    # Получение всех видео канала
    def true_channel(self, driver, name_channel):
        if name_channel[0] == '@':
            YOUTUBE_URL = 'https://www.youtube.com/'+ name_channel
        else:    
            YOUTUBE_URL = 'https://www.youtube.com/@'+ name_channel
        try:    
            driver.get(YOUTUBE_URL)
            time.sleep(10)
        except:
            print("Не удалось получить доступ к странице")    
            return    
        return driver


    def parse_identifikator(self, driver, section):
        #Скролл для загрузки комментариев
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        while True:
            try:
                driver.execute_script("window.scrollTo(0, 700)")
                driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight)")
                time.sleep(self.SCROLL_PAUSE_TIME)
                new_height = driver.execute_script("return document.documentElement.scrollHeight")
                time.sleep(self.SCROLL_PAUSE_TIME)
                if new_height == last_height:
                    break
                last_height = new_height 
            except:
                print("Ошибка")      
                break       
        page_html = BeautifulSoup(driver.page_source, 'html.parser')
        if section == "SHORTS":
            with open("page_shorts.txt", "w", encoding="utf-8") as file:
                file.write(str(page_html))
        else:
            with open("page_video.txt", "w", encoding="utf-8") as file:
                file.write(str(page_html))
        
    def regex_indetifikator(self, section):
        regex_pattern = r'href=".watch.v=(.{11})|href=".shorts.(.{11})'
        if section == "SHORTS":
            result = self.find_matches_in_file("page_shorts.txt", regex_pattern)
            co = 1
        else:
            result = self.find_matches_in_file("page_video.txt", regex_pattern)  
            co = 0  
        unique_result = list(set(result))
        first_values = []
        for item in unique_result:
            if item:
                first_value = item[co]
                first_values.append(first_value) 
        with open("all_result.txt", 'w+') as file:
            for item in first_values:
                file.write("%s\n" % item)
        return first_values

    def find_matches_in_file(self, file_path, regex_pattern):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                matches = re.findall(regex_pattern, content)
                return matches
        except FileNotFoundError:
            print(f"Файл не найден: {file_path}")
            return []
        except Exception as e:
            print(f"Ошибка: {e}")
            return []       
    
    def snippet_to_dict(self, comment_id, video_id, snippet, channel_id, parent_comment_id=False):
        t = {
            'comment_id': comment_id,
            'parent_id': parent_comment_id,
            'video_id': video_id,
            'text': snippet['textOriginal'],
            'author': snippet['authorDisplayName'],
            'author_channel_id': snippet['authorChannelId']['value'] if 'authorChannelId' in snippet else False,
            'date': snippet['publishedAt'],
            'likes': snippet['likeCount']
        }
        
        t['author_comment'] = t['author_channel_id'] and t['author_channel_id'] == channel_id
        return t
   
        
    #берем из файла все индентификаторы
    def file_identifikator(self):
        with open("all_result.txt", 'r') as file:
            lines = file.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].strip()
        lines = list(set(lines))
        return lines

    # Извлечение информации о канале из ответаv
    def info_channel(self, lines, name_channel):
        request = self.youtube.search().list(
            q=name_channel,
            type='channel',
            part='id,snippet',
            maxResults=1
        )
        response = request.execute()
        channel_id = response['items'][0]['id']['channelId']    
        video_info = []

        for video_id in lines:
            try:
                varr = 0 # количество полдписчиков надо вручную
                if (video_id != ''): 
                    request = self.youtube.videos().list(
                        part="snippet,statistics,contentDetails",
                        id=video_id
                    )
                    response = request.execute()
                    video_data = response['items'][0] 
                    video_info.append(video_data)                   
            except:
                pass
                # print(video_id)
                # print(str(varr))
        return channel_id, video_info


    # Получение комментариев
    def get_comments(self, channel_id, lines):
        comments = []
        for video_id in lines:
            
            args = {
                'videoId': video_id,
                'part': 'id,snippet,replies',
                'maxResults': 100
            }       
            varr = 0
            try:
                for page in range(0, 100):  # Максимум 10 000 запросов
                    varr += 1
                    r = self.youtube.commentThreads().list(**args).execute()
                    print(f"{page}/9 000 = {r['pageInfo']['totalResults']}")
                    if page % 90 == 0:
                        time.sleep(2)

                    for top_level in r['items']:
                        comment_id = top_level['snippet']['topLevelComment']['id']
                        snippet = top_level['snippet']['topLevelComment']['snippet']
                        comments.append(self.snippet_to_dict(comment_id, video_id, snippet, channel_id))

                        if 'replies' in top_level:
                            for reply in top_level['replies']['comments']:
                                comments.append(self.snippet_to_dict(reply['id'], video_id, reply['snippet'], comment_id, channel_id))

                    args['pageToken'] = r.get('nextPageToken')
                    if not args['pageToken']:
                        break
            except:
                #print(e)
                print(varr)
        return comments
            
    # Сохранение в JSON    
    def save_json(self, comments, video_info):
        data = {
            "video_info": video_info, 
            "comments": comments
        }

        with open('youtube_data.json', 'w+', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)   

    #форматирование строк для бд           
    def smile_delete(self, video_info, comments):
        n = 0
        for item in video_info:
            title = item['snippet']['title']
            title = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', title)
            item['snippet']['title'] = title
            
            description = item['snippet']['description']
            description = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]', '', description)
            item['snippet']['description'] = description
            
            date = item['snippet']['publishedAt']
            date = re.sub(r"[a-zA-Z]", ' ', date)
            item['snippet']['publishedAt'] = date
            
            try:
                tags = item['snippet']['tags']
                tags = ",".join(tags)
                item['snippet']['tags'] = tags
            except:
                print("необработанные теги:" + str(n))
            n += 1    
        for item in comments:
            date = item['date']
            date = re.sub(r"[a-zA-Z]", ' ', date)
            item['date'] = date
            
            text = item['text']
            text = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF⚡️🤞🥺🥰🤬☺🤩🤝🤣🤧🤗🥴🤣🤐🤔🫡🤦🤙⭐🥇🤘🤟🥳🤑❤]', ' ', text)
            item['text'] = text


if __name__ == '__main__': 
    load_dotenv()
    youtube_parser = YouTubeParser()
    name_channel = 'drhistory'
    name_section = [['Видео', 'videos'],['Shorts', 'shorts'],['Трансляции', 'streams']]
    youtube_parser.pars_selenium(name_section, name_channel)
    lines = youtube_parser.file_identifikator(name_channel)
    channel_id, video_info = youtube_parser.info_channel(lines)
    comments = youtube_parser.get_comments(channel_id, lines)
    youtube_parser.smile_delete(video_info, comments)
    youtube_parser.save_json(comments,video_info)    
    youtube_parser.connect_bd(video_info, name_channel, comments)
    print("парсинг завершен")         
    
