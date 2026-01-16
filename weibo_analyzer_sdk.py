# -*- coding: utf-8 -*-
"""
微博热搜产品创意分析工具 v2.0 (Claude Agent SDK增强版)
功能：自动抓取微博热搜，进行web搜索，使用Claude AI分析产品创意，生成HTML报告
"""

import sys
import io
import os
import json
import re
import time
import glob
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup

# Claude Agent SDK (可选)
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️  警告: anthropic包未安装，将使用规则引擎模式")
    print("   安装命令: pip install anthropic")

# ============================================================================
# 配置加载
# ============================================================================

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "weibo_api": {
            "url": "https://apis.tianapi.com/weibohot/index",
            "key": os.environ.get("TIANAPI_KEY", "")
        },
        "analysis": {
            "default_count": 10,
            "enable_ai_analysis": True,
            "enable_web_search": True,
            "max_concurrent_searches": 5,
            "use_claude_sdk": CLAUDE_AVAILABLE
        },
        "output": {
            "directory": "output",
            "auto_open": False  # GitHub Actions环境禁用自动打开
        }
    }

CONFIG = load_config()

# ============================================================================
# Claude Agent SDK 产品分析器
# ============================================================================

class ClaudeProductAnalyzer:
    """使用Claude Agent SDK进行产品创意分析（支持自定义API端点）"""

    def __init__(self):
        if not CLAUDE_AVAILABLE:
            raise ImportError("anthropic包未安装，请运行: pip install anthropic")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY环境变量未设置")

        # 支持自定义API端点（如智谱AI兼容接口）
        custom_api_url = os.environ.get("CUSTOM_API_URL")
        if custom_api_url:
            self.client = anthropic.Anthropic(api_key=api_key, base_url=custom_api_url)
            print(f"✓ 使用自定义API端点: {custom_api_url}")
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

        # 支持自定义模型ID
        self.model = os.environ.get("CUSTOM_MODEL_ID") or os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        print(f"✓ AI分析器已初始化 (模型: {self.model})")

    def analyze_product_idea(self, topic: str, search_results: list) -> dict:
        """使用Claude分析产品创意"""

        # 构建上下文
        context = self._build_context(topic, search_results)

        # Claude分析提示词
        prompt = f"""你是一位资深的产品创新专家和市场分析师。请基于以下热搜话题进行深度产品创意分析：

{context}

请以JSON格式返回分析结果，包含以下字段：
{{
    "name": "产品名称（不超过15字，要吸引眼球）",
    "core_features": [
        "核心功能1 - 简要描述（不超过30字）",
        "核心功能2 - 简要描述（不超过30字）",
        "核心功能3 - 简要描述（不超过30字）",
        "核心功能4 - 简要描述（不超过30字）",
        "核心功能5 - 简要描述（不超过30字）"
    ],
    "market_pain_points": [
        "用户痛点1 - 具体描述（不超过30字）",
        "用户痛点2 - 具体描述（不超过30字）",
        "用户痛点3 - 具体描述（不超过30字）",
        "用户痛点4 - 具体描述（不超过30字）",
        "用户痛点5 - 具体描述（不超过30字）"
    ],
    "target_users": "目标用户描述（50字内，具体且精准）",
    "innovation_points": [
        "创新点1（不超过25字）",
        "创新点2（不超过25字）",
        "创新点3（不超过25字）",
        "创新点4（不超过25字）",
        "创新点5（不超过25字）"
    ],
    "market_potential": {{
        "market_size": "市场规模描述（不超过30字）",
        "growth_stage": "增长阶段（如：快速成长期）",
        "competitive_advantage": "竞争优势描述（不超过40字）",
        "revenue_model": "商业模式描述（不超过30字）"
    }},
    "scores": {{
        "innovation": 创新性分数(15-30之间的整数),
        "pain_point": 痛点洞察分数(15-25之间的整数),
        "potential": 潜力空间分数(10-15之间的整数),
        "social": 社交属性分数(5-10之间的整数),
        "practicality": 实用性分数(5-10之间的整数),
        "feasibility": 可行性分数(5-10之间的整数)
    }}
}

评分标准：
- innovation (15-30分): 概念新颖程度，颠覆性创新得高分
- pain_point (15-25分): 是否抓住真实痛点，洞察深刻得高分
- potential (10-15分): 市场潜力大小，用户基数和增长空间
- social (5-10分): 是否具备传播性和社交裂变潜力
- practicality (5-10分): 解决实际问题的能力
- feasibility (5-10分): 技术实现难度，可行性高得高分

请确保：
1. 分析具体、有洞察力，避免套话和泛泛而谈
2. 针对具体热搜话题定制分析，不要用模板化内容
3. 提取话题中的关键信息（如品牌名、数字、事件等）融入分析
4. 直接返回JSON，不要有任何其他文字或解释

现在请开始分析："""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                temperature=0.7,  # 稍高的温度以获得更有创意的输出
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 解析Claude响应
            result_text = response.content[0].text

            # 清理可能的markdown代码块标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()

            analysis = json.loads(result_text)

            # 计算总分
            scores = analysis["scores"]
            interest_score = scores["innovation"] + scores["pain_point"] + scores["potential"] + scores["social"]
            utility_score = scores["practicality"] + scores["feasibility"]
            scores["total"] = round(interest_score + utility_score, 1)
            scores["interest_score"] = interest_score
            scores["utility_score"] = utility_score

            print(f"  ✓ Claude分析完成: {analysis['name']} (评分: {scores['total']})")

            return analysis

        except json.JSONDecodeError as e:
            print(f"  ✗ Claude响应解析失败: {e}")
            print(f"  响应内容: {result_text[:200]}...")
            return self._fallback_analysis(topic, search_results)
        except Exception as e:
            print(f"  ✗ Claude API调用失败: {e}")
            return self._fallback_analysis(topic, search_results)

    def _build_context(self, topic: str, search_results: list) -> str:
        """构建分析上下文"""
        context = f"""## 热搜话题
{topic}

## 话题分析
请分析这个热搜话题背后反映的用户需求、市场趋势和社会情绪。

## 背景信息
"""

        if search_results:
            context += "### 相关新闻/讨论\n"
            for i, r in enumerate(search_results[:5], 1):
                context += f"{i}. {r['title']}\n"
        else:
            context += "（暂无搜索结果，请基于话题名称本身进行分析）"

        return context

    def _fallback_analysis(self, topic: str, search_results: list) -> dict:
        """降级到规则引擎分析"""
        print(f"  ⚠️ 降级到规则引擎模式")
        # 导入原有的规则引擎
        from weibo_hot_analyzer import mock_ai_analysis
        return mock_ai_analysis(topic, search_results)


