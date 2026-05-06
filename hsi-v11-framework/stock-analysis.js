const YahooFinance = require('yahoo-finance2').YahooFinance;
const yahooFinance = new YahooFinance();
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Stock symbols (HK market)
const STOCKS = [
    { symbol: '03690.HK', name: 'Meituan' },
    { symbol: '00916.HK', name: 'China Longyuan Power' },
    { symbol: '00020.HK', name: 'Sensetime' },
    { symbol: '02318.HK', name: 'Ping An Insurance' },
    { symbol: '00700.HK', name: 'Tencent Holdings' },
    { symbol: '00345.HK', name: 'VITASOY' },
    { symbol: '^HSI', name: 'Hang Seng Index' }
];

// Output directory
const OUTPUT_DIR = '/root/.openclaw/workspace/stock-analysis-output';
const V11_DIR = path.join(OUTPUT_DIR, 'v11');
const CSAGENT_DIR = path.join(OUTPUT_DIR, 'csagent');

// Create directories
function ensureDirs() {
    [OUTPUT_DIR, V11_DIR, CSAGENT_DIR].forEach(dir => {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
            console.log(`Created: ${dir}`);
        }
    });
}

// Fetch historical data (6 months = ~180 days)
async function fetchStockData(symbol, name) {
    try {
        console.log(`Fetching ${symbol} (${name})...`);
        
        const period1 = new Date();
        period1.setMonth(period1.getMonth() - 6);
        
        const quote = await yahooFinance.chart(symbol, {
            period1: period1.toISOString().split('T')[0],
            interval: '1d'
        });
        
        if (!quote || !quote.quotes || quote.quotes.length === 0) {
            console.warn(`No data for ${symbol}`);
            return null;
        }
        
        // Process data
        const data = quote.quotes.map(q => ({
            date: q.date ? q.date.toISOString().split('T')[0] : 'N/A',
            open: q.open || 0,
            high: q.high || 0,
            low: q.low || 0,
            close: q.close || 0,
            volume: q.volume || 0
        })).filter(d => d.date !== 'N/A');
        
        console.log(`  Retrieved ${data.length} data points for ${symbol}`);
        return { symbol, name, data };
    } catch (error) {
        console.error(`Error fetching ${symbol}: ${error.message}`);
        return null;
    }
}

// Calculate technical indicators
function calculateIndicators(data) {
    if (data.length < 20) return {};
    
    const closes = data.map(d => d.close);
    const volumes = data.map(d => d.volume);
    
    // Simple Moving Average (20-day)
    const sma20 = [];
    for (let i = 19; i < closes.length; i++) {
        const sum = closes.slice(i - 19, i + 1).reduce((a, b) => a + b, 0);
        sma20.push(sum / 20);
    }
    
    // Calculate returns
    const returns = [];
    for (let i = 1; i < closes.length; i++) {
        returns.push((closes[i] - closes[i-1]) / closes[i-1] * 100);
    }
    
    const avgReturn = returns.length > 0 ? returns.reduce((a, b) => a + b, 0) / returns.length : 0;
    const totalReturn = ((closes[closes.length - 1] - closes[0]) / closes[0]) * 100;
    
    // Volatility (standard deviation of returns)
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length;
    const volatility = Math.sqrt(variance);
    
    return {
        sma20: sma20[sma20.length - 1] || 0,
        currentPrice: closes[closes.length - 1],
        startPrice: closes[0],
        totalReturn: totalReturn.toFixed(2),
        avgDailyReturn: avgReturn.toFixed(4),
        volatility: volatility.toFixed(4),
        dataPoints: closes.length
    };
}

// Generate CSV
function generateCSV(data) {
    const header = 'date,open,high,low,close,volume\n';
    const rows = data.map(d => `${d.date},${d.open},${d.high},${d.low},${d.close},${d.volume}`).join('\n');
    return header + rows;
}

// Generate analysis report
function generateReport(results) {
    let report = '# Stock Analysis Report\n\n';
    report += `Generated: ${new Date().toISOString()}\n\n`;
    report += '## Summary\n\n';
    report += '| Symbol | Name | Current Price | 6M Return % | Volatility |\n';
    report += '|--------|------|---------------|-------------|------------|\n';
    
    results.forEach(r => {
        if (r && r.indicators) {
            report += `| ${r.symbol} | ${r.name} | ${r.indicators.currentPrice?.toFixed(2) || 'N/A'} | ${r.indicators.totalReturn || 'N/A'} | ${r.indicators.volatility || 'N/A'} |\n`;
        }
    });
    
    report += '\n## Detailed Analysis\n\n';
    results.forEach(r => {
        if (r && r.indicators) {
            report += `### ${r.name} (${r.symbol})\n\n`;
            report += `- Current Price: ${r.indicators.currentPrice?.toFixed(2)}\n`;
            report += `- Start Price (6M ago): ${r.indicators.startPrice?.toFixed(2)}\n`;
            report += `- Total Return: ${r.indicators.totalReturn}%\n`;
            report += `- Average Daily Return: ${r.indicators.avgDailyReturn}%\n`;
            report += `- Volatility: ${r.indicators.volatility}\n`;
            report += `- Data Points: ${r.indicators.dataPoints}\n`;
            report += `- SMA (20-day): ${r.indicators.sma20?.toFixed(2)}\n\n`;
        }
    });
    
    return report;
}

// Main execution
async function main() {
    console.log('=== Stock Analysis Started ===\n');
    
    ensureDirs();
    
    const results = [];
    
    for (const stock of STOCKS) {
        const stockData = await fetchStockData(stock.symbol, stock.name);
        if (stockData) {
            const indicators = calculateIndicators(stockData.data);
            results.push({ ...stockData, indicators });
            
            // Save CSV
            const csv = generateCSV(stockData.data);
            const csvPath = path.join(V11_DIR, `${stock.symbol.replace('.HK', '').replace('^', '')}_data.csv`);
            fs.writeFileSync(csvPath, csv);
            console.log(`  Saved CSV: ${csvPath}`);
        }
    }
    
    // Generate and save report
    const report = generateReport(results);
    const reportPath = path.join(V11_DIR, 'analysis_report.md');
    fs.writeFileSync(reportPath, report);
    console.log(`\nSaved Report: ${reportPath}`);
    
    // Copy to csagent folder (same content for now)
    fs.cpSync(V11_DIR, CSAGENT_DIR, { recursive: true });
    console.log(`Copied results to csagent folder`);
    
    // Save summary JSON
    const summaryPath = path.join(OUTPUT_DIR, 'summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify(results, null, 2));
    console.log(`Saved Summary: ${summaryPath}`);
    
    console.log('\n=== Analysis Complete ===');
    console.log(`Output directory: ${OUTPUT_DIR}`);
}

main().catch(console.error);
