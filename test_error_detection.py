import requests
from lxml import html

def test_error_page(url):
    # 定义错误指示词列表
    error_indicators = [
        'sorry',
        'page not found',
        'no longer available',
        'does not exist'
    ]
    
    try:
        # 发送请求
        r = requests.get(url)
        
        # 检查状态码
        if r.status_code != 200:
            print(f"❌ 页面访问错误 (状态码: {r.status_code})")
            return f"HTTP_{r.status_code}"
            
        doc = html.fromstring(r.content)
        
        # 获取整个页面文本并转换为小写
        page_text = doc.text_content().lower()
        
        # 检查是否包含任何错误指示词
        if any(indicator in page_text for indicator in error_indicators):
            print("❌ 这是一个错误页面")
            return True
        else:
            print("✅ 这是一个正常页面")
            return False
            
    except requests.exceptions.HTTPError as e:
        error_code = e.response.status_code
        print(f"HTTP错误: {error_code}")
        return f"HTTP_{error_code}"
        
    except requests.exceptions.ConnectionError:
        print("连接错误: 无法连接到服务器")
        return "CONNECTION_ERROR"
        
    except requests.exceptions.Timeout:
        print("超时错误: 服务器响应超时")
        return "TIMEOUT_ERROR"
        
    except requests.exceptions.TooManyRedirects:
        print("重定向错误: 过多重定向")
        return "REDIRECT_ERROR"
        
    except requests.exceptions.RequestException as e:
        print(f"其他请求错误: {e}")
        return "UNKNOWN_ERROR"

# 测试用例
if __name__ == "__main__":
    # 可以测试多个 URL
    test_urls = [
        "https://www.racingpost.com/results/1016/Janadriyah/2023-02-25/834091",  # 应该是错误页面
        "https://www.racingpost.com/results/11/cheltenham/2018-05-04/698501"  # 应该是正常页面
    ]
    
    for url in test_urls:
        print("\n测试 URL:", url)
        result = test_error_page(url)
        print("检测结果:", result)