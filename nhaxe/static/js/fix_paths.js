const fs = require('fs');
const path = require('path');

const homeDir = 'd:/Front End Lập Trình WEB/Home';

const files = fs.readdirSync(homeDir).filter(f => f.endsWith('.html'));
let count = 0;

files.forEach(file => {
    const filePath = path.join(homeDir, file);
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Fix paths
    let newContent = content.replace(/\.\.\/CSS\/CSS\//g, '../CSS/');
    newContent = newContent.replace(/\.\.\/\.\.\/CSS\//g, '../CSS/');
    newContent = newContent.replace(/\.\.\/\.\.\/picture\//g, '../picture/');
    
    if (content !== newContent) {
        fs.writeFileSync(filePath, newContent, 'utf8');
        console.log('Fixed paths in:', file);
        count++;
    }
});

console.log(`\nFixed ${count} HTML files.`);

// Move CSS files
const oldCssDir = 'd:/Front End Lập Trình WEB/CSS/CSS';
const newCssDir = 'd:/Front End Lập Trình WEB/CSS';

if (fs.existsSync(oldCssDir)) {
    const cssFiles = fs.readdirSync(oldCssDir);
    cssFiles.forEach(cssFile => {
        fs.renameSync(path.join(oldCssDir, cssFile), path.join(newCssDir, cssFile));
    });
    fs.rmdirSync(oldCssDir);
    console.log('\nMoved CSS files from CSS/CSS to CSS/ and deleted empty folder.');
}
