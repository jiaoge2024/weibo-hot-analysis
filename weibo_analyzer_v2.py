# -*- coding: utf-8 -*-
"""
微博热搜产品创意分析工具 v2.1 (完全独立版本)
功能：自动抓取微博热搜，使用智谱AI分析产品创意，生成HTML报告
"""

import sys
import io
import os
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
from bs4 import BeautifulSoup

# Claude Agent SDK
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  警告: anthropic包未安装")
    print("   安装命令: pip install anthropic")

# ============================================================================
# 配置加载
# ============================================================================

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass

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
            "use_claude_sdk": ANTHROPIC_AVAILABLE
        },
        "output": {
            "directory": "output",
            "auto_open": False
        }
    }

CONFIG = load_config()

# ============================================================================
# 微博热搜API调用
# ============================================================================

def fetch_weibo_hot(count=10):
    """获取微博热搜榜单（带重试机制）"""
    url = CONFIG["weibo_api"]["url"]
    params = {
        "key": CONFIG["weibo_api"]["key"],
        "num": count
    }

    print(f"\n{'='*55}")
    print(f"   微博热搜产品创意分析工具 v2.1 (智谱AI增强版)")
    print(f"{'='*55}")
    print(f"\n正在获取微博热搜TOP {count}...")

    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"  尝试第 {attempt + 1}/{max_retries} 次请求...")
            response = requests.get(url, params=params, timeout=30)
            response.encoding = 'utf-8'

            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    hot_list = data.get("result", {}).get("list", [])
                    hot_list = hot_list[:count]
                    print(f"✓ 获取成功！共 {len(hot_list)} 条热搜\n")
                    return hot_list
                else:
                    print(f"  API返回错误: {data.get('msg', '未知错误')}")
            else:
                print(f"  HTTP错误: {response.status_code}")

            if attempt < max_retries - 1:
                print(f"  等待2秒后重试...")
                time.sleep(2)
            else:
                return get_backup_hot_list(count)

        except requests.exceptions.Timeout:
            print(f"  请求超时（30秒）")
            if attempt < max_retries - 1:
                print(f"  等待2秒后重试...")
                time.sleep(2)
            else:
                print(f"  所有重试均失败，使用备用数据")
                return get_backup_hot_list(count)
        except Exception as e:
            print(f"  请求异常: {str(e)[:50]}")
            if attempt < max_retries - 1:
                print(f"  等待2秒后重试...")
                time.sleep(2)
            else:
                print(f"  所有重试均失败，使用备用数据")
                return get_backup_hot_list(count)

    return get_backup_hot_list(count)

def get_backup_hot_list(count=10):
    """备用热搜列表（用于测试）"""
    print("使用备用热搜数据...\n")
    return [
        {"hotWord": f"AI技术突破{i}", "hotRank": i, "hotScore": 1000000 - i * 10000}
        for i in range(1, count + 1)
    ]

# ============================================================================
# Web搜索功能
# ============================================================================

