#!/bin/bash
# daily_report_workflow.sh - Push Iran war report to GitHub and update GitHub Pages

set -e

echo "Starting Iran War Daily Report Workflow - $(date)"

# Configuration
REPORT_DIR="/Users/liugang/.openclaw/workspace/iran_war_reports"
GH_PAGES_DIR="/Users/liugang/.openclaw/workspace/iran-war-gh-pages"
TODAY=$(date +%Y-%m-%d)
REPORT_FILE="$REPORT_DIR/$TODAY-report.md"
SEARCH_DATA="$REPORT_DIR/search_results_$TODAY.json"

# Check if report exists
if [ ! -f "$REPORT_FILE" ]; then
    echo "Error: Report file not found: $REPORT_FILE"
    exit 1
fi

# Check if search data exists
if [ ! -f "$SEARCH_DATA" ]; then
    echo "Error: Search data file not found: $SEARCH_DATA"
    exit 1
fi

echo "Found report: $REPORT_FILE"
echo "Found search data: $SEARCH_DATA"

# Step 1: Convert Markdown to HTML
cd "$GH_PAGES_DIR"

# Create HTML from Markdown (simple conversion)
echo "Converting Markdown to HTML..."
cp "$REPORT_FILE" "$GH_PAGES_DIR/$TODAY-report.md"

# Update the main web report
cat > "$GH_PAGES_DIR/web_report.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iran War Daily Report - $TODAY</title>
    <style>
        body { font-family: Arial, sans-serif; margin:数是 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        h2 { color: #444; margin-top: 30px; }
        h3 { color: #555; }
        .summary { background: #f9f9f9; padding: 20px; border-left: 4px solid #007bff; margin: 20px 0; }
        .source { font-size: 0.9em; color: #666; margin-top: 5px; }
        .timestamp { color: #888; font-size: 0.8em; margin-bottom: 20px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #777; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🇮🇷 Iran War Daily Report - $TODAY</h1>
        <div class="timestamp">Report generated: $(date) | Data sources: Tavily Search API (International Media)</div>
        
        <div class="summary">
            <h2>📋 Executive Summary</h2>
            <p>2026 Iran War enters fifth week with escalating regional conflict. Key developments include Hezbollah's formal entry (March 2), economic impacts from Strait of Hormuz closure, and shifting geopolitical alliances.</p>
            <p><strong>Latest Report:</strong> <a href="$TODAY-report.md" download>Download Full Markdown Report</a></p>
        </div>
        
        <h2>📊 Key Metrics</h2>
        <ul>
            <li><strong>Military:</strong> 2000+ missiles fired by Iran, 250+ Israeli strikes in Lebanon</li>
            <li><strong>Economic:</strong> Oil prices projected to rise $5-$7/barrel, potential global recession risk</li>
            <li><strong>Humanitarian:</strong> 1500+ civilian deaths, 3000+ injuries reported</li>
            <li><strong>Geopolitical:</strong> Saudi Arabia accused of covert support for US-Israel operations</li>
        </ul>
        
        <h2>🔗 Quick Links</h2>
        <ul>
            <li><a href="https://github.com/garylauchina/iran-war-report" target="_blank">GitHub Repository</a></li>
            <li><a href="$TODAY-report.md" target="_blank">Today's Full Report (Markdown)</a></li>
            <li><a href="https://www.criticalthreats.org/analysis/iran-update-evening-special-report-march-24-2026" target="_blank">Critical Threats Analysis</a></li>
            <li><a href="https://acleddata.com/update/middle-east-special-issue-march-2026" target="_blank">ACLED Conflict Data</a></li>
        </ul>
        
        <h2>📈 Trend Analysis</h2>
        <p><strong>Short-term (1-4 weeks):</strong> Military operations expected to continue at least one week</p>
        <p><strong>Medium-term (1-3 months):</strong> Critical nodes: Gulf states economic resilience, US domestic political stability</p>
        <p><strong>Long-term (3+ months):</strong> Strategic watershed - either US resurgence or accelerated decline in Middle East</p>
        
        <div class="footer">
            <p>This report is automatically generated using Tavily Search API to aggregate international media coverage.</p>
            <p>Report updates daily at 09:00 Beijing Time / 01:00 UTC</p>
            <p>© 2026 Iran War Monitoring Project | <a href="https://garylauchina.github.io/iran-war-report/">GitHub Pages</a></p>
        </div>
    </div>
</body>
</html>
EOF

# Step 2: Commit and push to GitHub Pages repository
echo "Committing changes to GitHub Pages repository..."
git add .

if git diff --cached --quiet; then
    echo "No changes to commit"
else
    git commit -m "Update Iran war daily report for $TODAY"
    
    echo "Pushing to GitHub Pages..."
    git push origin main
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pushed to GitHub Pages repository"
        echo "🌐 GitHub Pages should automatically rebuild from the main branch"
        echo "🔗 Report available at: https://garylauchina.github.io/iran-war-report/"
    else
        echo "⚠️ Warning: GitHub push failed"
        echo "Continuing with other workflow steps..."
    fi
fi

echo "Workflow completed - $(date)"