# ============================================================================
# 微博热搜API调用（复用原有代码）
# ============================================================================

def fetch_weibo_hot(count=10):
    """获取微博热搜榜单"""
    url = CONFIG["weibo_api"]["url"]
    params = {
        "key": CONFIG["weibo_api"]["key"],
        "num": count
    }

    print(f"\n{'='*55}")
    print(f"   微博热搜产品创意分析工具 v2.0 (Claude SDK)")
    print(f"{'='*55}")
    print(f"\n正在获取微博热搜TOP {count}...")

    try:
        response = requests.get(url, params=params, timeout=15)
        response.encoding = 'utf-8'
        data = response.json()

        if data.get("code") == 200:
            hot_list = data.get("result", {}).get("list", [])
            hot_list = hot_list[:count]
            print(f"获取成功！共 {len(hot_list)} 条热搜\n")
            return hot_list
        else:
            print(f"API返回错误: {data.get('msg', '未知错误')}")
            return get_backup_hot_list(count)
    except Exception as e:
        print(f"请求失败: {e}")
        return get_backup_hot_list(count)

def get_backup_hot_list(count=10):
    """备用热搜列表（用于测试）"""
    print("使用备用数据...\n")
    return [
        {"hotWord": f"测试热搜话题{i}", "hotRank": i, "hotScore": 1000000 - i * 10000}
        for i in range(1, count + 1)
    ]


# ============================================================================
# Web搜索功能（复用原有代码）
# ============================================================================

def web_search_topic(topic, max_results=3):
    """对热搜话题进行web搜索"""
    if not CONFIG["analysis"]["enable_web_search"]:
        return []

    search_query = f"{topic} 新闻 背景"
    encoded_query = requests.utils.quote(search_query)
    search_url = f"https://www.baidu.com/s?wd={encoded_query}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        time.sleep(0.5)  # 避免请求过快
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')

        results = []
        for item in soup.select('.result')[:max_results]:
            title_elem = item.select_one('h3 a')
            if title_elem:
                title = title_elem.get_text(strip=True)
                results.append({
                    "title": title,
                    "url": title_elem.get('href', '')
                })

        return results
    except Exception as e:
        print(f"  [搜索失败] {topic}: {e}")
        return []


