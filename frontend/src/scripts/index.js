import "../styles/index.scss";

// Import all of Bootstrap's JS
import * as bootstrap from 'bootstrap';

import "bootstrap-show-password/dist/bootstrap-show-password.js";
import "htmx.org";
import "masonry-layout";
import "imagesloaded";
import Typewriter from 'typewriter-effect/dist/core';


// Bootstrap - initialize tooltips
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

function importAll(r) {
    return r.keys().map(r);
}

const images = importAll(require.context('../img', false, /\.(png|jpe?g|svg)$/));

new Typewriter('#typewriter', {
    strings: ['Apprenez', 'Fabriquez', 'Partagez'],
    autoStart: true,
    loop: true,
});

// init Masonry
var $grid = $('.grid').masonry({
    itemSelector: '.grid-item',
    percentPosition: true
});

// layout Masonry after each image loads
$grid.imagesLoaded().progress( function() {
    $grid.masonry('layout');
  });