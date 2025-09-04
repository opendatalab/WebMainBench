#!/usr/bin/env python3
"""
数据集统计和筛选工具
统计WebMainBench数据集中的数据分布
"""
import json
import sys
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import argparse

from llm_web_kit.simple import extract_content_from_main_html
from llm_web_kit.input.datajson import ContentList



class DatasetStatistics:
    """数据集统计分析类"""
    
    def __init__(self, jsonl_file: str, output_file: str):
        self.jsonl_file = Path(jsonl_file)
        self.output_file = Path(output_file)
        self.data = []
        self.stats = {}
        
    def load_data(self):
        """加载JSONL数据"""
        print(f"📖 正在加载数据文件: {self.jsonl_file}")
        
        if not self.jsonl_file.exists():
            raise FileNotFoundError(f"文件不存在: {self.jsonl_file}")
        
        line_count = 0
        try:
            with open(self.jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        self.data.append(data)
                        line_count += 1
                        
                        # 每10000行显示进度
                        if line_count % 10000 == 0:
                            print(f"  📊 已加载 {line_count:,} 行...")
                            
                    except json.JSONDecodeError as e:
                        print(f"  ⚠️ 第 {line_num} 行JSON解析错误: {e}")
                        continue
                        
        except Exception as e:
            raise RuntimeError(f"读取文件时出错: {e}")
        
        print(f"✅ 成功加载 {len(self.data):,} 条数据")
        return self
    
    def generate_content_list(self, data):
        """生成content_list字段，使用llm_web_kit提取内容"""
        try:                   
            html_content = data.get("html", "")
            url = data.get("url", "")
            
            # 验证必要字段
            if not html_content:
                data["content_list"] = []
                return data
            
            # 提取内容
            result = extract_content_from_main_html(url, html_content, 'json')
            
            # 解析JSON
            try:
                result_json = json.loads(result)
                data["content_list"] = result_json.get("content_list", [])
                    
            except json.JSONDecodeError as e:
                data["content_list"] = []
            
            return data
            
        except Exception as e:
            # 确保即使出错也有content_list字段
            data["content_list"] = []
            return data

    # 计算HTML的DOM_WIDTH和DOM_DEPTH
    def calculate_DOM_WIDTH_DEPTH(self, data):
        """计算DOM树的深度和宽度"""
        try:
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
                
            html_content = data.get("html", "")
            if not html_content:
                data["meta"]["DOM_WIDTH"] = 0
                data["meta"]["DOM_DEPTH"] = 0
                return data
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 找到实际的根元素（通常是html标签）
            root_elements = [child for child in soup.children if child.name]
            
            if not root_elements:
                data["meta"]["DOM_WIDTH"] = 0
                data["meta"]["DOM_DEPTH"] = 0
                return data
            
            # 计算所有根元素的最大深度和宽度
            max_depth = 0
            max_width = 0
            
            for root in root_elements:
                depth = self._calculate_dom_depth(root)
                width = self._calculate_dom_width(root)
                max_depth = max(max_depth, depth)
                max_width = max(max_width, width)
            
            data["meta"]["DOM_WIDTH"] = max_width
            data["meta"]["DOM_DEPTH"] = max_depth
            
            return data
            
        except Exception as e:
            # 如果解析失败，设置默认值
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["DOM_WIDTH"] = 0
            data["meta"]["DOM_DEPTH"] = 0
            return data
    
    def _calculate_dom_depth(self, element):
        """递归计算DOM树的最大深度"""
        if not element or not hasattr(element, 'name') or not element.name:
            return 0
        
        # 获取所有直接子元素（忽略文本节点）
        children = [child for child in element.children if hasattr(child, 'name') and child.name]
        
        if not children:
            return 1
        
        # 递归计算所有子元素的深度，取最大值
        max_child_depth = max(self._calculate_dom_depth(child) for child in children)
        return 1 + max_child_depth
    
    def _calculate_dom_width(self, element):
        """递归计算DOM树的最大宽度（同一层级的最大子节点数）"""
        if not element or not hasattr(element, 'name') or not element.name:
            return 0
        
        # 获取所有直接子元素（忽略文本节点）
        children = [child for child in element.children if hasattr(child, 'name') and child.name]
        current_width = len(children)
        
        # 递归计算所有子元素的最大宽度
        max_child_width = 0
        for child in children:
            child_width = self._calculate_dom_width(child)
            max_child_width = max(max_child_width, child_width)
        
        # 返回当前层级宽度和子层级最大宽度中的较大者
        return max(current_width, max_child_width)

    # 计算HTML中的链接文本与总文本比例并更新数据
    def calculate_and_update_text_linktext_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # 将比例添加到meta字段中
                data["meta"]["text_linktext_ratio"] = 0.0
                return data
                
            # 使用html.parser解析器
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取所有文本
            all_text = soup.get_text()
            all_text_len = len(all_text)
            
            if all_text_len == 0:
                data["meta"]["text_linktext_ratio"] = 0.0
                return data
            
            # 提取所有链接文本
            link_text_len = sum(len(link.get_text()) for link in soup.find_all('a'))
            
            # 计算比例 (非链接文本 / 链接文本)
            if link_text_len <= 0:
                ratio = 1.0  # 使用一个较大的值来表示无限大
            else:
                ratio = link_text_len / all_text_len
                ratio = min(float(ratio), 1.0)  # 限制最大值
            
            # 将比例添加到meta字段中
            data["meta"]["text_linktext_ratio"] = ratio
            
            # 返回更新后的数据
            return data
            
        except Exception as e:
            # 如果解析失败，至少尝试添加默认值
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["text_linktext_ratio"] = 0.0
            return data

    # 计算HTML中的非链接文本与链接数量比例并更新数据
    def calculate_and_update_text_linknum_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # 将比例添加到meta字段中
                data["meta"]["text_linknum_ratio"] = 0.0
                return data
                
            # 使用html.parser解析器
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取所有文本
            all_text = soup.get_text()
            all_text_len = len(all_text)
            
            if all_text_len == 0:
                data["meta"]["text_linknum_ratio"] = 0.0
                return data
            
            # 计算链接数量
            links = soup.find_all('a')
            link_count = len(links)
            
            # 提取链接文本总长度
            link_text_len = sum(len(link.get_text()) for link in links)
            
            # 计算非链接文本长度
            non_link_text_len = all_text_len - link_text_len
            
            # 计算比例 (非链接文本长度 / 链接数量)
            if link_count <= 0:
                ratio = 10000.0  # 使用一个较大的值来表示无限大，但不要太极端
            else:
                ratio = non_link_text_len / link_count
                ratio = min(float(ratio), 10000.0)  # 限制最大值
            
            # 将比例添加到meta字段中
            data["meta"]["text_linknum_ratio"] = ratio
            
            # 返回更新后的数据
            return data
            
        except Exception as e:
            # 如果解析失败，至少尝试添加默认值
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["text_linknum_ratio"] = 0.0
            return data

    # 计算HTML中的表格内容与总内容比例，并更新数据
    def calculate_and_update_table_html_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # 将比例添加到meta字段中
                data["meta"]["table_html_source_ratio"] = 0.0
                return data
                
            # 使用html.parser解析器
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 获取整个HTML内容的长度
            total_html_length = len(html_content)
            
            if total_html_length == 0:
                data["meta"]["table_html_source_ratio"] = 0.0
                return data
            
            # 提取所有表格元素
            tables = soup.find_all(['table'])
            
            # 计算所有表格元素的HTML长度
            table_html_length = sum(len(str(table)) for table in tables)
            
            # 计算表格内容占总HTML内容的比例
            ratio = table_html_length / total_html_length
            
            # 确保比例在0到1之间
            ratio = max(0.0, min(1.0, ratio))
            
            # 将比例添加到meta字段中
            data["meta"]["table_html_source_ratio"] = ratio
            
            # 返回更新后的数据
            return data
            
        except Exception as e:
            # 如果解析失败，至少尝试添加默认值
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table_html_source_ratio"] = 0.0
            return data

    # 计算HTML中的表格内文字与总文字比例，并更新数据
    def calculate_and_update_table_text_ratio(self, data):
        try:
            html_content = data.get("html", "")
            
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # 将比例添加到meta字段中
                data["meta"]["table_text_ratio"] = 0.0
                return data
                
            # 使用html.parser解析器
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 获取整个文档的所有文本
            all_text = soup.get_text()
            total_text_length = len(all_text)
            
            if total_text_length == 0:
                data["meta"]["table_text_ratio"] = 0.0
                return data
            
            # 提取所有表格元素
            tables = soup.find_all(['table'])
            
            # 计算所有表格内的文本长度
            table_text_length = sum(len(table.get_text()) for table in tables)
            
            # 计算表格内文字占总文字内容的比例
            ratio = table_text_length / total_text_length
            
            # 确保比例在0到1之间
            ratio = max(0.0, min(1.0, ratio))
            
            # 将比例添加到meta字段中
            data["meta"]["table_text_ratio"] = ratio
            
            # 返回更新后的数据
            return data
            
        except Exception as e:
            # 如果解析失败，至少尝试添加默认值
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table_text_ratio"] = 0.0
            return data

    # 计算HTML中第一个表格的DOM深度，并更新数据
    def calculate_and_update_table_depth(self, data):
        try:
            html_content = data.get("html", "")
            
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            if not html_content:
                # 将深度添加到meta字段中，-1表示没有表格
                data["meta"]["table_dom_depth"] = -1
                return data
                
            # 使用html.parser解析器
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找第一个表格元素
            first_table = soup.find('table')
            
            # 如果没有找到表格
            if not first_table:
                data["meta"]["table_dom_depth"] = -1
                return data
            
            # 计算表格的DOM深度
            depth = 0
            parent = first_table.parent
            while parent and parent.name != '[document]':
                depth += 1
                parent = parent.parent
            
            # 将深度添加到meta字段中
            data["meta"]["table_dom_depth"] = depth
            
            # 返回更新后的数据
            return data
            
        except Exception as e:
            # 如果解析失败，至少尝试添加默认值
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table_dom_depth"] = -1
            return data
    
    # 检测HTML中包含的公式类型
    def detect_equations(self, data: dict) -> dict:
        """检测并标记页面中的公式类型，返回meta.equation字段作为字符串列表"""
        try:
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            # 初始化equation列表
            equation_types = []
            
            # 检查是否有content_list字段
            if 'content_list' not in data:
                data["meta"]["equation"] = equation_types
                return data
            
            # 获取content_list的JSON文本
            text = ContentList(data['content_list']).to_json()
            
            # 检测行内公式
            inline_matches = re.findall("equation-inline", text)
            if len(inline_matches) > 0:
                equation_types.append("inline")
            
            # 检测行间公式
            interline_matches = re.findall("equation-interline", text)
            if len(interline_matches) > 0:
                equation_types.append("interline")
            
            # 将结果存储到meta.equation字段
            data["meta"]["equation"] = equation_types
            
            return data
            
        except Exception as e:
            # 如果解析失败，返回空列表
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["equation"] = []
            return data

    # 检测HTML中包含的代码类型
    def detect_code(self, data: dict) -> dict:
        """检测并标记页面中的代码类型，返回meta.code字段作为字符串列表"""
        try:
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            # 初始化equation列表
            code_types = []
            
            # 检查是否有content_list字段
            if 'content_list' not in data:
                data["meta"]["code"] = code_types
                return data
            
            # 获取content_list的JSON文本
            text = ContentList(data['content_list']).to_json()
            
            # 检测行内公式
            inline_matches = re.findall("code-inline", text)
            if len(inline_matches) > 0:
                code_types.append("inline")
            
            # 检测行间公式
            target_str = r'"type": "code"'
            interline_matches = re.findall(target_str, text)
            if len(interline_matches) > 0:
                code_types.append("interline")
            
            # 将结果存储到meta.code字段
            data["meta"]["code"] = code_types
            
            return data
            
        except Exception as e:
            # 如果解析失败，返回空列表
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["code"] = []
            return data

    def classify_tables(self, data):
        """根据DOM深度和其他特征分类表格类型"""
        try:
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            # 初始化table类型列表
            table_types = []
            
            # 获取表格相关的meta信息
            table_dom_depth = data["meta"].get("table_dom_depth", -1)
            table_text_ratio = data["meta"].get("table_text_ratio", 0)
            table_html_ratio = data["meta"].get("table_html_source_ratio", 0)
            
            # 如果没有表格，返回空列表
            if table_dom_depth == -1:
                data["meta"]["table"] = table_types
                return data
            
            # 基于DOM深度和内容比例判断表格类型
            
            # Layout表格判断逻辑：
            # 1. DOM深度较浅（通常用于页面布局）
            # 2. 表格HTML占比高但文本占比低（主要是结构性标签）
            if (table_dom_depth <= 3 and table_html_ratio > 0.1 and table_text_ratio < 0.3) or \
               (table_dom_depth <= 2):
                table_types.append("layout")
            
            # Data表格判断逻辑：
            # 1. DOM深度较深（嵌套在内容区域）
            # 2. 表格文本占比较高（包含实际数据内容）
            # 3. 或者表格HTML占比适中但文本占比高
            if (table_dom_depth >= 3 and table_text_ratio >= 0.1) or \
               (table_text_ratio >= 0.3) or \
               (table_html_ratio > 0.05 and table_text_ratio >= 0.15):
                table_types.append("data")
            
            # 如果没有匹配任何类型，但确实有表格，默认为data类型
            if not table_types and table_dom_depth > -1:
                table_types.append("data")
            
            # 去重并排序
            table_types = sorted(list(set(table_types)))
            
            data["meta"]["table"] = table_types
            return data
            
        except Exception as e:
            # 如果解析失败，返回空列表
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["table"] = []
            return data

    # 计算text文本在DOM一维序列中的分布离散程度
    def calculate_text_DOM_distribution(self, data):
        """将DOM树线性化，计算文本分布的离散程度"""
        try:
            # 确保meta字段存在
            if "meta" not in data:
                data["meta"] = {}
            
            html_content = data.get("html", "")
            if not html_content:
                data["meta"]["text_distribution_dispersion"] = 0.0
                return data
            
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 将DOM树线性化为一维列表
            dom_sequence = self._linearize_dom_tree(soup)
            
            if not dom_sequence:
                data["meta"]["text_distribution_dispersion"] = 0.0
                return data
            
            # 找到所有文本节点在序列中的位置
            text_positions = []
            for i, node_info in enumerate(dom_sequence):
                if node_info['has_text']:
                    text_positions.append({
                        'position': i,
                        'text_length': node_info['text_length'],
                        'relative_position': i / len(dom_sequence)  # 相对位置 0-1
                    })
            
            if not text_positions:
                data["meta"]["text_distribution_dispersion"] = 0.0
                return data
            
            # 计算文本分布的离散程度
            dispersion = self._calculate_text_dispersion(text_positions, len(dom_sequence))
            
            data["meta"]["text_distribution_dispersion"] = dispersion
            
            return data
            
        except Exception as e:
            # 如果解析失败，返回默认值
            if "meta" not in data:
                data["meta"] = {}
            data["meta"]["text_distribution_dispersion"] = 0.0
            return data
    
    def _linearize_dom_tree(self, soup):
        """将DOM树线性化为一维序列（深度优先遍历）"""
        dom_sequence = []
        
        def traverse(element):
            if not element or not hasattr(element, 'name'):
                return
            
            # 跳过document节点
            if element.name == '[document]':
                # 处理根节点的子元素
                if hasattr(element, 'children'):
                    for child in element.children:
                        if hasattr(child, 'name') and child.name:
                            traverse(child)
                return
            
            # 处理当前元素 - 只获取直接文本内容
            text_content = ""
            text_length = 0
            has_text = False
            
            # 只收集元素的直接文本内容（不包括子元素的文本）
            if hasattr(element, 'contents'):
                for content in element.contents:
                    # 只处理直接的文本节点，跳过子元素
                    if isinstance(content, str) and content.strip():
                        text_content += content.strip() + " "
                        
            text_length = len(text_content.strip())
            has_text = text_length > 0
            
            # 添加到序列中
            node_info = {
                'tag': element.name,
                'has_text': has_text,
                'text_length': text_length,
                'text_content': text_content.strip()[:100] if has_text else ""  # 截取前100字符
            }
            dom_sequence.append(node_info)
            
            # 递归处理子元素
            if hasattr(element, 'children'):
                for child in element.children:
                    if hasattr(child, 'name') and child.name:
                        traverse(child)
        
        # 开始遍历
        traverse(soup)
        return dom_sequence
    
    def _calculate_text_dispersion(self, text_positions, total_nodes):
        """计算文本在一维序列中的分布离散程度 - 基于状态翻转次数"""
        if total_nodes < 2:
            return 0.0
        
        # 创建文本状态序列：1表示有文本，0表示无文本
        text_states = [0] * total_nodes
        for pos_info in text_positions:
            text_states[pos_info['position']] = 1
        
        # 计算状态翻转次数 (0->1 或 1->0)
        flips = 0
        for i in range(1, len(text_states)):
            if text_states[i] != text_states[i-1]:
                flips += 1
        
        # 归一化：翻转次数除以总节点数量
        dispersion_score = flips / total_nodes
        
        return round(dispersion_score, 4)

    def calculate_level_score(self, data):
        """计算页面内容难易程度评分"""
        # 确保meta字段存在
        if "meta" not in data:
            data["meta"] = {}
        
        meta = data["meta"]
        
        # 收集各项复杂度指标
        complexity_score = 0.0
        
        # 1. 表格复杂度
        table_text_ratio = meta.get("table_text_ratio", 0)
        table_complexity = min(table_text_ratio, 1.0)  # 归一化到0-1
        # complexity_score += 0.20 * table_complexity
        data["meta"]["table_complexity_score"] = round(table_complexity, 4) 
        
        # 2. DOM结构复杂度
        dom_depth = meta.get("DOM_DEPTH", 0)
        dom_width = meta.get("DOM_WIDTH", 0)
        # 基于实际数据分布调整归一化参数：
        # - 深度90%分位数约104，使用120作为归一化基准
        # - 宽度90%分位数约1283，使用1500作为归一化基准
        # - 使用平方根函数降低高值的影响，提供更好的区分度
        depth_norm = min(dom_depth / 20, 1.0) ** 0.7  # 使用0.7次幂平滑曲线
        width_norm = min(dom_width / 300, 1.0) ** 0.7
        dom_complexity = (depth_norm + width_norm) / 2  # 取平均值
        complexity_score += 0.25 * dom_complexity
        data["meta"]["dom_complexity_score"] = round(dom_complexity, 4) 
        
        # 3. 文本分布离散程度
        text_distribution_dispersion = meta.get("text_distribution_dispersion", 0)
        
        # 文本分布复杂度评分（简化版）
        text_dispersion_score = min(text_distribution_dispersion, 1.0)  # 归一化到0-1
        complexity_score += 0.25 * text_dispersion_score
        data["meta"]["text_dispersion_score"] = round(text_dispersion_score, 4) 

        # 4. 内容类型多样性
        content_diversity = 0.0
        equation_types = meta.get("equation", [])
        code_types = meta.get("code", [])
        table_types = meta.get("table", [])
        
        # 根据内容类型数量评分
        if equation_types:
            content_diversity += 0.3 * len(equation_types) / 2  # 最多2种公式类型
        if code_types:
            content_diversity += 0.3 * len(code_types) / 2      # 最多2种代码类型
        if table_types:
            content_diversity += 0.4 * len(table_types) / 2     # 最多2种表格类型
        
        content_diversity = min(content_diversity, 1.0)
        complexity_score += 0.25 * content_diversity
        data["meta"]["content_diversity_score"] = round(content_diversity, 4) 
        
        # 5. 链接文本比例
        text_linktext_ratio = meta.get("text_linktext_ratio", 0)
        # 链接比例过高或过低都可能增加复杂度
        link_complexity = min(text_linktext_ratio, 1.0)
        complexity_score += 0.25 * link_complexity
        data["meta"]["link_complexity_score"] = round(link_complexity, 4) 
        
        data["meta"]["overall_complexity_score"] = round(complexity_score, 4)  # 保存综合评分便于分析
      
        return data

    def calculate_level(self, data, threshold_30=None, threshold_70=None):
        """基于动态阈值计算页面内容难易程度:simple, mid, hard"""
        # 如果没有提供阈值，使用默认阈值
        if threshold_30 is None or threshold_70 is None:
            threshold_30 = 0.35
            threshold_70 = 0.65
        
        complexity_score = data["meta"]["overall_complexity_score"]
        if complexity_score >= threshold_70:
            level = 'hard'
        elif complexity_score >= threshold_30:
            level = 'mid'
        else:
            level = 'simple'
        data["meta"]["level"] = level
        return data
    
    def _calculate_dynamic_thresholds(self):
        """基于overall_complexity_score分布计算动态阈值"""
        complexity_scores = []
        for data in self.data:
            if "meta" in data and "overall_complexity_score" in data["meta"]:
                complexity_scores.append(data["meta"]["overall_complexity_score"])
        
        if not complexity_scores:
            print("⚠️  警告: 没有找到overall_complexity_score数据，使用默认阈值")
            return 0.35, 0.65  # 返回默认阈值
        
        # 排序并计算分位数
        complexity_scores.sort()
        n = len(complexity_scores)
        
        # 计算30%和70%分位数
        percentile_30_idx = int(n * 0.3)
        percentile_70_idx = int(n * 0.7)
        
        # 确保索引在有效范围内
        percentile_30_idx = min(percentile_30_idx, n - 1)
        percentile_70_idx = min(percentile_70_idx, n - 1)
        
        threshold_30 = complexity_scores[percentile_30_idx]
        threshold_70 = complexity_scores[percentile_70_idx]
        
        print(f"📊 复杂度分布阈值计算:")
        print(f"   总样本数: {n:,}")
        print(f"   30%分位数 (simple/mid分界): {threshold_30:.4f}")
        print(f"   70%分位数 (mid/hard分界): {threshold_70:.4f}")
        print(f"   复杂度得分范围: {min(complexity_scores):.4f} - {max(complexity_scores):.4f}")
        
        return threshold_30, threshold_70
    
    def _print_level_distribution(self):
        """统计并打印难易程度分类结果"""
        simple_count = mid_count = hard_count = 0
        for data in self.data:
            level = data.get("meta", {}).get("level", "unknown")
            if level == "simple":
                simple_count += 1
            elif level == "mid":
                mid_count += 1
            elif level == "hard":
                hard_count += 1
        
        total = len(self.data)
        print(f"📊 难易程度分类结果:")
        print(f"   Simple: {simple_count:,} ({simple_count/total*100:.1f}%)")
        print(f"   Mid:    {mid_count:,} ({mid_count/total*100:.1f}%)")
        print(f"   Hard:   {hard_count:,} ({hard_count/total*100:.1f}%)")

    def update_data(self):
        """更新数据中的统计信息"""
        print("🔄 第一阶段: 计算基础统计和复杂度得分...")
        
        # 第一阶段：计算所有基础统计信息和复杂度得分
        for i, data in enumerate(self.data):
            # 直接在原始数据上追加字段
            self.generate_content_list(data)
            self.calculate_DOM_WIDTH_DEPTH(data)  # DOM结构分析
            self.calculate_and_update_text_linktext_ratio(data)
            # self.calculate_and_update_text_linknum_ratio(data)
            # self.calculate_and_update_table_html_ratio(data)
            self.calculate_and_update_table_text_ratio(data)
            self.calculate_and_update_table_depth(data)
            self.classify_tables(data)  # 表格分类需要在表格相关统计之后
            self.calculate_text_DOM_distribution(data)  # 文本DOM分布分析
            self.detect_equations(data)
            self.detect_code(data)
            self.calculate_level_score(data)  # 只计算复杂度得分，不分类

            # 显示进度
            if (i + 1) % 100 == 0:
                print(f"  📊 已处理 {i + 1:,} 条数据...")
        
        print("🔄 第二阶段: 计算动态阈值和难易程度分类...")
        
        # 第二阶段：基于所有复杂度得分计算动态阈值
        threshold_30, threshold_70 = self._calculate_dynamic_thresholds()
        
        # 第三阶段：应用动态阈值进行难易程度分类
        for data in self.data:
            self.calculate_level(data, threshold_30, threshold_70)
        
        # 统计最终的分类结果
        self._print_level_distribution()
    
    def write_data(self):
        """写入数据"""
        print(f"📝 正在写入数据到: {self.output_file}")
        with open(self.output_file, "w", encoding="utf-8") as f:
            for data in self.data:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"✅ 成功写入 {len(self.data):,} 条数据")
    
    def calculate_meta_statistics(self):
        """计算meta字段的统计信息"""
        if not self.data:
            return {}
        
        stats = {
            'total_count': len(self.data),
            'numerical_stats': {},
            'categorical_stats': {},
            'correlation_stats': {}
        }
        
        # 数值型字段统计
        numerical_fields = [
            'text_linktext_ratio', 'text_linknum_ratio', 
            'table_html_source_ratio', 'table_text_ratio', 'table_dom_depth',
            'DOM_WIDTH', 'DOM_DEPTH',
            'text_distribution_dispersion',
            'table_complexity_score',
            'dom_complexity_score',
            'text_dispersion_score',
            'content_diversity_score',
            'link_complexity_score',
            'overall_complexity_score'
        ]
        
        for field in numerical_fields:
            values = []
            for data in self.data:
                if 'meta' in data and field in data['meta']:
                    value = data['meta'][field]
                    if isinstance(value, (int, float)) and value != -1:  # 排除-1这种特殊值
                        values.append(value)
            
            if values:
                stats['numerical_stats'][field] = {
                    'count': len(values),
                    'mean': sum(values) / len(values),
                    'median': sorted(values)[len(values)//2],
                    'min': min(values),
                    'max': max(values),
                    'std': (sum((x - sum(values)/len(values))**2 for x in values) / len(values))**0.5
                }
        
        # 分类型字段统计 - equation
        equation_combinations = {}
        for data in self.data:
            if 'meta' in data and 'equation' in data['meta']:
                eq_list = data['meta']['equation']
                eq_key = ','.join(sorted(eq_list)) if eq_list else 'none'
                equation_combinations[eq_key] = equation_combinations.get(eq_key, 0) + 1
        
        stats['categorical_stats']['equation'] = equation_combinations
        
        # 分类型字段统计 - code
        code_combinations = {}
        for data in self.data:
            if 'meta' in data and 'code' in data['meta']:
                code_list = data['meta']['code']
                code_key = ','.join(sorted(code_list)) if code_list else 'none'
                code_combinations[code_key] = code_combinations.get(code_key, 0) + 1
        
        stats['categorical_stats']['code'] = code_combinations

        # 分类型字段统计 - level
        level_combinations = {}
        for data in self.data:
            if 'meta' in data and 'level' in data['meta']:
                level_value = data['meta']['level']
                # level是字符串，直接使用
                level_key = level_value if level_value else 'none'
                level_combinations[level_key] = level_combinations.get(level_key, 0) + 1
        stats['categorical_stats']['level'] = level_combinations
        
        # 分类型字段统计 - table
        table_combinations = {}
        for data in self.data:
            if 'meta' in data and 'table' in data['meta']:
                table_list = data['meta']['table']
                table_key = ','.join(sorted(table_list)) if table_list else 'none'
                table_combinations[table_key] = table_combinations.get(table_key, 0) + 1
        stats['categorical_stats']['table_types'] = table_combinations

        # 交叉统计 - equation和code的组合
        equation_code_cross = {}
        for data in self.data:
            if 'meta' in data:
                eq_list = data['meta'].get('equation', [])
                code_list = data['meta'].get('code', [])
                eq_key = ','.join(sorted(eq_list)) if eq_list else 'none'
                code_key = ','.join(sorted(code_list)) if code_list else 'none'
                cross_key = f"eq:{eq_key}|code:{code_key}"
                equation_code_cross[cross_key] = equation_code_cross.get(cross_key, 0) + 1
        
        stats['correlation_stats']['equation_code_cross'] = equation_code_cross
        
        # 表格相关统计
        table_stats = {
            'has_table': 0,
            'no_table': 0,
            'high_table_ratio': 0  # table_text_ratio > 0.5
        }
        
        for data in self.data:
            if 'meta' in data:
                table_depth = data['meta'].get('table_dom_depth', -1)
                table_text_ratio = data['meta'].get('table_text_ratio', 0)
                
                if table_depth > -1:
                    table_stats['has_table'] += 1
                    if table_text_ratio > 0.5:
                        table_stats['high_table_ratio'] += 1
                else:
                    table_stats['no_table'] += 1
        
        stats['categorical_stats']['table'] = table_stats
        
        self.stats = stats
        return stats

    def print_summary(self):
        """打印统计摘要"""
        print("\n" + "=" * 80)
        print("📊 WebMainBench 数据集统计摘要")
        print("=" * 80)
        print(f"📄 总数据条数: {len(self.data):,}")
        
        if hasattr(self, 'stats') and self.stats:
            stats = self.stats
            
            # 数值型字段统计
            print(f"\n📈 数值型字段统计:")
            print("-" * 60)
            for field, field_stats in stats['numerical_stats'].items():
                print(f"  {field}:")
                print(f"    样本数: {field_stats['count']:,}")
                print(f"    均值: {field_stats['mean']:.4f}")
                print(f"    中位数: {field_stats['median']:.4f}")
                print(f"    最小值: {field_stats['min']:.4f}")
                print(f"    最大值: {field_stats['max']:.4f}")
                print(f"    标准差: {field_stats['std']:.4f}")
                print()
            
            # 公式类型分布
            print(f"📐 公式类型分布:")
            print("-" * 60)
            equation_stats = stats['categorical_stats'].get('equation', {})
            total_with_meta = sum(equation_stats.values())
            for eq_type, count in sorted(equation_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {eq_type}: {count:,} ({percentage:.1f}%)")
            
            # 代码类型分布
            print(f"\n💻 代码类型分布:")
            print("-" * 60)
            code_stats = stats['categorical_stats'].get('code', {})
            total_with_meta = sum(code_stats.values())
            for code_type, count in sorted(code_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {code_type}: {count:,} ({percentage:.1f}%)")
            
            # 表格统计
            print(f"\n📋 表格统计:")
            print("-" * 60)
            table_stats = stats['categorical_stats'].get('table', {})
            total = table_stats.get('has_table', 0) + table_stats.get('no_table', 0)
            if total > 0:
                print(f"  包含表格: {table_stats.get('has_table', 0):,} ({table_stats.get('has_table', 0)/total*100:.1f}%)")
                print(f"  无表格: {table_stats.get('no_table', 0):,} ({table_stats.get('no_table', 0)/total*100:.1f}%)")
                print(f"  高表格内容比例(>50%): {table_stats.get('high_table_ratio', 0):,}")
            
            # 表格类型分布
            print(f"\n📊 表格类型分布:")
            print("-" * 60)
            table_type_stats = stats['categorical_stats'].get('table_types', {})
            total_with_meta = sum(table_type_stats.values())
            for table_type, count in sorted(table_type_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {table_type}: {count:,} ({percentage:.1f}%)")
            
            # 难易程度分布
            print(f"\n🔍 难易程度分布:")
            print("-" * 60)
            level_stats = stats['categorical_stats'].get('level', {})
            total_with_meta = sum(level_stats.values())
            for level, count in sorted(level_stats.items()):
                percentage = (count / total_with_meta * 100) if total_with_meta > 0 else 0
                print(f"  {level}: {count:,} ({percentage:.1f}%)")
            
            # 公式和代码交叉统计（显示前10个最常见的组合）
            print(f"\n🔗 公式-代码组合分布 (Top 10):")
            print("-" * 60)
            cross_stats = stats['correlation_stats'].get('equation_code_cross', {})
            sorted_cross = sorted(cross_stats.items(), key=lambda x: x[1], reverse=True)[:10]
            for combo, count in sorted_cross:
                percentage = (count / len(self.data) * 100) if len(self.data) > 0 else 0
                print(f"  {combo}: {count:,} ({percentage:.1f}%)")
        
        print("\n" + "=" * 80)
        

    

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据集统计和筛选工具")
    # data/sample_dataset.jsonl
    # data/WebMainBench_1827_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl
    parser.add_argument("input_file", nargs='?', 
                       default="data/WebMainBench_1827_v1_WebMainBench_dataset_merge_with_llm_webkit.jsonl",
                       help="输入JSONL文件路径")
    parser.add_argument("--output", default="data/sample_dataset_with_stats.jsonl", type=str, help="输出文件路径")

    args = parser.parse_args()
    
    print("🔍 数据集统计和筛选工具")
    print("="*60)
    
    try:
        # 初始化和加载数据
        stats_tool = DatasetStatistics(args.input_file, args.output)       
        stats_tool.load_data()
        
        # 计算统计信息
        stats_tool.update_data()

        # 计算meta字段统计
        stats_tool.calculate_meta_statistics()
            
        # 显示统计摘要
        stats_tool.print_summary()
        
        # 写入数据
        stats_tool.write_data()
        
        print(f"\n🎉 任务完成!")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
 