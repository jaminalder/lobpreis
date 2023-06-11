var md = window.markdownit();
var result = md.render('# markdown-it rulezz!');
console.log("rendered md: " + result);
document.body.innerHTML = result;
