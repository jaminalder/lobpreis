var md = require('markdown-it')();
var result = md.render('# markdown-it rulezz!');
document.body.innerHTML = result;
