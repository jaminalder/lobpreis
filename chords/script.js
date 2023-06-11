const fs = require('fs');
const md = require('markdown-it')()
  .use(require('markdown-it-chords'));

try {
  const data = fs.readFileSync('./md/unser_gott.md', 'utf8');
  console.log(data);
  const result = md.render(data);
  console.log(result);
  fs.writeFileSync('./unser_gott.html', result);
} catch (err) {
  console.error(err);
}