def web_search_topic(topic, max_results=3):
    """对热搜话题进行web搜索"""
    if not CONFIG["analysis"].get("enable_web_search", True):
        return []

    try:
        search_query = f"{topic} 新闻 背景"
        encoded_query = requests.utils.quote(search_query)
        search_url = f"https://www.baidu.com/s?wd={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        time.sleep(0.5)
        response = requests.get(search_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # 尝试多种选择器
        for item in soup.select('.result')[:max_results]:
            try:
                title_elem = item.select_one('h3 a')
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:
                        results.append({
                            "title": title[:100],
                            "url": title_elem.get('href', '')
                        })
            except:
                continue

        return results

    except Exception as e:
        print(f"  [搜索跳过] {str(e)[:30]}")
        return []

# ============================================================================
# 智谱AI产品分析器
# ============================================================================

class ZhipuProductAnalyzer:
    """使用智谱AI进行产品创意分析"""

    def __init__(self):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic包未安装")

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY环境变量未设置")

        custom_api_url = os.environ.get("CUSTOM_API_URL")
        if custom_api_url:
            self.client = anthropic.Anthropic(api_key=api_key, base_url=custom_api_url)
            print(f"✓ 使用自定义API端点")
        else:
            self.client = anthropic.Anthropic(api_key=api_key)

        self.model = os.environ.get("CUSTOM_MODEL_ID", "glm-4.7")
        print(f"✓ AI分析器已初始化 (模型: {self.model})")

    def analyze_product_idea(self, topic: str, search_results: list) -> dict:
        """使用智谱AI分析产品创意"""

        context = self._build_context(topic, search_results)

        prompt = f"""你是产品创新专家。基于热搜话题进行产品创意分析：

热搜话题: {topic}

{self._format_search_results(search_results)}

请以JSON格式返回分析结果（直接返回JSON，不要其他文字）：
{{
    "name": "产品名称（不超过15字）",
    "core_features": [
        "功能1 - 描述",
        "功能2 - 描述",
        "功能3 - 描述",
        "功能4 - 描述",
        "功能5 - 描述"
    ],
    "market_pain_points": [
        "痛点1",
        "痛点2",
        "痛点3",
        "痛点4",
        "痛点5"
    ],
    "target_users": "目标用户描述（50字内）",
    "innovation_points": [
        "创新点1",
        "创新点2",
        "创新点3"
    ],
    "market_potential": {{
        "market_size": "市场规模",
        "growth_stage": "增长阶段",
        "competitive_advantage": "优势",
        "revenue_model": "商业模式"
    }},
    "scores": {{
        "innovation": 创新性(15-30),
        "pain_point": 痛点洞察(15-25),
        "potential": 潜力空间(10-15),
        "social": 社交属性(5-10),
        "practicality": 实用性(5-10),
        "feasibility": 可行性(5-10)
    }}
}}

请确保分析具体、有洞察力，避免套话。"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            result_text = response.content[0].text

            # 清理markdown标记
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

            print(f"  ✓ AI分析完成: {analysis['name'][:20]} (评分: {scores['total']})")

            return analysis

        except json.JSONDecodeError as e:
            print(f"  ✗ JSON解析失败，使用规则引擎")
            return self._rule_based_analysis(topic, search_results)
        except Exception as e:
            print(f"  ✗ AI调用失败: {str(e)[:30]}，使用规则引擎")
            return self._rule_based_analysis(topic, search_results)

    def _build_context(self, topic: str, search_results: list) -> str:
        """构建分析上下文"""
        context = f"热搜话题: {topic}\n"
        if search_results:
            context += "\n相关新闻:\n"
            for r in search_results[:3]:
                context += f"  - {r['title']}\n"
        return context

    def _format_search_results(self, search_results: list) -> str:
        """格式化搜索结果"""
        if not search_results:
            return "（暂无搜索结果）"
        return "\n".join([f"- {r['title']}" for r in search_results[:3]])

    def _rule_based_analysis(self, topic: str, search_results: list) -> dict:
        """规则引擎分析（AI失败时降级）"""
        random.seed(hash(topic))

        return {
            "name": f"「{topic[:8]}」智能助手",
            "core_features": [
                f"实时追踪'{topic}'相关动态",
                "AI智能分析与推荐",
                "个性化内容定制",
                "社交互动分享",
                "数据可视化展示"
            ],
            "market_pain_points": [
                f"关于'{topic}'的信息分散",
                "缺乏专业深度分析",
                "个性化推荐不足",
                "互动体验差",
                "数据不直观"
            ],
            "target_users": f"关注'{topic}'的用户群体",
            "innovation_points": [
                f"针对'{topic}'的专业分析",
                "AI智能推荐",
                "多维度数据融合",
                "实时追踪",
                "社交化协作"
            ],
            "market_potential": {
                "market_size": f"基于'{topic}'的垂直市场",
                "growth_stage": "成长期",
                "competitive_advantage": "专业壁垒",
                "revenue_model": "会员+增值服务"
            },
            "scores": {
                "innovation": random.randint(15, 30),
                "pain_point": random.randint(15, 25),
                "potential": random.randint(10, 15),
                "social": random.randint(5, 10),
                "practicality": random.randint(5, 10),
                "feasibility": random.randint(5, 10),
                "total": 0,
                "interest_score": 0,
                "utility_score": 0
            }
        }

# ============================================================================
# 主流程
# ============================================================================

def main(count=None):
    """主函数"""
    if count is None:
        count = CONFIG["analysis"]["default_count"]

    # 初始化AI分析器
    try:
        analyzer = ZhipuProductAnalyzer()
        use_ai = True
    except Exception as e:
        print(f"⚠️ AI初始化失败: {e}")
        print("将使用规则引擎模式")
        use_ai = False

    # 1. 获取微博热搜
    hot_list = fetch_weibo_hot(count)
    if not hot_list:
        print("未能获取热搜数据")
        return None

    # 2. 分析每个热搜
    print("正在分析热搜话题...")
    hot_topics_with_analysis = []

    for i, hot in enumerate(hot_list, 1):
        topic = hot.get("hotword", hot.get("hotWord", ""))
        rank = i

        print(f"  [{i}/{len(hot_list)}] 分析: {topic}")

        # Web搜索（可选）
        search_results = []
        if CONFIG["analysis"].get("enable_web_search"):
            try:
                search_results = web_search_topic(topic)
            except:
                pass

        # AI分析或规则引擎
        if use_ai:
            try:
                analysis = analyzer.analyze_product_idea(topic, search_results)
            except Exception as e:
                print(f"  ✗ 分析失败: {e}")
                analysis = analyzer._rule_based_analysis(topic, search_results)
        else:
            analysis = analyzer._rule_based_analysis(topic, search_results)

        hot_topics_with_analysis.append({
            "topic": topic,
            "rank": rank,
            "hot_score": hot.get("hotScore", 0),
            "search_results": search_results,
            "analysis": analysis
        })

        print()

    # 3. 生成HTML报告
    print("正在生成HTML报告...")
    generate_html_report(hot_topics_with_analysis)

    # 4. 输出摘要
    print_summary(hot_topics_with_analysis)

    return True

def generate_html_report(hot_topics_with_analysis):
    """生成HTML报告"""
    today = datetime.now()
    date_str = today.strftime("%Y%m%d")
    timestamp = today.strftime("%Y年%m月%d日 %H:%M")

    # 按评分排序
    sorted_topics = sorted(
        hot_topics_with_analysis,
        key=lambda x: x['analysis']['scores']['total'],
        reverse=True
    )

    # 统计
    excellent = sum(1 for t in sorted_topics if t['analysis']['scores']['total'] >= 80)
    good = sum(1 for t in sorted_topics if 60 <= t['analysis']['scores']['total'] < 80)
    average = sum(1 for t in sorted_topics if t['analysis']['scores']['total'] < 60)

    # 生成文件序号
    output_dir = Path(__file__).parent / CONFIG["output"]["directory"]
    output_dir.mkdir(exist_ok=True)

    existing_files = list(output_dir.glob(f"weibo_hot_{date_str}_*.html"))
    if existing_files:
        numbers = []
        for f in existing_files:
            match = re.search(rf'weibo_hot_{date_str}_(\d+)\.html', f.name)
            if match:
                numbers.append(int(match.group(1)))
        file_number = max(numbers) + 1 if numbers else 1
    else:
        file_number = 1

    filename = f"weibo_hot_{date_str}_{file_number}.html"

    # 生成HTML
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微博热搜产品创意分析 - {date_str}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        header {{ text-align: center; margin-bottom: 30px; }}
        h1 {{
            font-size: 2em;
            background: linear-gradient(90deg, #ff6b6b, #feca57, #48dbfb);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .subtitle {{ color: #94a3b8; font-size: 0.9em; }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .stat-item {{
            background: rgba(255,255,255,0.1);
            padding: 15px 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{ font-size: 1.5em; font-weight: bold; }}
        .stat-label {{ color: #94a3b8; font-size: 0.8em; }}
        .excellent {{ color: #ffd700; }}
        .good {{ color: #48dbfb; }}
        .average {{ color: #a0aec0; }}
        .topic-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .topic-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .topic-title {{ font-size: 1.4em; font-weight: bold; }}
        .score {{ font-size: 2.5em; font-weight: bold; color: #16a34a; }}
        .section {{ margin: 15px 0; }}
        .section-title {{ font-weight: bold; margin-bottom: 10px; color: #333; }}
        .feature-list {{ list-style: none; }}
        .feature-list li {{
            padding: 8px 0;
            border-bottom: 1px solid #f5f5f5;
        }}
        .tag {{
            display: inline-block;
            background: #22c55e;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        .product-details {{
            background: #fefce8;
            padding: 20px;
            border-radius: 10px;
            margin-top: 15px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #64748b;
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>微博热搜产品创意分析报告</h1>
            <p class="subtitle">基于热搜话题的产品创新机会挖掘</p>
            <p class="subtitle">生成时间: {timestamp}</p>

            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{len(sorted_topics)}</div>
                    <div class="stat-label">分析热点</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value excellent">{excellent}</div>
                    <div class="stat-label">优秀创意 (≥80分)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value good">{good}</div>
                    <div class="stat-label">良好创意 (60-80分)</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value average">{average}</div>
                    <div class="stat-label">一般创意 (<60分)</div>
                </div>
            </div>
        </header>
'''

    for topic_data in sorted_topics:
        topic = topic_data['topic']
        analysis = topic_data['analysis']
        scores = analysis['scores']

        html += f'''
        <div class="topic-card">
            <div class="topic-header">
                <div>
                    <span class="topic-title">🔥 {topic}</span>
                    <span class="tag">热</span>
                </div>
                <div class="score">{scores['total']}</div>
            </div>

            <div class="product-details">
                <div class="section">
                    <div class="section-title">🎯 产品名称</div>
                    <div>{analysis['name']}</div>
                </div>

                <div class="section">
                    <div class="section-title">⚙️ 核心功能</div>
                    <ul class="feature-list">
                        {''.join([f'<li>{f}</li>' for f in analysis['core_features'][:5]])}
                    </ul>
                </div>

                <div class="section">
                    <div class="section-title">👥 目标用户</div>
                    <div>{analysis['target_users']}</div>
                </div>

                <div class="section">
                    <div class="section-title">📊 评分详情</div>
                    <div>有趣度: {scores.get('interest_score', 0)}/80分 |
                        有用度: {scores.get('utility_score', 0)}/20分 |
                        综合: {scores['total']}分</div>
                </div>
            </div>
        </div>
'''

    html += '''
        <div class="footer">
            <p>数据来源: 微博热搜 | 生成工具: 微博热搜产品创意分析 v2.1 (智谱AI增强版)</p>
            <p>本报告基于AI分析生成，仅供参考</p>
        </div>
    </div>
</body>
</html>'''

    # 保存文件
    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ 报告已保存: {output_path.name}")

def print_summary(hot_topics_with_analysis):
    """输出分析摘要"""
    print(f"\n{'='*55}")
    print("   分析完成！")
    print(f"{'='*55}")

    sorted_by_score = sorted(
        hot_topics_with_analysis,
        key=lambda x: x['analysis']['scores']['total'],
        reverse=True
    )

    excellent = sum(1 for t in sorted_by_score if t['analysis']['scores']['total'] >= 80)
    good = sum(1 for t in sorted_by_score if 60 <= t['analysis']['scores']['total'] < 80)

    print(f"\n📊 分析概况:")
    print(f"  - 分析热点: {len(hot_topics_with_analysis)}个")
    print(f"  - 优秀创意(≥80分): {excellent}个")
    print(f"  - 良好创意(60-80分): {good}个")

    print(f"\n🌟 TOP3 优秀创意:")
    for i, t in enumerate(sorted_by_score[:3], 1):
        print(f"  {i}. {t['analysis']['name'][:30]}")
        print(f"     评分: {t['analysis']['scores']['total']}分")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else None
    main(count)
