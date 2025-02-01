#!/usr/bin/env python3

import os
import sys
import requests
from lxml import html
from utils.header import RandomHeader
from utils.settings import Settings
from utils.race import Race, VoidRaceError

settings = Settings()
random_header = RandomHeader()

def collect_failed_urls(error_dir):
    """收集所有error_*.csv文件中的失败URL"""
    failed_urls = set()
    
    for file in os.listdir(error_dir):
        if file.startswith('errors_') and file.endswith('.csv'):
            file_path = os.path.join(error_dir, file)
            with open(file_path, 'r') as f:
                # 跳过标题行
                next(f)
                for line in f:
                    url = line.strip()
                    if url:
                        failed_urls.add(url)
                        
    return sorted(list(failed_urls))

def retry_scrape(urls, output_dir):
    """重新爬取失败的URL"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    success_file = os.path.join(output_dir, 'retry_success.csv')
    error_file = os.path.join(output_dir, 'retry_errors.csv')
    
    with open(success_file, 'w', encoding='utf-8') as csv, \
         open(error_file, 'w', encoding='utf-8') as error_f:
             
        # 写入CSV头
        csv.write(settings.csv_header + '\n')
        error_f.write('url\n')
        
        total = len(urls)
        success = 0
        
        print(f"开始重试 {total} 个URL...")
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"处理 {i}/{total}: {url}")
                
                r = requests.get(url, headers=random_header.header())
                
                if r.status_code != 200:
                    print(f"HTTP Error {r.status_code}: {url}")
                    error_f.write(f'{url}\n')
                    continue
                    
                if '/error/' in r.url or 'error' in r.url.lower():
                    print(f"重定向到错误页面: {url}")
                    error_f.write(f'{url}\n')
                    continue
                
                doc = html.fromstring(r.content)
                
                error_indicators = ["Not Found"]
                page_text = doc.text_content().lower()
                if any(indicator.lower() in page_text for indicator in error_indicators):
                    print(f"页面包含错误信息: {url}")
                    error_f.write(f'{url}\n')
                    continue
                
                try:
                    race = Race(url, doc, 'flat', settings.fields)
                except VoidRaceError:
                    continue
                except Exception as e:
                    print(f"处理比赛数据时出错: {url}\n错误: {str(e)}\n")
                    error_f.write(f'{url}\n')
                    continue
                
                # 只处理平地赛
                if race.race_info['type'] != 'Flat':
                    continue
                
                for row in race.csv_data:
                    csv.write(row + '\n')
                    
                success += 1
                print(f"成功获取数据")
                
            except Exception as e:
                print(f"访问URL时出错: {url}\n错误: {str(e)}\n")
                error_f.write(f'{url}\n')
                continue
                
        print(f"\n处理完成:")
        print(f"总计: {total} 个URL")
        print(f"成功: {success} 个")
        print(f"失败: {total - success} 个")
        print(f"\n结果保存在:")
        print(f"成功数据: {success_file}")
        print(f"失败记录: {error_file}")

def main():
    if settings.toml is None:
        sys.exit()
        
    # 设置数据目录
    base_dir = r'C:\Users\zhang\OneDrive\rotman\horse\src\scraping\rpscrape\data\regions\all\flat'
    output_dir = os.path.join(base_dir, 'retry')
    
    # 收集失败的URL
    failed_urls = collect_failed_urls(base_dir)
    
    if not failed_urls:
        print(f"在 {base_dir} 中未找到任何失败的URL")
        return
        
    print(f"找到 {len(failed_urls)} 个失败的URL")
    
    # 重新爬取
    retry_scrape(failed_urls, output_dir)

if __name__ == '__main__':
    main() 