# ============================================================================
# 产品创意分析
# ============================================================================

def analyze_product_idea(topic, search_results=[]):
    """基于热搜话题分析产品创意"""

    # 优先使用Claude SDK
    if CONFIG["analysis"].get("use_claude_sdk") and CLAUDE_AVAILABLE:
        try:
            analyzer = ClaudeProductAnalyzer()
            return analyzer.analyze_product_idea(topic, search_results)
        except Exception as e:
            print(f"  ⚠️ Claude SDK不可用: {e}")
            print(f"  降级到规则引擎...")

    # 降级到规则引擎
    from weibo_hot_analyzer import mock_ai_analysis
    return mock_ai_analysis(topic, search_results)


# ============================================================================
# 事件脉络生成（复用原有代码）
# ============================================================================

# 导入原有的HTML生成函数
def import_html_generator():
    """动态导入原有的HTML生成函数"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("weibo_hot_analyzer",
                                                     Path(__file__).parent / "weibo_hot_analyzer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ============================================================================
# 主流程
# ============================================================================

def main(count=None):
    """主函数"""
    if count is None:
        count = CONFIG["analysis"]["default_count"]

    # 检查是否使用Claude SDK
    use_claude = CONFIG["analysis"].get("use_claude_sdk", False) and CLAUDE_AVAILABLE
    if use_claude:
        print(f"🤖 使用Claude Agent SDK进行AI分析")
    else:
        print(f"📋 使用规则引擎模式")

    # 1. 获取微博热搜
    hot_list = fetch_weibo_hot(count)
    if not hot_list:
        print("未能获取热搜数据")
        return None

    # 2. 分析每个热搜
    print("正在分析热搜话题...")
    hot_topics_with_analysis = []

    for i, hot in enumerate(hot_list, 1):
        topic = hot.get("hotword", hot.get("hotWord", hot.get("word", "")))
        rank = i

        print(f"  [{i}/{len(hot_list)}] 分析: {topic}")

        # Web搜索
        search_results = []
        if CONFIG["analysis"]["enable_web_search"]:
            print(f"       - 正在搜索相关信息...")
            search_results = web_search_topic(topic)

        # AI分析
        print(f"       - 正在进行产品创意分析...")
        analysis = analyze_product_idea(topic, search_results)

        hot_topics_with_analysis.append({
            "topic": topic,
            "rank": rank,
            "hot_score": hot.get("hotScore", 0),
            "search_results": search_results,
            "analysis": analysis
        })

        print()  # 空行分隔

    # 3. 生成HTML报告（使用原有的生成函数）
    print("正在生成HTML报告...")
    module = import_html_generator()
    html_content, filename = module.generate_html_report(hot_topics_with_analysis)

    output_dir = Path(__file__).parent / CONFIG["output"]["directory"]
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # 4. 输出结果
    print(f"\n{'='*55}")
    print("   分析完成！")
    print(f"{'='*55}")
    print(f"\n报告已保存: {output_path.absolute()}")
    print(f"\n📊 分析概况:")

    sorted_by_score = sorted(
        hot_topics_with_analysis,
        key=lambda x: x['analysis']['scores']['total'],
        reverse=True
    )

    excellent = sum(1 for t in sorted_by_score if t['analysis']['scores']['total'] >= 80)
    good = sum(1 for t in sorted_by_score if 60 <= t['analysis']['scores']['total'] < 80)

    print(f"  - 分析热点: {len(hot_topics_with_analysis)}个")
    print(f"  - 优秀创意(≥80分): {excellent}个")
    print(f"  - 良好创意(60-80分): {good}个")

    print(f"\n🌟 TOP3 优秀创意:")
    for i, t in enumerate(sorted_by_score[:3], 1):
        print(f"  {i}. {t['analysis']['name']}")
        print(f"     评分: {t['analysis']['scores']['total']}分")
        print(f"     核心: {', '.join(t['analysis']['core_features'][:2])}")

    # 自动打开浏览器（本地运行时）
    if CONFIG["output"].get("auto_open", False):
        try:
            import webbrowser
            webbrowser.open(f'file://{output_path.absolute()}')
            print(f"\n已在浏览器中打开报告")
        except:
            pass

    return str(output_path.absolute())


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(count)
