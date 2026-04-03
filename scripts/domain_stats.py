#!/usr/bin/env python3
"""
Domain distribution statistics script
Analyzes domain distribution, TLD distribution, and the relationship between domains and meta information in the dataset

Usage:
    python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl
"""

import json
import argparse
from collections import Counter, defaultdict
from urllib.parse import urlparse
from pathlib import Path
import csv


class DomainStatsAnalyzer:
    """Domain statistics analyzer"""
    
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
        """Load JSONL data."""
        print(f"Loading data: {self.input_file}")
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    self.data.append(item)
print(f"Loaded {len(self.data)} records\n")
    
    def extract_domain(self, url):
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return None
    
    def extract_tld(self, domain):
        """Extract top-level domain."""
        if domain and '.' in domain:
            return domain.split('.')[-1]
        return None
    
    def analyze(self):
        """Run analysis."""
        print("="*60)
        print("Starting domain distribution analysis")
        print("="*60 + "\n")
        
        for item in self.data:
            url = item.get('url', '')
            domain = self.extract_domain(url)
            
            if not domain:
                continue
            
            # Count domains
            self.domain_counter[domain] += 1
            
            # Count TLDs
            tld = self.extract_tld(domain)
            if tld:
                self.tld_counter[tld] += 1
            
            # Count meta information for domains
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
        """Print basic statistics."""
        print("="*60)
        print("1. Basic Statistics")
        print("="*60)
        
        total_samples = len(self.data)
        unique_domains = len(self.domain_counter)
        
print(f"Total samples: {total_samples}")
print(f"Unique domains: {unique_domains}")
print(f"Average samples per domain: {total_samples/unique_domains:.2f}")
        
        # Domain sample count distribution
        samples_per_domain = list(self.domain_counter.values())
print(f"\nSamples per domain statistics:")
print(f"  Min: {min(samples_per_domain)}")
print(f"  Max: {max(samples_per_domain)}")
print(f"  Mean: {sum(samples_per_domain)/len(samples_per_domain):.2f}")
print(f"  Median: {sorted(samples_per_domain)[len(samples_per_domain)//2]}")
        
        # Single-sample domain ratio
        single_sample_domains = sum(1 for count in samples_per_domain if count == 1)
print(f"\nDomains with only 1 sample: {single_sample_domains} ({single_sample_domains/unique_domains*100:.1f}%)")
        print()
    
    def print_tld_distribution(self):
        """Print TLD distribution."""
        print("="*60)
        print("2. Top-Level Domain (TLD) Distribution")
        print("="*60)
        
        total = sum(self.tld_counter.values())
print(f"\nTotal of {len(self.tld_counter)} TLD types\n")
        
        for tld, count in self.tld_counter.most_common(20):
            percentage = count / total * 100
            bar = '█' * int(percentage / 2)
            print(f"  .{tld:15} {count:5} ({percentage:5.2f}%) {bar}")
        
        if len(self.tld_counter) > 20:
            print(f"\n  ... and {len(self.tld_counter) - 20} more TLD types")
        print()
    
    def print_top_domains(self, n=30):
        """Print top domains."""
        print("="*60)
        print(f"3. Top {n} Domains")
        print("="*60 + "\n")
        
        total = sum(self.domain_counter.values())
        
        for i, (domain, count) in enumerate(self.domain_counter.most_common(n), 1):
            percentage = count / total * 100
            print(f"{i:3}. {domain:50} {count:5} ({percentage:5.2f}%)")
        print()
    
    def print_domain_meta_analysis(self):
        """Print domain meta information analysis."""
        print("="*60)
        print("4. Domain and Content Type Analysis")
        print("="*60 + "\n")
        
        # Find domains with the most special content
        domains_with_table = [(d, info['has_table']) for d, info in self.domain_meta.items() if info['has_table'] > 0]
        domains_with_code = [(d, info['has_code']) for d, info in self.domain_meta.items() if info['has_code'] > 0]
        domains_with_equation = [(d, info['has_equation']) for d, info in self.domain_meta.items() if info['has_equation'] > 0]
        
print(f"Domains with tables: {len(domains_with_table)}")
        if domains_with_table:
print("  Top 10 domains (by table count):")
            for domain, count in sorted(domains_with_table, key=lambda x: -x[1])[:10]:
print(f"    {domain:50} {count} samples")
        
print(f"\nDomains with code: {len(domains_with_code)}")
        if domains_with_code:
print("  Top 10 domains (by code count):")
            for domain, count in sorted(domains_with_code, key=lambda x: -x[1])[:10]:
print(f"    {domain:50} {count} samples")
        
print(f"\nDomains with equations: {len(domains_with_equation)}")
        if domains_with_equation:
print("  Top 10 domains (by equation count):")
            for domain, count in sorted(domains_with_equation, key=lambda x: -x[1])[:10]:
print(f"    {domain:50} {count} samples")
        print()
    
    def print_language_by_tld(self):
        """Print language distribution by TLD."""
        print("="*60)
        print("5. TLD and Language Distribution")
        print("="*60 + "\n")
        
        tld_languages = defaultdict(Counter)
        
        for domain, info in self.domain_meta.items():
            tld = self.extract_tld(domain)
            if tld:
                for lang, count in info['languages'].items():
                    tld_languages[tld][lang] += count
        
        # Display language distribution for major TLDs
        for tld, lang_counter in sorted(tld_languages.items(), 
                                       key=lambda x: sum(x[1].values()), 
                                       reverse=True)[:10]:
            total = sum(lang_counter.values())
print(f".{tld} ({total} samples total):")
            for lang, count in lang_counter.most_common(3):
                print(f"  {lang:15} {count:4} ({count/total*100:5.1f}%)")
            print()
    
    def save_reports(self, output_dir='results'):
        """Save statistics reports."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save domain statistics CSV
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
        
print(f"✓ Domain statistics CSV saved: {domain_csv}")
        
        # Save TLD statistics CSV
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
        
print(f"✓ TLD statistics CSV saved: {tld_csv}")
        
        # Save domain list
        domains_txt = output_path / 'unique_domains.txt'
        with open(domains_txt, 'w', encoding='utf-8') as f:
            for domain in sorted(self.domain_counter.keys()):
                f.write(f"{domain}\n")
        
print(f"✓ Domain list saved: {domains_txt}")
        
        # Save detailed statistics in JSON format
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
        
print(f"✓ JSON statistics saved: {stats_json}")
        print()
    
    def run(self, output_dir='results'):
        """Execute full analysis pipeline."""
        self.load_data()
        self.analyze()
        self.print_basic_stats()
        self.print_tld_distribution()
        self.print_top_domains()
        self.print_domain_meta_analysis()
        self.print_language_by_tld()
        
        print("="*60)
        print("Saving Statistics Reports")
        print("="*60 + "\n")
        self.save_reports(output_dir)
        
        print("="*60)
        print("Domain statistics analysis complete!")
        print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Analyze domain distribution information in the dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl
  
  python scripts/domain_stats.py data/WebMainBench_7887_with_meta.jsonl \\
    --output-dir results/domain_analysis
        '''
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the input JSONL file'
    )
    
    parser.add_argument(
        '--output-dir',
        default='results',
        help='Output directory (default: results)'
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not Path(args.input_file).exists():
print(f"Error: File does not exist: {args.input_file}")
        return 1
    
    # Run analysis
    analyzer = DomainStatsAnalyzer(args.input_file)
    analyzer.run(args.output_dir)
    
    return 0


if __name__ == '__main__':
    exit(main())

