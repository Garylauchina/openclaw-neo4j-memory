#!/usr/bin/env python3
"""
调试汇率API - 检查实际响应格式
"""

import requests
import json
from datetime import datetime

def test_exchangerate_host():
    """测试exchangerate.host API"""
    print("🧪 测试 exchangerate.host API...")
    
    url = "https://api.exchangerate.host/latest?base=USD&symbols=CNY"
    
    try:
        print(f"请求URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        # 尝试解析JSON
        try:
            data = response.json()
            print(f"响应JSON (原始):")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 检查关键字段
            print(f"\n字段检查:")
            print(f"  'rates' in data: {'rates' in data}")
            if 'rates' in data:
                print(f"  data['rates']: {data['rates']}")
                print(f"  'CNY' in data['rates']: {'CNY' in data['rates']}")
                if 'CNY' in data['rates']:
                    print(f"  USD/CNY汇率: {data['rates']['CNY']}")
            
            print(f"  'success' in data: {'success' in data}")
            if 'success' in data:
                print(f"  data['success']: {data['success']}")
            
            print(f"  'base' in data: {'base' in data}")
            if 'base' in data:
                print(f"  data['base']: {data['base']}")
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            print(f"响应文本: {response.text[:500]}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_frankfurter_app():
    """测试frankfurter.app API（备用）"""
    print("\n🧪 测试 frankfurter.app API...")
    
    url = "https://api.frankfurter.app/latest?from=USD&to=CNY"
    
    try:
        print(f"请求URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        data = response.json()
        print(f"响应JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 检查关键字段
        print(f"\n字段检查:")
        print(f"  'rates' in data: {'rates' in data}")
        if 'rates' in data:
            print(f"  USD/CNY汇率: {data['rates'].get('CNY', 'N/A')}")
        
        print(f"  'base' in data: {'base' in data}")
        if 'base' in data:
            print(f"  data['base']: {data['base']}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_exchangerate_api():
    """测试exchangerate-api.com API（备用）"""
    print("\n🧪 测试 exchangerate-api.com API...")
    
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    
    try:
        print(f"请求URL: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        data = response.json()
        print(f"响应JSON (简化):")
        # 只显示关键字段
        simplified = {
            'base': data.get('base'),
            'date': data.get('date'),
            'rates': {k: v for k, v in list(data.get('rates', {}).items())[:5]} if data.get('rates') else {}
        }
        print(json.dumps(simplified, indent=2, ensure_ascii=False))
        
        # 检查CNY汇率
        if 'rates' in data and 'CNY' in data['rates']:
            print(f"\nUSD/CNY汇率: {data['rates']['CNY']}")
            
    except Exception as e:
        print(f"请求失败: {e}")

def test_currency_api():
    """测试免费货币API列表"""
    print("\n🧪 测试多个免费汇率API...")
    
    apis = [
        {
            "name": "exchangerate.host",
            "url": "https://api.exchangerate.host/latest?base=USD&symbols=CNY",
            "parser": lambda data: data.get("rates", {}).get("CNY")
        },
        {
            "name": "frankfurter.app", 
            "url": "https://api.frankfurter.app/latest?from=USD&to=CNY",
            "parser": lambda data: data.get("rates", {}).get("CNY")
        },
        {
            "name": "exchangerate-api.com",
            "url": "https://api.exchangerate-api.com/v4/latest/USD",
            "parser": lambda data: data.get("rates", {}).get("CNY")
        },
        {
            "name": "api.exchangeratesapi.io",
            "url": "https://api.exchangeratesapi.io/latest?base=USD&symbols=CNY",
            "parser": lambda data: data.get("rates", {}).get("CNY")
        }
    ]
    
    results = []
    
    for api in apis:
        try:
            print(f"\n测试 {api['name']}...")
            response = requests.get(api["url"], timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                rate = api["parser"](data)
                
                if rate:
                    results.append({
                        "name": api["name"],
                        "rate": rate,
                        "status": "success"
                    })
                    print(f"  ✅ 成功: {rate}")
                else:
                    print(f"  ⚠️  成功但无法解析汇率")
                    print(f"  响应: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"  ❌ 失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 异常: {e}")
    
    # 汇总结果
    print(f"\n📊 API测试汇总 ({len(results)}/{len(apis)} 成功):")
    for result in results:
        print(f"  {result['name']}: {result['rate']}")
    
    return results

def main():
    """主函数"""
    print("🔧 汇率API调试工具")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试各个API
    test_exchangerate_host()
    test_frankfurter_app()
    test_exchangerate_api()
    
    # 综合测试
    results = test_currency_api()
    
    # 推荐最佳API
    if results:
        best = min(results, key=lambda x: abs(x['rate'] - 7.0) if x['rate'] else 100)
        print(f"\n🎯 推荐使用: {best['name']} (汇率: {best['rate']})")
        
        # 生成修复代码
        print(f"\n🔧 修复代码示例:")
        if best['name'] == 'frankfurter.app':
            print("""
# 使用 frankfurter.app
url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
res = requests.get(url, timeout=5).json()
rate = res["rates"][target]
""")
        elif best['name'] == 'exchangerate-api.com':
            print("""
# 使用 exchangerate-api.com  
url = f"https://api.exchangerate-api.com/v4/latest/{base}"
res = requests.get(url, timeout=5).json()
rate = res["rates"][target]
""")
        else:
            print("""
# 通用修复（添加错误处理）
try:
    res = requests.get(url, timeout=5).json()
    if 'rates' in res and target in res['rates']:
        rate = res['rates'][target]
    elif 'data' in res and target in res['data']:
        rate = res['data'][target]
    else:
        # 尝试其他字段
        rate = res.get(target) or res.get('rate')
except:
    # 使用备用API
    pass
""")
    else:
        print("\n❌ 所有API测试失败，需要其他方案")
        
        # 备用方案：使用模拟数据
        print("\n💡 备用方案：使用模拟数据 + 真实API重试")
        print("""
# 模拟模式
if use_mock:
    rate = 7.2 + random.uniform(-0.1, 0.1)
else:
    # 尝试多个API
    for api_url in backup_apis:
        try:
            res = requests.get(api_url, timeout=3).json()
            rate = extract_rate(res)
            break
        except:
            continue
""")

if __name__ == "__main__":
    main()