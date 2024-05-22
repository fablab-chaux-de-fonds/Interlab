import Typewriter from 'typewriter-effect/dist/core';

document.addEventListener('DOMContentLoaded', function() {
  const typewriterStrings = JSON.parse(document.getElementById('typewriter-data').textContent);
  new Typewriter('#typewriter', {
      strings: typewriterStrings,
      autoStart: true,
      loop: true,
  });
});