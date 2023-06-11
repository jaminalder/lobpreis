#!/usr/bin/env node
'use strict'

const fs = require('fs');
const md = require('markdown-it')()
  .use(require('markdown-it-chords'));

const input_md = fs.readFileSync('./chords/md/unser_gott.md', 'utf8');
console.log(input_md);
const generated_song = md.render(input_md);
console.log(generated_song);

let styles = fs.readFileSync('./node_modules/markdown-it-chords/markdown-it-chords.css', { encoding: 'utf8' })

let output = `<html>
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>markdown-it-chords: Write your lyric sheets in markdown</title>
</head>
<style>
${styles}
</style>

<body>

${md.render(generated_song)}

</body>
</html>
`

fs.writeFileSync('./chords/html/unser_gott.html', output);
