#!/usr/bin/env node

/**
 * Web App Inspector - Captures console logs and screenshots
 * Usage: node inspect_webapp.js <url> [action]
 */

const http = require('http');
const fs = require('fs');

const url = process.argv[2] || 'http://localhost:3001';
const action = process.argv[3];

console.log('🔍 Inspecting:', url);
console.log('');

// Simple HTTP check
http.get(url, (res) => {
  console.log('✅ Server responding:', res.statusCode);
  console.log('');

  let data = '';
  res.on('data', chunk => data += chunk);
  res.on('end', () => {
    // Check for JavaScript errors in the HTML
    const hasScript = data.includes('<script>');
    const hasApi = data.includes('async function api');
    const hasLoadWorkflows = data.includes('loadWorkflows()');

    console.log('📄 HTML Analysis:');
    console.log('  - Has <script> tag:', hasScript);
    console.log('  - Has api() function:', hasApi);
    console.log('  - Calls loadWorkflows():', hasLoadWorkflows);
    console.log('  - HTML size:', Math.round(data.length / 1024), 'KB');
    console.log('');

    // Check for syntax errors
    const scriptMatch = data.match(/<script>([\s\S]*?)<\/script>/);
    if (scriptMatch) {
      const script = scriptMatch[1];
      fs.writeFileSync('/tmp/dashboard_script.js', script);
      console.log('📝 JavaScript extracted to /tmp/dashboard_script.js');
      console.log('');

      // Try to find obvious syntax errors
      const suspiciousPatterns = [
        { pattern: /`[^`]*`[^`]*`/g, name: 'Nested template literals' },
        { pattern: /\${[^}]*\${/g, name: 'Nested interpolation' },
        { pattern: /(['"])[^\1]*\1[^\1]*\1/g, name: 'Quote nesting issues' }
      ];

      console.log('🔍 Checking for common issues:');
      suspiciousPatterns.forEach(({pattern, name}) => {
        const matches = script.match(pattern);
        if (matches && matches.length > 0) {
          console.log(`  ⚠️  ${name}: ${matches.length} occurrences`);
        }
      });
    }

    console.log('');
    console.log('💡 To capture browser console logs, install puppeteer:');
    console.log('   npm install puppeteer');
    console.log('   Then run: node inspect_webapp_browser.js');
  });
}).on('error', (err) => {
  console.error('❌ Error:', err.message);
});
