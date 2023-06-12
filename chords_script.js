#!/usr/bin/env node
'use strict'

const fs = require('fs');
const md = require('markdown-it')()
  .use(require('markdown-it-chords'));

const input_md = fs.readFileSync('./chords/md/unser_gott.md', { encoding: 'utf8' });
console.log(input_md);
const generated_song = md.render(input_md);
console.log(generated_song);

let output = `<html>
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>markdown-it-chords: Write your lyric sheets in markdown</title>
</head>
<style>
:root {
	--chord-diagram-font-size: 10px;
}
.chord {
	display: inline-block;
	position: relative;
	user-select: none;
	height: 3.2em;
	font-size: 70%;
}
.chord.diagram {
	height: calc(1.5em + (3.5 * var(--chord-diagram-font-size)))
}
.chord .inner {
	position: absolute;
	display: block;
	left: 0;
	bottom: 1.3em;
}
.chord i {
	font-style: normal;
	display: inline-block;
}
.chord i.diagram {
	font: 100 var(--chord-diagram-font-size) Courier;
	line-height: .5em;
	position: absolute;
	bottom: 0;
	display: none;
}
.chord .inner:hover i.diagram,
.chord.diagram i.diagram,
.chord i.diagram.show {
	display: inline-block;
}
.chord:not(.diagram) .inner:hover i.diagram {
	background: white;
	z-index: 5;
}
</style>

<body>

${generated_song}

</body>
</html>
`

fs.writeFileSync('./chords/html/unser_gott.html', output);
