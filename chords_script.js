#!/usr/bin/env node
'use strict'

const fs = require('fs');
const md = require('markdown-it')()
  .use(require('markdown-it-chords'));

const input_md = fs.readFileSync('./chords/md/unser_gott.md', { encoding: 'utf8' });
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
.chord {
	font-family: Didot, "Helvetica Neue", serif;
}
body {
	padding: 50px;
	font-size: 14pt;
	max-width: 1900px;
	margin: 0 auto;
}
#sandbox div,
#sandbox textarea {
	width: 50%;
	resize: none;
	overflow: scroll;
	float: left;
	box-sizing: border-box;
	padding: 10px;
}
code {
	background: #eee;
	font-size: 75%;
}
pre {
	background: #eee;
	padding: 10px 10px 0;
	max-width: 100%;
	overflow: scroll;
	display: inline-block;
}
.clearfix:after, pre:after {
	content: "";
	display: table;
	clear: both;
}
#controls {
	background: lightgray;
	padding: 10px;
}
#controls select,
#controls input {
	vertical-align: middle;
}
</style>

<body>

${generated_song}

</body>
</html>
`

fs.writeFileSync('./chords/html/unser_gott.html', output);
