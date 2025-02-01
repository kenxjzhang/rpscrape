#!/usr/bin/env python3

import os
import sys
import requests
from lxml import html
from utils.header import RandomHeader
from utils.settings import Settings

settings = Settings()
random_header = RandomHeader()

def get_race_info(doc):
    """获取比赛详细信息"""
    try:
        info_texts = []
        
        # 获取rp-raceInfo下的所有li元素
        race_info_items = doc.xpath("//div[@class='rp-raceInfo']//li")
        
        # 获取每个li的完整文本内容
        for item in race_info_items:
            # 获取当前li下的所有文本，包括子元素
            text = ''.join(item.xpath('.//text()'))
            # 清理多余空格
            text = ' '.join(text.split())
            if text:
                info_texts.append(text)
        
        return " ||".join(info_texts)
        
    except Exception as e:
        print(f"Error parsing race info: {str(e)}")
        return ""

def retry_failed_races(error_file_path):
    """重新爬取失败的URL"""
    base_dir = os.path.dirname(error_file_path)
    output_file = os.path.join(base_dir, 'retry_results.csv')
    new_error_file = os.path.join(base_dir, 'retry_errors.csv')
    
    print(f"处理错误文件: {error_file_path}")
    print(f"结果将保存到: {output_file}")
    
    with open(error_file_path, 'r') as f:
        failed_urls = [line.strip() for line in f.readlines()[1:]]
    
    print(f"发现 {len(failed_urls)} 个失败的URL")
    
    success_count = 0
    with open(output_file, 'w', encoding='utf-8', newline='') as csv, \
         open(new_error_file, 'w', encoding='utf-8') as error_file:
        csv.write('date,course_id,course,race_id,race_info,url\n')
        error_file.write('url\n')
        
        for url in failed_urls:
            try:
                print(f"正在处理: {url}")
                
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
                
                csv_line = f'{date},{course_id},{course},{race_id},"{race_info}",{url}\n'
                csv.write(csv_line)
                success_count += 1
                print(f"成功获取数据: {csv_line.strip()}")
                
            except Exception as e:
                print(f"Error accessing URL: {url}\nError: {str(e)}\n")
                error_file.write(f'{url}\n')
                continue
    
    print(f"\n处理完成:")
    print(f"成功获取: {success_count} 条记录")
    print(f"结果保存在: {output_file}")

def main():
    if settings.toml is None:
        sys.exit()
    
    data_dir = r'C:\Users\zhang\OneDrive\rotman\horse\data\raw\race_flat\extra_info'
    
    error_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.startswith('errors_') and file.endswith('_extra.csv'):
                error_files.append(os.path.join(root, file))
    
    if not error_files:
        print(f"在 {data_dir} 中未找到任何错误文件")
        return
    
    print(f"在 {data_dir} 中找到以下错误文件:")
    for i, file in enumerate(error_files, 1):
        print(f"{i}. {file}")
    
    while True:
        try:
            choice = input("\n请选择要处理的文件编号 (输入'all'处理所有文件): ")
            if choice.lower() == 'all':
                for file in error_files:
                    retry_failed_races(file)
                break
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(error_files):
                    retry_failed_races(error_files[idx])
                    break
                else:
                    print("无效的选择，请重试")
        except ValueError:
            print("请输入有效的数字或'all'")

if __name__ == '__main__':
    main()