#!/bin/bash

###############################################################################
# WebMainBench 数据集完整处理脚本
# 
# 功能：为数据集添加完整的 meta 字段
# - meta.level, meta.table, meta.code, meta.equation (通过 statics.py)
# - meta.language (通过 language_classify.py)
# - meta.style (通过 style_classify.py)
#
# 使用方法：
#   ./scripts/process_dataset.sh <input_file> <output_file> <api_key> [base_url]
#
# 示例：
#   ./scripts/process_dataset.sh \
#     data/sample_dataset_with_fields.jsonl \
#     data/final_dataset.jsonl \
#     sk-xxxxx \
#     https://api.deepseek.com/v1
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# 检查参数
if [ $# -lt 3 ]; then
    print_error "参数不足！"
    echo ""
    echo "使用方法："
    echo "  $0 <input_file> <output_file> <api_key> [base_url] [batch_size]"
    echo ""
    echo "参数说明："
    echo "  input_file   - 输入 JSONL 文件路径"
    echo "  output_file  - 最终输出文件路径"
    echo "  api_key      - OpenAI API 密钥"
    echo "  base_url     - API 基础 URL (可选，默认: https://api.deepseek.com/v1)"
    echo "  batch_size   - 批处理大小 (可选，默认: 50)"
    echo ""
    echo "示例："
    echo "  $0 data/input.jsonl data/output.jsonl sk-xxxxx"
    echo "  $0 data/input.jsonl data/output.jsonl sk-xxxxx https://api.openai.com/v1 100"
    exit 1
fi

# 获取参数
INPUT_FILE="$1"
FINAL_OUTPUT="$2"
API_KEY="$3"
BASE_URL="${4:-https://api.deepseek.com/v1}"
BATCH_SIZE="${5:-50}"

# 生成中间文件名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEMP_DIR="data/temp_${TIMESTAMP}"
STEP1_OUTPUT="${TEMP_DIR}/step1_with_stats.jsonl"
STEP2_OUTPUT="${TEMP_DIR}/step2_with_language.jsonl"

# 验证输入文件
if [ ! -f "$INPUT_FILE" ]; then
    print_error "输入文件不存在: $INPUT_FILE"
    exit 1
fi

# 创建临时目录
mkdir -p "$TEMP_DIR"

# 打印配置信息
print_step "🚀 开始处理数据集"
print_info "输入文件: $INPUT_FILE"
print_info "输出文件: $FINAL_OUTPUT"
print_info "API 地址: $BASE_URL"
print_info "批处理大小: $BATCH_SIZE"
print_info "临时目录: $TEMP_DIR"
echo ""

# 统计输入文件行数
INPUT_LINES=$(wc -l < "$INPUT_FILE" | tr -d ' ')
print_info "输入数据总数: $INPUT_LINES 条"
echo ""

# ============================================================================
# 步骤 1: 添加统计字段
# ============================================================================
print_step "📊 步骤 1/3: 计算统计字段 (level, table, code, equation)"

if python scripts/statics.py --input "$INPUT_FILE" --output "$STEP1_OUTPUT"; then
    STEP1_LINES=$(wc -l < "$STEP1_OUTPUT" | tr -d ' ')
    print_success "步骤 1 完成！处理了 $STEP1_LINES 条数据"
    
    # 验证数据完整性
    if [ "$INPUT_LINES" -ne "$STEP1_LINES" ]; then
        print_warning "数据行数不一致！输入: $INPUT_LINES, 输出: $STEP1_LINES"
    fi
else
    print_error "步骤 1 失败！"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# ============================================================================
# 步骤 2: 添加语言字段
# ============================================================================
print_step "🌐 步骤 2/3: 检测语言 (language)"

export OPENAI_API_KEY="$API_KEY"

if python scripts/language_classify.py \
    "$STEP1_OUTPUT" \
    --output "$STEP2_OUTPUT" \
    --api-key "$API_KEY" \
    --base-url "$BASE_URL" \
    --batch-size "$BATCH_SIZE"; then
    
    STEP2_LINES=$(wc -l < "$STEP2_OUTPUT" | tr -d ' ')
    print_success "步骤 2 完成！处理了 $STEP2_LINES 条数据"
    
    # 验证数据完整性
    if [ "$STEP1_LINES" -ne "$STEP2_LINES" ]; then
        print_warning "数据行数不一致！输入: $STEP1_LINES, 输出: $STEP2_LINES"
    fi
else
    print_error "步骤 2 失败！"
    print_warning "保留中间文件: $STEP1_OUTPUT"
    exit 1
fi

# ============================================================================
# 步骤 3: 添加网页类型字段
# ============================================================================
print_step "🎨 步骤 3/3: 分类网页类型 (style)"

if python scripts/style_classify.py \
    "$STEP2_OUTPUT" \
    --output "$FINAL_OUTPUT" \
    --api-key "$API_KEY" \
    --base-url "$BASE_URL" \
    --batch-size "$BATCH_SIZE"; then
    
    FINAL_LINES=$(wc -l < "$FINAL_OUTPUT" | tr -d ' ')
    print_success "步骤 3 完成！处理了 $FINAL_LINES 条数据"
    
    # 验证数据完整性
    if [ "$STEP2_LINES" -ne "$FINAL_LINES" ]; then
        print_warning "数据行数不一致！输入: $STEP2_LINES, 输出: $FINAL_LINES"
    fi
else
    print_error "步骤 3 失败！"
    print_warning "保留中间文件: $STEP2_OUTPUT"
    exit 1
fi

# ============================================================================
# 完成与清理
# ============================================================================
print_step "🎉 处理完成！"

print_info "最终输出: $FINAL_OUTPUT"
print_info "处理数据: $FINAL_LINES 条"
echo ""

# 询问是否删除临时文件
read -p "是否删除临时文件？(y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$TEMP_DIR"
    print_success "已删除临时文件"
else
    print_info "临时文件保留在: $TEMP_DIR"
fi

# 显示输出文件示例
print_step "📋 输出数据示例"
print_info "查看第一条数据的 meta 字段："
echo ""
head -n 1 "$FINAL_OUTPUT" | python -c "
import json
import sys

data = json.loads(sys.stdin.read())
meta = data.get('meta', {})

print('Meta 字段内容:')
print(json.dumps(meta, indent=2, ensure_ascii=False))
"

print_success "全部完成！🎊"

