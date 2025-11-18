#!/usr/bin/env python3
"""
域名分布统计脚本
统计数据集中的域名分布、TLD分布、以及域名与meta信息的关系

使用方法:
    python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl
"""

import json
import argparse
from collections import Counter, defaultdict
from urllib.parse import urlparse
from pathlib import Path
import csv


class DomainStatsAnalyzer:
    """域名统计分析器"""
    
    def __init__(self, input_file):
        self.input_file = input_file
        self.data = []
        self.domain_counter = Counter()
        self.tld_counter = Counter()
        self.domain_meta = defaultdict(lambda: {
            'languages': Counter(),
            'styles': Counter(),
            'levels': Counter(),
            'has_table': 0,
            'has_code': 0,
            'has_equation': 0,
            'count': 0
        })
        
    def load_data(self):
        """加载JSONL数据"""
        print(f"加载数据: {self.input_file}")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    self.data.append(item)
        print(f"已加载 {len(self.data)} 条数据\n")
    
    def extract_domain(self, url):
        """从URL提取域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return None
    
    def extract_tld(self, domain):
        """提取顶级域名"""
        if domain and '.' in domain:
            return domain.split('.')[-1]
        return None
    
    def analyze(self):
        """执行分析"""
        print("="*60)
        print("开始分析域名分布")
        print("="*60 + "\n")
        
        for item in self.data:
            url = item.get('url', '')
            domain = self.extract_domain(url)
            
            if not domain:
                continue
            
            # 统计域名
            self.domain_counter[domain] += 1
            
            # 统计TLD
            tld = self.extract_tld(domain)
            if tld:
                self.tld_counter[tld] += 1
            
            # 统计域名的meta信息
            meta = item.get('meta', {})
            self.domain_meta[domain]['count'] += 1
            self.domain_meta[domain]['languages'][meta.get('language', 'unknown')] += 1
            self.domain_meta[domain]['styles'][meta.get('style', 'unknown')] += 1
            self.domain_meta[domain]['levels'][meta.get('level', 'unknown')] += 1
            
            if meta.get('table'):
                self.domain_meta[domain]['has_table'] += 1
            if meta.get('code'):
                self.domain_meta[domain]['has_code'] += 1
            if meta.get('equation'):
                self.domain_meta[domain]['has_equation'] += 1
    
    def print_basic_stats(self):
        """打印基本统计信息"""
        print("="*60)
        print("1. 基本统计")
        print("="*60)
        
        total_samples = len(self.data)
        unique_domains = len(self.domain_counter)
        
        print(f"总样本数: {total_samples}")
        print(f"独立域名数: {unique_domains}")
        print(f"平均每域名样本数: {total_samples/unique_domains:.2f}")
        
        # 域名样本数分布
        samples_per_domain = list(self.domain_counter.values())
        print(f"\n每域名样本数统计:")
        print(f"  最小值: {min(samples_per_domain)}")
        print(f"  最大值: {max(samples_per_domain)}")
        print(f"  平均值: {sum(samples_per_domain)/len(samples_per_domain):.2f}")
        print(f"  中位数: {sorted(samples_per_domain)[len(samples_per_domain)//2]}")
        
        # 单样本域名占比
        single_sample_domains = sum(1 for count in samples_per_domain if count == 1)
        print(f"\n只有1个样本的域名: {single_sample_domains} ({single_sample_domains/unique_domains*100:.1f}%)")
        print()
    
    def print_tld_distribution(self):
        """打印TLD分布"""
        print("="*60)
        print("2. 顶级域名(TLD)分布")
        print("="*60)
        
        total = sum(self.tld_counter.values())
        print(f"\n总共 {len(self.tld_counter)} 种TLD\n")
        
        for tld, count in self.tld_counter.most_common(20):
            percentage = count / total * 100
            bar = '█' * int(percentage / 2)
            print(f"  .{tld:15} {count:5} ({percentage:5.2f}%) {bar}")
        
        if len(self.tld_counter) > 20:
            print(f"\n  ... 还有 {len(self.tld_counter) - 20} 种TLD")
        print()
    
    def print_top_domains(self, n=30):
        """打印热门域名"""
        print("="*60)
        print(f"3. Top {n} 域名")
        print("="*60 + "\n")
        
        total = sum(self.domain_counter.values())
        
        for i, (domain, count) in enumerate(self.domain_counter.most_common(n), 1):
            percentage = count / total * 100
            print(f"{i:3}. {domain:50} {count:5} ({percentage:5.2f}%)")
        print()
    
    def print_domain_meta_analysis(self):
        """打印域名的meta信息分析"""
        print("="*60)
        print("4. 域名与内容类型分析")
        print("="*60 + "\n")
        
        # 找出包含特殊内容最多的域名
        domains_with_table = [(d, info['has_table']) for d, info in self.domain_meta.items() if info['has_table'] > 0]
        domains_with_code = [(d, info['has_code']) for d, info in self.domain_meta.items() if info['has_code'] > 0]
        domains_with_equation = [(d, info['has_equation']) for d, info in self.domain_meta.items() if info['has_equation'] > 0]
        
        print(f"包含表格的域名数: {len(domains_with_table)}")
        if domains_with_table:
            print("  Top 10 域名(按表格数量):")
            for domain, count in sorted(domains_with_table, key=lambda x: -x[1])[:10]:
                print(f"    {domain:50} {count} 个样本")
        
        print(f"\n包含代码的域名数: {len(domains_with_code)}")
        if domains_with_code:
            print("  Top 10 域名(按代码数量):")
            for domain, count in sorted(domains_with_code, key=lambda x: -x[1])[:10]:
                print(f"    {domain:50} {count} 个样本")
        
        print(f"\n包含公式的域名数: {len(domains_with_equation)}")
        if domains_with_equation:
            print("  Top 10 域名(按公式数量):")
            for domain, count in sorted(domains_with_equation, key=lambda x: -x[1])[:10]:
                print(f"    {domain:50} {count} 个样本")
        print()
    
    def print_language_by_tld(self):
        """打印TLD的语言分布"""
        print("="*60)
        print("5. TLD与语言分布")
        print("="*60 + "\n")
        
        tld_languages = defaultdict(Counter)
        
        for domain, info in self.domain_meta.items():
            tld = self.extract_tld(domain)
            if tld:
                for lang, count in info['languages'].items():
                    tld_languages[tld][lang] += count
        
        # 显示主要TLD的语言分布
        for tld, lang_counter in sorted(tld_languages.items(), 
                                       key=lambda x: sum(x[1].values()), 
                                       reverse=True)[:10]:
            total = sum(lang_counter.values())
            print(f".{tld} (共{total}个样本):")
            for lang, count in lang_counter.most_common(3):
                print(f"  {lang:15} {count:4} ({count/total*100:5.1f}%)")
            print()
    
    def save_reports(self, output_dir='results'):
        """保存统计报告"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存域名统计CSV
        domain_csv = output_path / 'domain_statistics.csv'
        with open(domain_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Domain', 'Sample_Count', 'Percentage',
                'Top_Language', 'Top_Style', 'Top_Level',
                'Has_Table', 'Has_Code', 'Has_Equation'
            ])
            
            total = sum(self.domain_counter.values())
            for domain, count in self.domain_counter.most_common():
                info = self.domain_meta[domain]
                top_lang = info['languages'].most_common(1)[0][0] if info['languages'] else 'unknown'
                top_style = info['styles'].most_common(1)[0][0] if info['styles'] else 'unknown'
                top_level = info['levels'].most_common(1)[0][0] if info['levels'] else 'unknown'
                
                writer.writerow([
                    domain,
                    count,
                    f"{count/total*100:.2f}%",
                    top_lang,
                    top_style,
                    top_level,
                    info['has_table'],
                    info['has_code'],
                    info['has_equation']
                ])
        
        print(f"✓ 域名统计CSV已保存: {domain_csv}")
        
        # 保存TLD统计CSV
        tld_csv = output_path / 'tld_statistics.csv'
        with open(tld_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['TLD', 'Count', 'Percentage'])
            
            total = sum(self.tld_counter.values())
            for tld, count in self.tld_counter.most_common():
                writer.writerow([
                    tld,
                    count,
                    f"{count/total*100:.2f}%"
                ])
        
        print(f"✓ TLD统计CSV已保存: {tld_csv}")
        
        # 保存域名列表
        domains_txt = output_path / 'unique_domains.txt'
        with open(domains_txt, 'w', encoding='utf-8') as f:
            for domain in sorted(self.domain_counter.keys()):
                f.write(f"{domain}\n")
        
        print(f"✓ 域名列表已保存: {domains_txt}")
        
        # 保存JSON格式的详细统计
        stats_json = output_path / 'domain_stats.json'
        stats_data = {
            'summary': {
                'total_samples': len(self.data),
                'unique_domains': len(self.domain_counter),
                'unique_tlds': len(self.tld_counter)
            },
            'tld_distribution': dict(self.tld_counter),
            'top_50_domains': dict(self.domain_counter.most_common(50))
        }
        
        with open(stats_json, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON统计已保存: {stats_json}")
        print()
    
    def run(self, output_dir='results'):
        """执行完整分析流程"""
        self.load_data()
        self.analyze()
        self.print_basic_stats()
        self.print_tld_distribution()
        self.print_top_domains()
        self.print_domain_meta_analysis()
        self.print_language_by_tld()
        
        print("="*60)
        print("保存统计报告")
        print("="*60 + "\n")
        self.save_reports(output_dir)
        
        print("="*60)
        print("域名统计分析完成！")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='统计数据集中的域名分布信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl
  
  python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl \\
    --output-dir results/domain_analysis
        '''
    )
    
    parser.add_argument(
        'input_file',
        help='输入的JSONL文件路径'
    )
    
    parser.add_argument(
        '--output-dir',
        default='results',
        help='输出目录 (默认: results)'
    )
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not Path(args.input_file).exists():
        print(f"错误: 文件不存在: {args.input_file}")
        return 1
    
    # 执行分析
    analyzer = DomainStatsAnalyzer(args.input_file)
    analyzer.run(args.output_dir)
    
    return 0


if __name__ == '__main__':
    exit(main())

