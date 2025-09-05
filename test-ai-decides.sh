#!/bin/bash

# Test script for enhanced telemetry agent with AI-decides strategy

echo "🚀 Testing Enhanced Telemetry Agent with AI-Decides Strategy"
echo "============================================================"

# Navigate to the telemetry-scanner directory
cd /Users/shuaib.tabit/Documents/TRA/telemetry-scanner

# Test with the customer-span ticket using different strategies
echo ""
echo "📋 Testing with customer-span-attributes.txt ticket"
echo ""

# Test 1: Auto strategy (AI decides)
echo "🤖 Test 1: Auto strategy (AI decides)"
python enhanced_cli.py \
    --ticket-key customer-span-attributes.txt \
    --local-ticket \
    --dirs-proj-path ~/Documents/TRA/iam-tasks/test_dirs.proj \
    --output runs/test-ai-decides-auto \
    --strategy auto \
    --batch-size 50 \
    --max-candidates 100

echo ""
echo "📊 Results for Auto Strategy:"
echo "Files processed: $(ls runs/test-ai-decides-auto/ 2>/dev/null | wc -l)"
if [ -f "runs/test-ai-decides-auto/solution.diff" ]; then
    echo "Diff generated: ✅"
    echo "Diff size: $(wc -l < runs/test-ai-decides-auto/solution.diff) lines"
else
    echo "Diff generated: ❌"
fi

echo ""
echo "Test 2: Direct strategy (Force direct modification)"
python enhanced_cli.py \
    --ticket-key customer-span-attributes.txt \
    --local-ticket \
    --dirs-proj-path ~/Documents/TRA/iam-tasks/test_dirs.proj \
    --output runs/test-ai-decides-direct \
    --strategy direct \
    --batch-size 50 \
    --max-candidates 100

echo ""
echo "📊 Results for Direct Strategy:"
echo "Files processed: $(ls runs/test-ai-decides-direct/ 2>/dev/null | wc -l)"
if [ -f "runs/test-ai-decides-direct/solution.diff" ]; then
    echo "Diff generated: ✅"
    echo "Diff size: $(wc -l < runs/test-ai-decides-direct/solution.diff) lines"
else
    echo "Diff generated: ❌"
fi

echo ""
echo "📈 Comparison Summary:"
echo "====================="
echo "Auto strategy files: $(ls runs/test-ai-decides-auto/ 2>/dev/null | wc -l)"
echo "Direct strategy files: $(ls runs/test-ai-decides-direct/ 2>/dev/null | wc -l)"

if [ -f "runs/test-ai-decides-auto/solution.diff" ] && [ -f "runs/test-ai-decides-direct/solution.diff" ]; then
    auto_lines=$(wc -l < runs/test-ai-decides-auto/solution.diff)
    direct_lines=$(wc -l < runs/test-ai-decides-direct/solution.diff)
    echo "Auto strategy diff: $auto_lines lines"
    echo "Direct strategy diff: $direct_lines lines"
    
    if [ $direct_lines -gt $auto_lines ]; then
        echo "✅ Direct strategy generated more comprehensive changes"
    elif [ $auto_lines -gt $direct_lines ]; then
        echo "🤔 Auto strategy generated more changes (AI chose different approach)"
    else
        echo "📊 Both strategies generated similar amount of changes"
    fi
fi

echo ""
echo "🔍 To examine results:"
echo "cat runs/test-ai-decides-auto/enhanced_intent.json"
echo "cat runs/test-ai-decides-direct/enhanced_intent.json"
echo "diff runs/test-ai-decides-auto/solution.diff runs/test-ai-decides-direct/solution.diff"
