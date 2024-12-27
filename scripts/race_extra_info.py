#!/usr/bin/env python3

import gzip
import requests
import os
import sys
from dataclasses import dataclass
from lxml import html
from orjson import loads

from utils.argparser import ArgParser
from utils.completer import Completer
from utils.header import RandomHeader
from utils.settings import Settings
from utils.course import course_name, courses
from utils.lxml_funcs import xpath

settings = Settings()
random_header = RandomHeader()

@dataclass
class RaceList:
    course_id: str
    course_name: str 
    url: str

# 保持原有的URL获取逻辑
def get_race_urls(tracks, years, code):
    urls = set()
    url_course = 'https://www.racingpost.com:443/profile/course/filter/results'
    url_result = 'https://www.racingpost.com/results'
    
    race_lists = []
    
    for track in tracks:
        for year in years:
            race_list = RaceList(*track, f'{url_course}/{track[0].lower()}/{year}/{code}/all-races')
            race_lists.append(race_list)
            
    for race_list in race_lists:
        r = requests.get(race_list.url, headers=random_header.header())
        races = loads(r.text)['data']['principleRaceResults']
        
        if races:
            for race in races:
                race_date = race["raceDatetime"][:10]
                race_id = race["raceInstanceUid"]
                url = f'{url_result}/{race_list.course_id}/{race_list.course_name}/{race_date}/{race_id}'
                urls.add(url.replace(' ', '-').replace("'", ''))
                
    return sorted(list(urls))

def get_race_urls_date(dates, region):
    urls = set()
    days = [f'https://www.racingpost.com/results/{d}' for d in dates]
    course_ids = {course[0] for course in courses(region)}
    
    for day in days:
        r = requests.get(day, headers=random_header.header())
        doc = html.fromstring(r.content)
        races = xpath(doc, 'a', 'link-listCourseNameLink')
        
        for race in races:
            if race.attrib['href'].split('/')[2] in course_ids:
                urls.add('https://www.racingpost.com' + race.attrib['href'])
                
    return sorted(list(urls))

def get_race_info(doc):
    """获取比赛详细信息，保持原始格式"""
    try:
        info_texts = []
        
        # 获取rp-raceInfo下的所有li元素
        race_info_items = doc.xpath("//div[@class='rp-raceInfo']//li")
        
        # 获取每个li的完整文本内容
        for item in race_info_items:
            # 获取当前li下的所有文本，包括子元素
            text = ''.join(item.xpath('.//text()'))
            # 清理多余空格：将多个空格替换为单个空格，并去除首尾空格
            text = ' '.join(text.split())
            if text:
                info_texts.append(text)
        
        # 用 " || " 分隔不同的li内容
        return " ||".join(info_texts)
        
    except Exception as e:
        print(f"Error parsing race info: {str(e)}")
        return ""

# 这是新的数据抓取函数,需要自定义具体要抓取的数据
def scrape_extra_info(races, folder_name, file_name, code):
    out_dir = f'../data/{folder_name}/{code}'
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    file_path = f'{out_dir}/{file_name}_extra.csv'
    error_path = f'{out_dir}/errors_{file_name}_extra.csv'
    
    with open(file_path, 'w', encoding='utf-8') as csv, open(error_path, 'w') as error_file:
        # CSV表头
        csv.write('date,course_id,course,race_id,race_info,url\n')
        error_file.write('url\n')
        
        for url in races:
            try:
                # 从URL中解析基本信息
                url_parts = url.split('/')
                course_id = url_parts[4]
                course = url_parts[5]
                date = url_parts[6]
                race_id = url_parts[7]
                
                r = requests.get(url, headers=random_header.header())
                
                if r.status_code != 200:
                    print(f"HTTP Error {r.status_code}: {url}")
                    error_file.write(f'{url}\n')
                    continue
                    
                doc = html.fromstring(r.content)
                race_info = get_race_info(doc)
                
                # 写入CSV行
                csv_line = f'{date},{course_id},{course},{race_id},"{race_info}",{url}\n'
                csv.write(csv_line)
                
            except Exception as e:
                print(f"Error accessing URL: {url}\nError: {str(e)}\n")
                error_file.write(f'{url}\n')
                continue

def main():
    if settings.toml is None:
        sys.exit()
        
    parser = ArgParser()
    
    if len(sys.argv) > 1:
        args = parser.parse_args(sys.argv[1:])
        
        if args.date:
            folder_name = 'dates/' + args.region
            file_name = args.date.replace('/', '_')
            races = get_race_urls_date(parser.dates, args.region)
        else:
            folder_name = args.region if args.region else course_name(args.course)
            file_name = args.year
            races = get_race_urls(parser.tracks, parser.years, args.type)
            
        scrape_extra_info(races, folder_name, file_name, args.type)
    else:
        if sys.platform == 'linux':
            import readline
            completions = Completer()
            readline.set_completer(completions.complete)
            readline.parse_and_bind('tab: complete')
            
        while True:
            args = input('[rpscrape]> ').lower().strip()
            args = parser.parse_args_interactive([arg.strip() for arg in args.split()])
            
            if args:
                if 'dates' in args:
                    races = get_race_urls_date(args['dates'], args['region'])
                else:
                    races = get_race_urls(args['tracks'], args['years'], args['type'])
                    
                scrape_extra_info(races, args['folder_name'], args['file_name'], args['type'])

if __name__ == '__main__':
    main() 